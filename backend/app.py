from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama REST API endpoint

SYSTEM_PROMPT = (
    "You are an AI assistant for a professional search/chat application. "
    "Please provide clear, concise, and factual responses, ideally 1-3 sentences. "
    "Only elaborate if the user explicitly asks for a detailed description."
)

@app.post("/chat")
async def chat(query: str = Form(None)):
    # Prepend system prompt to the query for consistent behavior
    prompt = f"{SYSTEM_PROMPT}\nUser: {query}\nAI:"
    payload = {
        "model": "llama3",  # or your preferred model
        "prompt": prompt,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        r.raise_for_status()
        response_json = r.json()
        return {"message": response_json['response'].strip()}
    except Exception as e:
        return {"message": f"Error querying Ollama: {str(e)}"}

