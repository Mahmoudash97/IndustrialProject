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
        self.qdrant_client = QdrantClient(url="http://localhost:6333")
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
                "search_results": [],
                "last_query": ""
            }
        return self.conversation_states[session_id]
    
    def update_conversation_state(self, session_id: str, updates: Dict[str, Any]):
        """Update conversation state"""
        state = self.get_conversation_state(session_id)
        state.update(updates)
    
    def extract_requirements(self, text: str) -> List[str]:
        """Extract location requirements from user text"""
        requirements = []
        text_lower = text.lower()
        
        # Location types
        location_keywords = {
            "mountain": "mountainous area",
            "beach": "coastal/beach location",
            "city": "urban environment",
            "forest": "forest/woodland",
            "desert": "desert landscape",
            "lake": "lakeside location",
            "indoor": "indoor setting",
            "outdoor": "outdoor setting",
            "modern": "modern architecture",
            "historic": "historical building",
            "rustic": "rustic/rural setting"
        }
        
        for keyword, description in location_keywords.items():
            if keyword in text_lower:
                requirements.append(description)
        
        return requirements
    
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
            model="tinyllama",
            temperature=0.7,
            request_timeout=60.0
        )
    
    def process_message(self, user_input: str, session_id: str, image: Optional[Image.Image] = None) -> str:
        """Process user message and return appropriate response."""
        try:
            state = self.location_service.get_conversation_state(session_id)
            print("session_id:", session_id)
            current_state = state["state"]
            user_input_lower = user_input.lower()
            
            # Handle greeting/initial state
            if current_state == ConversationState.GREETING:
                self.location_service.update_conversation_state(session_id, {
                    "state": ConversationState.COLLECTING_REQUIREMENTS
                })
                return "Hello! Welcome to our location finder service. I'm here to help you find the perfect filming or photoshoot location. What type of location are you looking for? Please describe your vision - indoor or outdoor, the style or mood you want, any specific features you need, etc."
            
            # Handle requirement collection
            elif current_state == ConversationState.COLLECTING_REQUIREMENTS:
                new_requirements = self.location_service.extract_requirements(user_input)
                state["requirements"].extend(new_requirements)
                
                self.location_service.update_conversation_state(session_id, {
                    "state": ConversationState.CONFIRMING_REQUIREMENTS,
                    "requirements": list(set(state["requirements"]))  # Remove duplicates
                })
                
                requirements_text = ", ".join(state["requirements"]) if state["requirements"] else "your general requirements"
                return f"Great! I understand you're looking for: {requirements_text}. Is that all you're looking for, or do you have any other specific requirements?"
            
            # Handle confirmation
            elif current_state == ConversationState.CONFIRMING_REQUIREMENTS:
                if any(confirm in user_input_lower for confirm in ["yes", "that's all", "that's it", "no more", "search", "find"]):
                    # Perform search
                    search_query = self.location_service.build_search_query(state["requirements"])
                    
                    if image:
                        # Image-based search
                        query_embedding = self.location_service.image_to_embedding(image)
                        search_type = "image and text"
                    else:
                        # Text-based search
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
                    # Collect more requirements
                    new_requirements = self.location_service.extract_requirements(user_input)
                    state["requirements"].extend(new_requirements)
                    
                    self.location_service.update_conversation_state(session_id, {
                        "requirements": list(set(state["requirements"]))
                    })
                    
                    requirements_text = ", ".join(state["requirements"])
                    return f"I've added those requirements. So now I have: {requirements_text}. Is that everything, or would you like to add more specific details?"
            
            # Handle follow-up questions or new searches
            elif current_state == ConversationState.RESPONDING:
                if any(new_search in user_input_lower for new_search in ["new search", "different", "other locations", "more options"]):
                    self.location_service.update_conversation_state(session_id, {
                        "state": ConversationState.GREETING,
                        "requirements": [],
                        "search_results": []
                    })
                    return "Of course! Let's start fresh. What type of location are you looking for this time?"
                
                else:
                    # Use LLM for general conversation about the results
                    context = f"Previous search results: {state['search_results'][:3]}"  # Limit context
                    prompt = f"{LOCATION_FINDER_SYSTEM_PROMPT}\n\nContext: {context}\n\nUser: {user_input}\n\nAssistant:"
                    
                    response = self.llm.complete(prompt)
                    return str(response).strip()
            
            # Default fallback
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
            response += f"**Location {i}** (Match: {score_percentage}%)\n"
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
