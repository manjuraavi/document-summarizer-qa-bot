import streamlit as st
import requests
import time
import os
from pathlib import Path

# Set page layout
st.set_page_config(
    page_title="📚 RAG Document Assistant",
    layout="wide"
)

# --- Custom Styles ---
st.markdown("""
<style>
    .stTextInput input, .stTextArea textarea {
        padding: 12px !important;
        border-radius: 8px !important;
    }
    .stButton button {
        padding: 10px;
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
    }
    .uploaded-file {
        padding: 10px;
        background: #f0f2f6;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .source-text {
        background-color: #f7f7f7;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #4CAF50;
        margin-bottom: 10px;
        font-size: 0.9em;
    }
    .stProgress .st-bo {
        background-color: #4CAF50;
    }
    .relevance-high {
        color: #4CAF50;
        font-weight: bold;
    }
    .relevance-medium {
        color: #FFC107;
        font-weight: bold;
    }
    .relevance-low {
        color: #F44336;
        font-weight: bold;
    }
    .summary-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #4CAF50;
    }
    .stat-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    .stat-label {
        color: #666;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "document_info" not in st.session_state:
    st.session_state.document_info = []

if "show_sources" not in st.session_state:
    st.session_state.show_sources = True

if "avg_relevance" not in st.session_state:
    st.session_state.avg_relevance = 0.0

if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    default_api_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
    api_url = st.text_input("Backend API URL", default_api_url)    
    # Toggle for source visibility
    st.session_state.show_sources = st.toggle("Show Source Documents", st.session_state.show_sources)
    
    # Stats section
    st.divider()
    st.header("📊 Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.total_questions}</div>
            <div class="stat-label">Questions Asked</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        relevance = int(st.session_state.avg_relevance * 100) if st.session_state.total_questions > 0 else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{relevance}%</div>
            <div class="stat-label">Avg. Relevance</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Document upload section
    st.header("📤 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Upload documents (PDF, DOCX, TXT, PPTX, XLSX, CSV)",
        type=["pdf", "docx", "txt", "pptx", "xlsx", "csv"],
        accept_multiple_files=True
    )

    col1, col2 = st.columns(2)
    with col1:
        process_btn = st.button("📥 Process Documents", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear All", use_container_width=True)
    
    if clear_btn:
        st.session_state.document_info = []
        st.session_state.messages = []
        st.session_state.avg_relevance = 0.0
        st.session_state.total_questions = 0
        st.experimental_rerun()
    
    if process_btn and uploaded_files:
        for uploaded_file in uploaded_files:
            with st.status(f"Processing {uploaded_file.name}...", expanded=True) as status:
                st.write("Uploading file...")
                
                # Upload file to API
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    response = requests.post(f"{api_url}/uploadfile/", files=files)
                    
                    if response.status_code == 200:
                        task_id = response.json().get("task_id")
                        st.write(f"✅ Upload successful! Processing document...")
                        
                        # Check processing status
                        max_retries = 60  # Increased for larger documents
                        retries = 0
                        while retries < max_retries:
                            status_response = requests.post(
                                f"{api_url}/check_task_status/",
                                json={"task_id": task_id}
                            )
                            
                            if status_response.status_code == 200:
                                try:
                                    status_data = status_response.json()
                                    if "status" not in status_data:
                                        raise ValueError("Missing status in response")
                                    
                                    if status_data["status"] == "completed":
                                        st.write("✅ Document processed successfully!")
                                        
                                        # Get document summary
                                        try:
                                            summary_response = requests.get(f"{api_url}/summary/{task_id}")
                                            if summary_response.status_code == 200:
                                                summary_data = summary_response.json()
                                                # Add to session state
                                                st.session_state.document_info.append({
                                                    "task_id": task_id,
                                                    "filename": status_data.get("file", uploaded_file.name),
                                                    "summary": summary_data.get("summary", "No summary available")
                                                })
                                            else:
                                                st.session_state.document_info.append({
                                                    "task_id": task_id,
                                                    "filename": status_data.get("file", uploaded_file.name),
                                                    "summary": "Summary not available"
                                                })
                                        except Exception as e:
                                            st.warning(f"Couldn't retrieve summary: {str(e)}")
                                            st.session_state.document_info.append({
                                                "task_id": task_id,
                                                "filename": status_data.get("file", uploaded_file.name),
                                                "summary": "Summary not available"
                                            })
                                        
                                        break
                                    elif status_data["status"] == "failed":
                                        error = status_data.get("error", "Unknown error")
                                        st.error(f"Processing failed: {error}")
                                        status.update(label=f"❌ {uploaded_file.name} failed", state="error")
                                        break
                                    else:
                                        st.write(f"Still processing... (attempt {retries+1}/{max_retries})")
                                        progress = min(float(retries) / max_retries, 0.95)
                                        st.progress(progress)
                                        retries += 1
                                        time.sleep(3)  # Longer wait for big documents
                                except Exception as e:
                                    st.error(f"Error processing status: {str(e)}")
                                    status.update(label=f"❌ {uploaded_file.name} failed", state="error")
                                    break
                            else:
                                st.error("Failed to check processing status")
                                status.update(label=f"❌ {uploaded_file.name} failed", state="error")
                                break
                                
                        if retries >= max_retries:
                            st.error("Processing timed out. The document might still be processing in the background.")
                            status.update(label=f"⚠️ {uploaded_file.name} processing timeout", state="error")
                    else:
                        st.error(f"Upload failed: {response.text}")
                        status.update(label=f"❌ {uploaded_file.name} failed", state="error")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    status.update(label=f"❌ {uploaded_file.name} failed", state="error")
    
    # Display processed documents
    if st.session_state.document_info:
        st.divider()
        st.header("📚 Processed Documents")
        
        for doc in st.session_state.document_info:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
                st.markdown("**Document Summary:**")
                st.markdown(doc["summary"])
                st.markdown("</div>", unsafe_allow_html=True)

# --- Main Interface ---
st.title("📚 Document RAG Assistant")
st.caption("Upload your documents, ask questions, and get intelligent answers based on your content.")

# Check if documents are available
if not st.session_state.document_info:
    st.info("👈 Upload documents in the sidebar to get started!")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show sources if enabled and available
        if st.session_state.show_sources and msg["role"] == "assistant" and "sources" in msg:
            sources = msg["sources"]
            if sources:
                st.markdown("**Source Documents:**")
                for i, source in enumerate(sources):
                    # Determine relevance class based on score
                    relevance_class = "relevance-high"
                    relevance_text = "High Relevance"
                    if source['score'] < 0.7:
                        relevance_class = "relevance-medium"
                        relevance_text = "Medium Relevance"
                    if source['score'] < 0.5:
                        relevance_class = "relevance-low"
                        relevance_text = "Low Relevance"
                    
                    # Display relevance score with color coding
                    relevance_percent = int(source['score'] * 100)
                    
                    with st.expander(f"Source {i+1} - {Path(source['source']).name} - <span class='{relevance_class}'>{relevance_percent}% {relevance_text}</span>", expanded=i==0):
                        st.markdown(f"<div class='source-text'>{source['text']}</div>", unsafe_allow_html=True)
                        
                        # Display progress bar for relevance
                        st.progress(source['score'])

# Chat input
if st.session_state.document_info:  # Only show input if documents are loaded
    if question := st.chat_input("Ask questions about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer from API
        with st.chat_message("assistant"):
            with st.spinner("Searching documents for an answer..."):
                try:
                    response = requests.post(
                        f"{api_url}/ask", 
                        json={"question": question},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "I couldn't find an answer to your question.")
                        sources = data.get("sources", [])
                        
                        # Display answer
                        st.markdown(answer)
                        
                        # Update statistics
                        st.session_state.total_questions += 1
                        
                        # Calculate average relevance from sources
                        if sources:
                            avg_source_relevance = sum(s['score'] for s in sources) / len(sources)
                            # Update running average
                            current_avg = st.session_state.avg_relevance
                            question_count = st.session_state.total_questions
                            st.session_state.avg_relevance = (current_avg * (question_count - 1) + avg_source_relevance) / question_count
                        
                        # Display sources if enabled
                        if st.session_state.show_sources and sources:
                            st.markdown("**Source Documents:**")
                            for i, source in enumerate(sources):
                                relevance_class = "relevance-high"
                                relevance_text = "High Relevance"
                                if source['score'] < 0.7:
                                    relevance_class = "relevance-medium"
                                    relevance_text = "Medium Relevance"
                                if source['score'] < 0.5:
                                    relevance_class = "relevance-low"
                                    relevance_text = "Low Relevance"
                                
                                # Display relevance score with color coding
                                relevance_percent = int(source['score'] * 100)
                                
                                with st.expander(f"Source {i+1} - {Path(source['source']).name} - <span class='{relevance_class}'>{relevance_percent}% {relevance_text}</span>", expanded=i==0):
                                    st.markdown(f"<div class='source-text'>{source['text']}</div>", unsafe_allow_html=True)
                                    
                                    # Display progress bar for relevance
                                    st.progress(source['score'])
                        
                        # Add to chat history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources
                        })
                    else:
                        st.error(f"Error: API request failed with status code {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")