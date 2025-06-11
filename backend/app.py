# /backend/app.py

import os
import logging
import logging.config
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from llama_index_service import query_engine, sanitize_text
import json
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multimodal Chatbot API",
    description="Advanced AI chatbot with image and text processing capabilities",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    message_id: str
    timestamp: str
    confidence: float = 0.0

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with system status"""
    return HealthResponse(
        status="healthy",
        message="Multimodal Chatbot API is running successfully",
        timestamp=datetime.now().isoformat(),
        version="2.0.0"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    query: str = Form(...),
    image: Optional[List[UploadFile]] = File(None)
):
    """Enhanced chat endpoint with multimodal support"""
    
    if not query_engine:
        logger.error("Query engine not initialized")
        raise HTTPException(
            status_code=503, 
            detail="AI service temporarily unavailable. Please try again later."
        )
    
    try:
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Sanitize input
        clean_query = sanitize_text(query.strip())
        
        if not clean_query:
            return ChatResponse(
                response="I'd be happy to help! Could you please tell me what you'd like to know?",
                sources=[],
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.9
            )
        
        # Handle greetings with enhanced responses
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in clean_query.lower() for greeting in greetings):
            return ChatResponse(
                response="Hello! 👋 I'm your AI assistant, ready to help you with questions about interior design, home decoration, and living spaces. What would you like to explore today?",
                sources=[],
                message_id=message_id,
                timestamp=timestamp,
                confidence=1.0
            )
        
        # Process images if provided
        image_context = ""
        if image and len(image) > 0:
            logger.info(f"Processing {len(image)} image(s)")
            image_context = f" [Note: User uploaded {len(image)} image(s) - image processing capabilities would be implemented here]"
        
        # Enhanced query with context
        enhanced_query = f"{clean_query}{image_context}"
        
        # Query the AI model
        logger.info(f"Processing query: {enhanced_query}")
        response = query_engine.query(enhanced_query)
        
        # Extract sources (this would be enhanced based on your actual response structure)
        sources = []
        if hasattr(response, 'source_nodes'):
            sources = [node.metadata.get('filename', 'Unknown') for node in response.source_nodes]
        
        # Calculate confidence (simple implementation)
        confidence = min(len(response.response) / 100, 1.0) if hasattr(response, 'response') else 0.8
        
        result = ChatResponse(
            response=str(response),
            sources=list(set(sources)),  # Remove duplicates
            message_id=message_id,
            timestamp=timestamp,
            confidence=confidence
        )
        
        logger.info(f"Query processed successfully. Message ID: {message_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        
        # Return a friendly error message instead of raising HTTP exception
        return ChatResponse(
            response="I apologize, but I encountered an issue processing your request. Could you please try rephrasing your question or try again in a moment?",
            sources=[],
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            confidence=0.0
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "response": "I'm experiencing some technical difficulties. Please try again later.",
            "sources": [],
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.0
        }
    )

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting Multimodal Chatbot API on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True
    )
