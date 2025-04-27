import asyncio
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import shutil
import os
from pathlib import Path
from rag import process_document, query_document
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
PROCESSING_STATUS = {}  # key: task_id, value: status info

class TaskStatus(BaseModel):
    task_id: str

class Question(BaseModel):
    question: str

@app.post("/uploadfile/")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process a document file"""
    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{file.filename}")
    
    # Save uploaded file
    try:
        logger.info(f"Uploading and saving file to {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        PROCESSING_STATUS[task_id] = {"status": "processing", "file": file.filename}
        logger.info(f"Starting document processing for {file.filename}")

        # Add the document processing to the background task queue
        background_tasks.add_task(process_and_update_status, task_id, file_path)
        
        return {"task_id": task_id}  # Return the task ID to the frontend for status checking

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        PROCESSING_STATUS[task_id] = {"status": "failed", "error": str(e)}
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def process_and_update_status(task_id: str, file_path: str):
    """Process the file and update the task status"""
    try:
        # Process the document
        result = await process_document(file_path, task_id)
        
        # Update the status
        PROCESSING_STATUS[task_id] = result
        logger.info(f"Document processing completed for task {task_id} with status: {result['status']}")
    except Exception as e:
        PROCESSING_STATUS[task_id] = {"status": "failed", "error": str(e)}
        logger.error(f"Error during document processing for task {task_id}: {str(e)}")

@app.post("/check_task_status/") 
async def check_task_status(task: TaskStatus):
    """Check the status of a document processing task"""
    if task.task_id in PROCESSING_STATUS:
        return PROCESSING_STATUS[task.task_id]
    else:
        return {"status": "not_found", "error": "Invalid task ID"}

@app.post("/ask")
async def ask_question(query: Question):
    """Answer a question based on the processed documents"""
    try:
        logger.info(f"Received question: {query.question}")
        
        start_time = time.time()
        result = await query_document(query.question)
        duration = time.time() - start_time
        
        logger.info(f"Processing completed in {duration:.2f} seconds")
        return result
    except Exception as e:
        logger.error(f"Question answering error: {str(e)}")
        return {"answer": f"Error: {str(e)}", "sources": []}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/summary/{task_id}")
async def get_document_summary(task_id: str):
    """Get the summary of a processed document"""
    if task_id in PROCESSING_STATUS and PROCESSING_STATUS[task_id]["status"] == "completed":
        return {
            "summary": PROCESSING_STATUS[task_id].get("summary", "No summary available"),
            "file": PROCESSING_STATUS[task_id].get("file", "Unknown file")
        }
    elif task_id in PROCESSING_STATUS:
        return {"error": f"Document processing not completed: {PROCESSING_STATUS[task_id]['status']}"}
    else:
        raise HTTPException(status_code=404, detail="Task ID not found")