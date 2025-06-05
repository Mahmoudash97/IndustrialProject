from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llama_index_service import query_engine, sanitize_text
import logging

# Configure structured logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chat API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(query: str):
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Empty query")
            
        sanitized = sanitize_text(query)
        response = query_engine.query(sanitized)
        
        return {
            "response": str(response).strip(),
            "sources": [node.metadata["filename"] for node in response.source_nodes]
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Processing error") from e
