import torch
import numpy as np
from transformers import AutoProcessor, AutoModel
from qdrant_client import QdrantClient
from PIL import Image
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from llama_index.llms.ollama import Ollama

logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "qihoo360/fg-clip-large"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class ConversationState(Enum):
    GREETING = "greeting"
    SEARCHING = "searching"

class LocationSearchService:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url="https://cfd9b2d8-fc05-42a9-a872-8c3d26d0c400.eu-central-1-0.aws.cloud.qdrant.io:6333",
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.mxDtOqWAzg6CtZqBdzl6nbUAMkH8rKsExwL-EKbLRf8"
        )
        self.collection_name = "film_locations"
        self.conversation_states: Dict[str, Dict[str, Any]] = {}

        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE).eval()

        logger.info("LocationSearchService initialized successfully")

    def text_to_embedding(self, text: str) -> np.ndarray:
        with torch.no_grad():
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            features = self.model.get_text_features(**inputs)
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.cpu().numpy()[0]

    def image_to_embedding(self, image: Image.Image) -> np.ndarray:
        with torch.no_grad():
            inputs = self.processor(images=[image], return_tensors="pt", padding=True)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            features = self.model.get_image_features(**inputs)
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.cpu().numpy()[0]

    def search_locations(self, query_embedding: np.ndarray, top_k: int = 10, unique_locations: int = 3) -> List[Dict]:
        try:
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k * 3,
                with_payload=True
            )
            seen_names = set()
            unique_results = []
            for result in search_results:
                name = result.payload["location_title"]
                if name not in seen_names:
                    seen_names.add(name)
                    unique_results.append({
                        "location_title": name,
                        "location_url": result.payload["location_url"]
                    })
                if len(unique_results) >= unique_locations:
                    break
            logger.info(f"Found {len(unique_results)} unique locations")
            return unique_results
        except Exception as e:
            logger.error(f"Error searching locations: {e}")
            return []

class ConversationalLocationBot:
    def __init__(self, location_service: LocationSearchService):
        self.location_service = location_service
        self.llm = Ollama(
            model="tinyllama",
            temperature=0.7,
            request_timeout=60.0
        )

    def process_message(self, user_input: str, session_id: str, image: Optional[Image.Image] = None) -> List[str]:
        try:
            # Use internal session tracking or stateless if preferred
            if session_id not in self.location_service.conversation_states:
                self.location_service.conversation_states[session_id] = {
                    "state": ConversationState.GREETING,
                    "chat_history": []
                }

            state = self.location_service.conversation_states[session_id]
            state["chat_history"].append({"role": "user", "content": user_input})
            current_state = state["state"]

            if current_state == ConversationState.GREETING:
                state["state"] = ConversationState.SEARCHING
                greeting = "Hello! Welcome to our location finder service. What type of location are you looking for? Please describe your vision—indoor or outdoor, style, mood, or any specific features you need."
                state["chat_history"].append({"role": "assistant", "content": greeting})
                return [greeting]

            elif current_state == ConversationState.SEARCHING:
                ack_message = "Great, I'll start searching for it."
                state["chat_history"].append({"role": "assistant", "content": ack_message})

                search_query = user_input.strip()[:70]
                if image:
                    query_embedding = self.location_service.image_to_embedding(image)
                    search_type = "image and text"
                else:
                    query_embedding = self.location_service.text_to_embedding(search_query)
                    search_type = "text"

                results = self.location_service.search_locations(query_embedding, top_k=10, unique_locations=3)

                # Session ends after search
                self.location_service.conversation_states.pop(session_id, None)

                result_message = self._format_search_results(results, search_type)
                closing_message = "Thank you for using our location finder! Send a message to start a new search."

                return [ack_message, result_message, closing_message]

            else:
                # Fallback: reset to SEARCHING
                self.location_service.conversation_states[session_id]["state"] = ConversationState.SEARCHING
                return ["Please describe what kind of location you are looking for to begin a new search."]

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ["I apologize, but I'm experiencing technical difficulties. Please try again."]


    def _format_search_results(self, results: List[Dict], search_type: str) -> str:
        if not results:
            return "I couldn't find any locations matching your requirements."

        response = f"Here are the {len(results)} best locations from your {search_type} search:\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. [{result['location_title']}]( {result['location_url']} )\n"
        return response.strip()


# Initialize global services
try:
    location_service = LocationSearchService()
    query_engine = ConversationalLocationBot(location_service)
    logger.info("Conversational location bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize location services: {e}")
    query_engine = None
    location_service = None
