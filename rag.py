import os
import logging
from typing import Dict, Any, List
from pathlib import Path
import asyncio

# LlamaIndex imports
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.schema import NodeWithScore
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings, ServiceContext
from llama_index.core.schema import QueryBundle
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.prompts import ChatMessage, MessageRole, ChatPromptTemplate
from llama_index.llms.openai import OpenAI

# ChromaDB import
import chromadb

# OpenAI API for summarization
from openai import AsyncOpenAI

# Environment variables
from dotenv import load_dotenv

load_dotenv()

# Configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PATH", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "local:BAAI/bge-small-en-v1.5")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("document_qa.log")
    ]
)
logger = logging.getLogger("rag")

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Configure LlamaIndex
def configure_llama_index():
    """Configure LlamaIndex with the required settings"""
    try:
        Settings.llm = OpenAI(model=LLM_MODEL, temperature=0.1)
        Settings.embed_model = EMBED_MODEL
        logger.info("LlamaIndex configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure LlamaIndex: {str(e)}")
        return False

# Configure LlamaIndex at module load time
configure_llama_index()

async def generate_summary(text: str) -> str:
    """Generate a document summary using OpenAI"""
    try:
        response = await openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert summarizer. Create a concise summary that captures the key information in the document. Focus on the main topics, key findings, and important details."},
                {"role": "user", "content": f"Please summarize the following document in 4-5 sentences:\n\n{text[:4000]}"}
            ],
            temperature=0.3,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        return "Summary generation failed. The document has been processed successfully but no summary is available."

def get_or_create_collection(task_id: str):
    """Get or create a ChromaDB collection for the document"""
    try:
        collection_name = f"doc_{task_id}"
        return chroma_client.get_or_create_collection(name=collection_name)
    except Exception as e:
        logger.error(f"Failed to create ChromaDB collection: {str(e)}")
        raise

async def process_document(file_path: str, task_id: str) -> Dict[str, Any]:
    """Process a document using LlamaIndex"""
    try:
        # Get the document collection
        chroma_collection = get_or_create_collection(task_id)
        
        # Create a ChromaVectorStore with the collection
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        # Create a storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Load documents using LlamaIndex
        documents = SimpleDirectoryReader(
            input_files=[file_path]
        ).load_data()
        
        if not documents:
            return {"status": "failed", "error": "No content could be extracted from the document"}
        
        window_size = 5  # Adjusted to capture larger chunks

        # Parse the documents into nodes using sentence window
        node_parser = SentenceWindowNodeParser.from_defaults(
            window_size=window_size,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )
        
        # Create nodes from documents
        nodes = node_parser.get_nodes_from_documents(documents)
        
        # Create the index with the nodes
        index = VectorStoreIndex(
            nodes, 
            storage_context=storage_context,
        )
        
        # Generate a summary
        doc_content = " ".join([doc.text for doc in documents])
        summary = await generate_summary(doc_content)
        
        return {
            "status": "completed",
            "summary": summary,
            "file": os.path.basename(file_path),
            "index_id": task_id
        }
    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
        return {"status": "failed", "error": str(e)}

async def query_document(question: str, top_k: int = 4) -> Dict[str, Any]:
    """Query all document collections and return the most relevant answer"""
    try:
        # Get all collections
        logger.info("Listing all collections in ChromaDB")
        collections = chroma_client.list_collections()
        
        if not collections:
            return {"answer": "No documents have been uploaded yet.", "sources": []}
        
        best_results = []
        
        # Query each collection
        for collection_info in collections:
            collection_name = collection_info.name
            
            # Skip collections that don't start with "doc_"
            if not collection_name.startswith("doc_"):
                continue
                
            chroma_collection = chroma_client.get_collection(collection_name)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            
            # Create index from the existing vector store
            index = VectorStoreIndex.from_vector_store(vector_store)
            logger.info(f"Loaded index for collection: {collection_name}")
            
            # Create a retriever
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k,
            )
            logger.info(f"Created retriever for collection: {collection_name}")

            # Log the question being processed
            logger.info(f"Retrieving nodes for question: {question}")

            # Retrieve nodes
            nodes = retriever.retrieve(question)
            logger.info(f"Retrieved {len(nodes)} nodes for question: {question}")

            # If no nodes are retrieved, log and skip to the next collection
            if not nodes:
                logger.info(f"No nodes retrieved for collection: {collection_name}. Skipping to next collection.")
                continue

            # Log before creating the QA template
            logger.info("Creating QA template...")
            try:
                # Create a simpler prompt template since we're having issues with ChatPromptTemplate
                from llama_index.core.prompts import PromptTemplate
                
                qa_template = PromptTemplate(
                    "You are a helpful assistant that provides accurate information based on the context.\n"
                    "Context information is below.\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"
                    "Given the context information and not prior knowledge, "
                    "answer the question: {query_str}"
                )
                
                logger.info(f"QA Template created for collection: {collection_name}")
                logger.info(f"Response Mode: {ResponseMode.COMPACT}, QA Template: {qa_template}")
            except Exception as e:
                logger.error(f"Error creating QA Template: {str(e)}")
                raise

            # Create response synthesizer
            response_synthesizer = get_response_synthesizer(
                response_mode=ResponseMode.COMPACT,
                text_qa_template=qa_template
            )
            logger.info(f"Response synthesizer created for collection: {collection_name}")

            # Create query bundle from the question
            from llama_index.core.schema import QueryBundle
            query_bundle = QueryBundle(question)
            
            # Generate response - use the NodeWithScore objects directly
            # Don't try to convert them to Document objects
            response = response_synthesizer.synthesize(query_bundle, nodes)
            
            # Calculate the relevance score (average similarity score)
            avg_similarity = sum(node.score for node in nodes if hasattr(node, 'score')) / len(nodes)
            
            # Extract source information from nodes
            sources = []
            for i, node in enumerate(nodes):
                metadata = node.metadata if hasattr(node, 'metadata') else {}
                file_path = metadata.get("file_path", "Unknown")
                
                sources.append({
                    "source": file_path,
                    "text": node.text if hasattr(node, 'text') else str(node),
                    "score": node.score if hasattr(node, 'score') else 0.5
                })
            
            best_results.append({
                "answer": response.response,
                "sources": sources,
                "avg_score": avg_similarity,
                "collection": collection_name
            })
        
        if not best_results:
            return {"answer": "No relevant information found in the uploaded documents.", "sources": []}
            
        # Sort results by average similarity score (descending)
        best_results.sort(key=lambda x: x["avg_score"], reverse=True)
        
        # Return the best result
        return {
            "answer": best_results[0]["answer"],
            "sources": best_results[0]["sources"]
        }
        
    except Exception as e:
        logger.error(f"Failed to query documents: {str(e)}")
        return {"answer": f"Error during document retrieval: {str(e)}", "sources": []}
