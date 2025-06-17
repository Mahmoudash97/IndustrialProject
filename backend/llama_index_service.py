# Enhanced llama_index_service.py
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient, models
from transformers import AutoProcessor, AutoModel
from PIL import Image
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
import re
import io
import hashlib
from llama_index.llms.ollama import Ollama


logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "qihoo360/fg-clip-large"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ConversationState(Enum):
    GREETING = "greeting"
    COLLECTING_REQUIREMENTS = "collecting_requirements"
    CONFIRMING_REQUIREMENTS = "confirming_requirements"
    SEARCHING = "searching"
    RESPONDING = "responding"

class LocationSearchService:
    def __init__(self):
        # Initialize Qdrant client
        from qdrant_client import QdrantClient

        self.qdrant_client = QdrantClient(
            url="https://cfd9b2d8-fc05-42a9-a872-8c3d26d0c400.eu-central-1-0.aws.cloud.qdrant.io:6333", 
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.mxDtOqWAzg6CtZqBdzl6nbUAMkH8rKsExwL-EKbLRf8"
        )

        self.collection_name = "film_locations"
        self.conversation_states: Dict[str, Dict[str, Any]] = {}

        # Initialize FG-CLIP model
        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE).eval()
        
        logger.info("LocationSearchService initialized successfully")
    
    def text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding using FG-CLIP"""
        with torch.no_grad():
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            features = self.model.get_text_features(**inputs)
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.cpu().numpy()[0]
    
    def image_to_embedding(self, image: Image.Image) -> np.ndarray:
        """Convert image to embedding using FG-CLIP"""
        with torch.no_grad():
            inputs = self.processor(images=[image], return_tensors="pt", padding=True)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            features = self.model.get_image_features(**inputs)
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.cpu().numpy()[0]

    def search_locations(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar locations in Qdrant"""
        try:
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    "location_id": result.payload["location_id"],
                    "image_path": result.payload["image_path"],
                    "similarity_score": result.score,
                    "point_id": result.id
                })
            
            logger.info(f"Found {len(results)} similar locations")
            return results
            
        except Exception as e:
            logger.error(f"Error searching locations: {e}")
            return []
    
    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        """Get conversation state for a session"""
        if session_id not in self.conversation_states:
            self.conversation_states[session_id] = {
                "state": ConversationState.GREETING,
                "requirements": [],
                "all_user_inputs": [],
                "search_results": [],
                "last_query": ""
            }
        return self.conversation_states[session_id]
    
    def update_conversation_state(self, session_id: str, updates: Dict[str, Any]):
        """Update conversation state"""
        state = self.get_conversation_state(session_id)
        state.update(updates)

    
    def build_search_query(self, requirements: List[str]) -> str:
        """Build search query from requirements"""
        if not requirements:
            return "beautiful filming location"
        return f"filming location with {', '.join(requirements)}"
    
    


# Enhanced system prompt for conversational flow
LOCATION_FINDER_SYSTEM_PROMPT = """You are a helpful location finder assistant for a filming and photoshoot location service. Your role is to help users find the perfect location for their needs.

CONVERSATION FLOW:
1. GREETING: Start by greeting the user warmly and asking what type of location they're looking for
2. COLLECTING: Gather their requirements (indoor/outdoor, style, mood, specific features, etc.)
3. CONFIRMING: After they provide requirements, ask "Is that all you're looking for, or do you have any other specific requirements?"
4. SEARCHING: Once they confirm, perform the search and present results

GUIDELINES:
- Be friendly and professional
- Ask clarifying questions to understand their vision
- Focus on practical filming/photoshoot considerations (lighting, space, accessibility, permits)
- Present search results in an organized, helpful way
- If no good matches found, suggest alternatives or ask for different requirements

Always stay in character as a location specialist."""

class ConversationalLocationBot:
    def __init__(self, location_service: LocationSearchService):
        self.location_service = location_service
        self.llm = Ollama(
            model="llama2",
            temperature=0.7,
            request_timeout=120.0
        )

    def detect_confirmation_with_llm(self, chat_history: str, last_user_message: str) -> bool:
        prompt = (
            "You are a helpful assistant for a location search service. "
            "Based on the conversation so far and the user's latest message, does the user confirm they are done providing requirements? "
            "Respond with only 'yes' or 'no'.\n\n"
            f"Conversation so far:\n{chat_history}\n"
            f"User's latest message: {last_user_message}\n"
            "Confirmation:"
        )
        response = self.llm.complete(prompt)
        return response.text.strip().lower().startswith("yes")
    
    def extract_and_rewrite_requirements_with_llm(self, chat_history: str) -> str:
        prompt = (
            "You are a helpful assistant for a location search service. "
            "Based on the conversation so far, extract all the user's requirements for a filming or photoshoot location, "
            "and rewrite them as a single, concise search query.\n\n"
            f"Conversation so far:\n{chat_history}\n"
            "Search query:"
        )
        response = self.llm.complete(prompt)
        return response.text.strip()
    
    def process_message(self, user_input: str, session_id: str, image: Optional[Image.Image] = None) -> str:
        try:
            state = self.location_service.get_conversation_state(session_id)
            print("session_id:", session_id)
            current_state = state["state"]

            # Append every user message to chat history
            state.setdefault("chat_history", []).append({"role": "user", "content": user_input})

            # Prepare chat history for LLM (last 8 turns for brevity)
            chat_history = "\n".join(
                [f"{msg['role'].capitalize()}: {msg['content']}" for msg in state["chat_history"][-8:]]
            )

            if current_state == ConversationState.GREETING:
                self.location_service.update_conversation_state(session_id, {
                    "state": ConversationState.COLLECTING_REQUIREMENTS
                })
                state["chat_history"].append({"role": "assistant", "content":
                    "Hello! Welcome to our location finder service. What type of location are you looking for? Please describe your vision—indoor or outdoor, style, mood, or any specific features you need."
                })
                return state["chat_history"][-1]["content"]

            elif current_state == ConversationState.COLLECTING_REQUIREMENTS:
                self.location_service.update_conversation_state(session_id, {
                    "state": ConversationState.CONFIRMING_REQUIREMENTS
                })
                state["chat_history"].append({"role": "assistant", "content":
                    "Great! Is that all you're looking for, or do you have any other specific requirements?"
                })
                return state["chat_history"][-1]["content"]

            elif current_state == ConversationState.CONFIRMING_REQUIREMENTS:
                # LLM determines if user is confirming
                is_confirm = self.detect_confirmation_with_llm(chat_history, user_input)
                print(f"User Input: {user_input}")
                print("------------------------------")
                print(f"combined_requirements: {chat_history}")
                print("------------------------------")
                if is_confirm:
                    # LLM rewrites all requirements into a search query
                    search_query = self.extract_and_rewrite_requirements_with_llm(chat_history)
                    print(f"Search Query: {search_query} END")
                    if image:
                        query_embedding = self.location_service.image_to_embedding(image)
                        search_type = "image and text"
                    else:
                        query_embedding = self.location_service.text_to_embedding(search_query)
                        search_type = "text"
                    results = self.location_service.search_locations(query_embedding, top_k=5)
                    self.location_service.update_conversation_state(session_id, {
                        "state": ConversationState.RESPONDING,
                        "search_results": results,
                        "last_query": search_query
                    })
                    return self._format_search_results(results, search_type)
                else:
                    self.location_service.update_conversation_state(session_id, {
                        "state": ConversationState.CONFIRMING_REQUIREMENTS
                    })
                    state["chat_history"].append({"role": "assistant", "content":
                        "I've added those requirements. Is that everything, or would you like to add more specific details?"
                    })
                    return state["chat_history"][-1]["content"]

            elif current_state == ConversationState.RESPONDING:
                state["chat_history"].append({"role": "assistant", "content":
                    "Is there anything specific you'd like to know about these locations, or would you like to search for different ones?"
                })
                return state["chat_history"][-1]["content"]

            return "I'm here to help you find locations! Please tell me what you're looking for, or say 'hi' to start over."
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again or start a new search."
    
    def _format_search_results(self, results: List[Dict], search_type: str) -> str:
        if not results:
            return "I couldn't find any locations matching your requirements. Would you like to try with different criteria or start a new search?"

        response = f"Great! I found {len(results)} locations based on your {search_type} search:\n\n"

        for i, result in enumerate(results, 1):
            score_percentage = int(result['similarity_score'] * 100)  # Use the correct key
            response += f"**Location {i}** (Link: https://studioscott.be/locaties/{result['location_id']}/%)\n"
            response += f"• ID: {result['location_id']} in {result['image_path']}\n"
            # Only include optional fields if present
            if result.get('description'):
                response += f"• Description: {result['description']}\n"
            if result.get('location_type'):
                response += f"• Type: {result['location_type']}\n"
            if result.get('features'):
                features = result['features'][:3]
                response += f"• Features: {', '.join(features)}\n"
            response += "\n"

        response += "Would you like more details about any of these locations, or would you like to search for something different?"
        return response


# Initialize global services
try:
    location_service = LocationSearchService()
    query_engine = ConversationalLocationBot(location_service)
    logger.info("Conversational location bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize location services: {e}")
    query_engine = None
    location_service = None
