from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from llama_index_service import LocationSearchService, query_engine, location_service
import logging
import logging.config
import asyncio
import uuid
import os
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import io
from PIL import Image


# Configure structured logging
try:
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
except:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Advanced AI Chat API", 
    version="3.0",
    description="RAG-powered chatbot API with image support",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", '["*"]')
if isinstance(cors_origins, str):
    import json
    try:
        cors_origins = json.loads(cors_origins)
    except:
        cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    message_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    sources: List[str] = []
    message_id: str
    timestamp: str
    status: str = "delivered"
    session_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    query_engine_status: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    file_id: str

def get_max_file_size():
    return int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default

def get_allowed_file_types():
    return os.getenv("ALLOWED_FILE_TYPES", "image/jpeg,image/png,image/gif,image/webp").split(",")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """Enhanced chat endpoint with location search integration."""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Use provided session_id or generate a new one
        session_id = session_id or str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        logging.info(f"Processing chat request: {message_id[:8]}... Session: {session_id[:8]}")

        # Handle image if provided
        pil_image = None
        if image:
            if image.size > get_max_file_size():
                raise HTTPException(status_code=413, detail="File too large")
            if image.content_type not in get_allowed_file_types():
                raise HTTPException(status_code=400, detail="Unsupported file type")
            image_content = await image.read()
            pil_image = Image.open(io.BytesIO(image_content)).convert("RGB")
            logging.info(f"Image processed: {image.filename}")

        # Process with conversational bot
        if query_engine is None:
            raise HTTPException(status_code=503, detail="Location service not available")

        response_text = query_engine.process_message(query, session_id, pil_image)

        # Get current session state for metadata
        if location_service:
            state = location_service.get_conversation_state(session_id)
            sources = [f"location_{result['location_id']}" for result in state.get('search_results', [])]
        else:
            sources = []

        logging.info(f"Response generated for {message_id[:8]} with {len(sources)} location sources")

        return ChatResponse(
            message=response_text,
            sources=sources,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            status="delivered",
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Chat error: {str(e)}", exc_info=True)
        return ChatResponse(
            message="I apologize, but I'm experiencing technical difficulties. Please try again.",
            sources=[],
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            status="error",
            session_id=session_id
        )

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads with validation and processing"""
    try:
        if file.size > get_max_file_size():
            raise HTTPException(status_code=413, detail="File too large")
        
        if file.content_type not in get_allowed_file_types():
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        content = await file.read()
        file_id = str(uuid.uuid4())
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{file_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {file_path}")
        
        return UploadResponse(
            message=f"File '{file.filename}' uploaded successfully",
            filename=file.filename,
            size=len(content),
            file_id=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    query_engine_status = "healthy" if query_engine is not None else "unavailable"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="3.0",
        query_engine_status=query_engine_status
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Advanced AI Chat API",
        "version": "3.0",
        "status": "running",
        "docs": "/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else "disabled",
        "endpoints": {
            "chat": "/chat",
            "upload": "/upload", 
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
