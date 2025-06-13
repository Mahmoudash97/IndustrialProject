# /backend/app.py
import os
import logging
import logging.config
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from llama_index_service import query_engine, sanitize_text
from vector_service import vector_service
import json
import uuid
from datetime import datetime
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Film Location Similarity Search API",
    description="Advanced AI chatbot with location similarity search capabilities",
    version="3.0.0",
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

class LocationResult(BaseModel):
    id: str
    score: float
    location: str
    description: str
    image_path: str
    features: List[str]

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    locations: List[LocationResult] = []
    message_id: str
    timestamp: str
    confidence: float = 0.0
    search_type: str = "text"

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str
    qdrant_info: dict = {}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with system status"""
    qdrant_info = vector_service.get_collection_info()
    
    return HealthResponse(
        status="healthy",
        message="Film Location Similarity Search API is running successfully",
        timestamp=datetime.now().isoformat(),
        version="3.0.0",
        qdrant_info=qdrant_info
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    query: str = Form(...),
    images: Optional[List[UploadFile]] = File(None)
):
    """Enhanced chat endpoint with location similarity search"""
    
    try:
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Sanitize input
        clean_query = sanitize_text(query.strip())
        
        if not clean_query and (not images or len(images) == 0):
            return ChatResponse(
                response="I'd be happy to help! Please provide a description or upload images of the type of location you're looking for.",
                sources=[],
                locations=[],
                message_id=message_id,
                timestamp=timestamp,
                confidence=0.9,
                search_type="greeting"
            )
        
        # Handle greetings
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if clean_query and any(greeting in clean_query.lower() for greeting in greetings):
            return ChatResponse(
                response="Hello! 👋 I'm your AI assistant for finding film locations. You can describe the type of location you're looking for (like 'modern kitchen' or 'outdoor driveway') or upload images for visual similarity search. How can I help you find the perfect location today?",
                sources=[],
                locations=[],
                message_id=message_id,
                timestamp=timestamp,
                confidence=1.0,
                search_type="greeting"
            )
        
        # Determine search type and perform similarity search
        search_results = []
        search_type = "text"
        
        if images and len(images) > 0:
            # Image-based or combined search
            image_data = await images[0].read()  # Use first image for search
            
            if clean_query:
                # Combined search
                search_results = vector_service.search_combined(
                    text_query=clean_query,
                    image_data=image_data,
                    limit=5,
                    score_threshold=0.6
                )
                search_type = "combined"
            else:
                # Image-only search
                search_results = vector_service.search_by_image(
                    image_data=image_data,
                    limit=5,
                    score_threshold=0.6
                )
                search_type = "image"
        elif clean_query:
            # Text-only search
            search_results = vector_service.search_by_text(
                text_query=clean_query,
                limit=5,
                score_threshold=0.6
            )
            search_type = "text"
        
        # Convert search results to LocationResult objects
        locations = []
        for result in search_results:
            locations.append(LocationResult(
                id=str(result["id"]),
                score=result["score"],
                location=result["location"],
                description=result["description"],
                image_path=result["image_path"],
                features=result["features"]
            ))
        
        # Generate AI response based on search results
        if locations:
            location_names = [loc.location for loc in locations[:3]]
            features_found = []
            for loc in locations[:3]:
                features_found.extend(loc.features)
            unique_features = list(set(features_found))
            
            if search_type == "image":
                ai_response = f"Based on your uploaded image, I found {len(locations)} similar locations: {', '.join(location_names)}. These locations feature {', '.join(unique_features[:5])}."
            elif search_type == "combined":
                ai_response = f"Based on your description '{clean_query}' and uploaded image, I found {len(locations)} matching locations: {', '.join(location_names)}. These locations feature {', '.join(unique_features[:5])}."
            else:
                ai_response = f"Based on your search for '{clean_query}', I found {len(locations)} relevant locations: {', '.join(location_names)}. These locations feature {', '.join(unique_features[:5])}."
            
            # Also get AI commentary using the original query engine
            if query_engine:
                try:
                    enhanced_query = f"Provide information about film locations that match: {clean_query}. Focus on interior design and visual characteristics."
                    ai_commentary = query_engine.query(enhanced_query)
                    ai_response += f"\n\n{str(ai_commentary)}"
                except Exception as e:
                    logger.warning(f"Could not get AI commentary: {e}")
        else:
            ai_response = f"I couldn't find any locations matching your search criteria. Try using different keywords or uploading a reference image to help me understand what you're looking for."
        
        # Calculate confidence based on search results
        confidence = min(len(locations) / 5.0, 1.0) if locations else 0.3
        
        result = ChatResponse(
            response=ai_response,
            sources=["Vector Database", "LLaMA AI Model"],
            locations=locations,
            message_id=message_id,
            timestamp=timestamp,
            confidence=confidence,
            search_type=search_type
        )
        
        logger.info(f"Search completed: {search_type} search, {len(locations)} results found")
        return result
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        
        return ChatResponse(
            response="I apologize, but I encountered an issue processing your request. Please try rephrasing your question or try again in a moment.",
            sources=[],
            locations=[],
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            confidence=0.0,
            search_type="error"
        )

@app.get("/locations/search")
async def search_locations(
    q: str,
    limit: int = 5,
    score_threshold: float = 0.6,
    location_filter: Optional[str] = None
):
    """Direct endpoint for location similarity search"""
    try:
        results = vector_service.search_by_text(
            text_query=q,
            limit=limit,
            score_threshold=score_threshold,
            location_filter=location_filter
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error in location search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/info")
async def get_collection_info():
    """Get information about the vector database collection"""
    try:
        info = vector_service.get_collection_info()
        return info
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting Film Location Similarity Search API on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True
    )
