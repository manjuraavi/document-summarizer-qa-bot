# 📙 RAG Document Assistant

A **Retrieval-Augmented Generation (RAG)** system for document analysis, summarization, and question answering.

This project allows you to upload documents, generate their summaries, ask natural language questions, and retrieve highly relevant document snippets using LLMs and vector databases.

---

## 🚀 Features

- 📂 Upload and process multiple document formats:
  - PDF
  - DOCX
  - TXT
  - Markdown (.md)

- 📖 Automatic document summarization using OpenAI's LLMs

- 🔍 Natural language question answering over your documents

- 🔁 Fast retrieval of relevant chunks with similarity scores

- 🌐 Clean, responsive Streamlit web app

- 🛠️ Document management: upload, select, delete, and refresh documents easily

---

## 📊 Components

| Component            | Tech Stack                                         |
|----------------------|----------------------------------------------------|
| Frontend             | Streamlit                                          |
| Backend              | FastAPI                                            |
| Document Processing  | LlamaIndex (Index building, node splitting, etc.)  |
| Vector Storage       | ChromaDB (Local Vector Database)                   |
| LLM Engine           | OpenAI GPT-3.5 Turbo / GPT-4                        |
| Embedding Model      | BAAI bge-small-en-v1.5 (local) or OpenAI embeddings |

---

## 🔧 Setup Instructions

### 🔁 Prerequisites

- Python 3.9+
- OpenAI API key


### 📚 Installation

#### Option 1: Local Setup (No Docker)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/manjuraavi/document-summarizer-qa-bot.git
   cd document-summarizer-qa-bot
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**:

   Create a `.env` file at the root with:

   ```env
   OPENAI_API_KEY=your-openai-api-key
   CHROMA_PATH=./chroma_db
   EMBED_MODEL=local:BAAI/bge-small-en-v1.5  # or your preferred embedding model
   LLM_MODEL=gpt-3.5-turbo  # or gpt-4
   ```

#### Option 2: Docker Setup (Recommended for easy deployment)

1. **Build the Docker image**:

  ```
  docker build -t document_summarizer_qa_bot .
  ```

2. **Run the Docker container**:

  ```
  docker run -d -p 8001:8001 -p 8501:8501 --env-file .env document_summarizer_qa_bot
  ```
  This will expose the FastAPI backend on port 8001 and the Streamlit frontend on port 8501.

3. **Access the app: Open http://localhost:8501 in your browser**.

### 💡 Quick Start

1. **Start the backend server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```

2. **Start the frontend Streamlit app**:
   ```bash
   streamlit run frontend.py
   ```

3. **Access the app**:
   Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔢 Usage Instructions

- Upload documents through the Streamlit sidebar.
- Wait for processing (tokenization, embedding, indexing).
- View document summaries instantly.
- Ask natural language questions about your documents.
- View concise answers and matched document sources.
- Manage documents (delete, refresh, upload new ones).

---

## 🐞 Development Notes

- **LlamaIndex** efficiently splits large documents into retrievable nodes.
- **ChromaDB** acts as a fast vector search engine.
- **Local Embeddings** are used (BAAI bge-small-en-v1.5) for cost-saving.
- **OpenAI GPT models** answer user queries using the retrieved relevant chunks.

- Supported formats:
  - PDF (.pdf)
  - Word Documents (.docx)
  - Plain Text Files (.txt)
  - Markdown (.md)


---

## 📊 Example Architecture

```plaintext
[Frontend: Streamlit]
        ↳ Upload documents
        ↳ Ask questions

[Backend: FastAPI]
        ↳ Handle documents
        ↳ Query processing

[Document Index]
        ↳ LlamaIndex creates split nodes

[Vector DB]
        ↳ ChromaDB stores embeddings

[Answer Engine]
        ↳ OpenAI LLM summarizes and answers
```

---

## 👤 Contributors

- [@manjuraavi](https://github.com/manjuraavi)

---

## 📜 License

MIT License

Copyright (c) 2025 Manjusha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

# 🔥 Ready to supercharge your documents with AI? Let's go! 🚀

