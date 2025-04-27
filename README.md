# RAG Document Assistant

A Retrieval-Augmented Generation (RAG) system for document analysis and question answering.

## Features

- Upload and process various document formats (PDF, DOCX, TXT, etc.)
- Generate document summaries automatically
- Ask questions about your documents using natural language
- Retrieve relevant document snippets with relevance scores
- Clean, intuitive UI with document management

## Components

1. **Frontend**: Streamlit web interface
2. **Backend**: FastAPI server
3. **Document Processing**: LlamaIndex for document indexing
4. **Vector Storage**: ChromaDB for efficient document retrieval
5. **Answering Engine**: OpenAI models for question answering

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API Key

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
CHROMA_PATH=./chroma_db
EMBED_MODEL=local:BAAI/bge-small-en-v1.5  # or another embedding model
LLM_MODEL=gpt-3.5-turbo  # or gpt-4
```

### Running the Application

1. Start the backend server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

2. Start the frontend interface:

```bash
streamlit run frontend.py
```

3. Access the application at http://localhost:8501

## Usage

1. Upload documents through the sidebar
2. Wait for document processing to complete
3. Ask questions about your documents
4. View answers with relevant source snippets

## Development Notes

- The system uses LlamaIndex for document processing, which provides superior handling of large documents
- ChromaDB is used for vector storage, allowing efficient retrieval of document chunks
- Document summaries are generated using OpenAI's models
- The system handles various document formats including PDF, DOCX, TXT, and more