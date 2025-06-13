import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import torch
from PIL import Image
import open_clip
import io
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class VectorSearchService:
    def __init__(self):
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "film_locations")
        self.api_key = os.getenv("QDRANT_API_KEY")
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=self.qdrant_host,
            port=self.qdrant_port,
            api_key=self.api_key if self.api_key else None
        )
        
        # Initialize embedding models
        self.text_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        # Initialize CLIP for image embeddings
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32', 
            pretrained='openai',
            device=self.device
        )
        
        logger.info(f"VectorSearchService initialized with Qdrant at {self.qdrant_host}:{self.qdrant_port}")
        logger.info(f"Using device: {self.device}")

    def encode_text(self, text: str) -> List[float]:
        """Generate text embeddings using sentence transformer"""
        try:
            embedding = self.text_model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise

    def encode_image(self, image_data: Union[bytes, Image.Image]) -> List[float]:
        """Generate image embeddings using open_clip"""
        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
            else:
                image = image_data.convert("RGB")
            image_input = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise

    def search_similar_locations(
        self, 
        query_vector: List[float], 
        limit: int = 5,
        score_threshold: float = 0.7,
        location_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar locations in Qdrant"""
        try:
            # Prepare filter if location is specified
            search_filter = None
            if location_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="location",
                            match=MatchValue(value=location_filter)
                        )
                    ]
                )
            
            # Perform similarity search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                    "location": result.payload.get("location", "Unknown"),
                    "description": result.payload.get("description", ""),
                    "image_path": result.payload.get("image_path", ""),
                    "features": result.payload.get("features", [])
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} similar locations")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar locations: {e}")
            raise

    def search_by_text(self, text_query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search locations by text description"""
        query_vector = self.encode_text(text_query)
        return self.search_similar_locations(query_vector, **kwargs)

    def search_by_image(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """Search locations by image similarity"""
        query_vector = self.encode_image(image_data)
        return self.search_similar_locations(query_vector, **kwargs)

    def search_combined(
        self, 
        text_query: str, 
        image_data: Optional[bytes] = None,
        text_weight: float = 0.7,
        image_weight: float = 0.3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search using both text and image with weighted combination"""
        try:
            # Get text embedding
            text_vector = np.array(self.encode_text(text_query))
            if image_data:
                # Get image embedding
                image_vector = np.array(self.encode_image(image_data))
                # Ensure vectors have the same dimension (pad with zeros if needed)
                if len(text_vector) != len(image_vector):
                    max_len = max(len(text_vector), len(image_vector))
                    text_vector = np.pad(text_vector, (0, max_len - len(text_vector)))
                    image_vector = np.pad(image_vector, (0, max_len - len(image_vector)))
                # Combine vectors with weights
                combined_vector = (text_weight * text_vector + image_weight * image_vector)
                combined_vector = combined_vector / np.linalg.norm(combined_vector)
            else:
                combined_vector = text_vector
            return self.search_similar_locations(combined_vector.tolist(), **kwargs)
        except Exception as e:
            logger.error(f"Error in combined search: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}

# Global instance
vector_service = VectorSearchService()
