# /mnt/c/Users/asadi/Desktop/ChatBot/ChatBot_Reop/IndustrialProject/backend/llama_index_service.py


from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.node_parser import SemanticSplitterNodeParser
import os
import re
import logging

logger = logging.getLogger(__name__)

# Enhanced Emoji Filter Pattern
EMOJI_PATTERN = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U00002500-\U00002BEF"  # chinese symbols
    u"\U00002702-\U000027B0"
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    u"\U0001f926-\U0001f937"
    u"\U00010000-\U0010ffff"
    u"\u2640-\u2642"
    u"\u2600-\u2B55"
    u"\u200d"
    u"\u23cf"
    u"\u23e9"
    u"\u231a"
    u"\ufe0f"
    u"\u3030"
    "]+", flags=re.UNICODE
)

def sanitize_text(text: str) -> str:
    """Remove emojis and normalize text for processing"""
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub('', text)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

# Chat system prompt for better conversational behavior
SYSTEM_PROMPT = (
    "You are a helpful, respectful, and honest assistant. "
    "Always answer as helpfully as possible. "
    "If the user greets you (hello, hi, hey), respond with a friendly greeting."
    " If you don't know the answer, say so honestly."
)

def build_prompt(user_input: str) -> str:
    """Format prompt for Llama chat models."""
    return (
        f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{user_input} [/INST]"
    )

# Advanced Embedding Setup with error handling
try:
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        embed_batch_size=16,
    )
    logger.info("Embedding model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    raise

class AdvancedIndexer:
    def __init__(self, data_dir: str = "sample_data"):
        self.data_dir = data_dir
        self._ensure_sample_data()
        try:
            self.llm = Ollama(
                model="llama3", 
                temperature=0.3, 
                top_k=50,
                request_timeout=60.0
            )
            self.node_parser = SemanticSplitterNodeParser(
                buffer_size=2,
                breakpoint_percentile_threshold=95,
                embed_model=Settings.embed_model
            )
            logger.info("LLM and node parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM components: {e}")
            raise

    def _ensure_sample_data(self):
        os.makedirs(self.data_dir, exist_ok=True)
        samples = {
            "doc1.txt": "Modern living room with green sofa and wooden floor. Features comfortable seating and natural lighting.",
            "doc2.txt": "Compact kitchen connected to bright open space. Includes modern appliances and efficient storage solutions.",
            "doc3.txt": "Welcome to our AI assistant! I can help you with questions about interior design, home decoration, and living spaces.",
            "doc4.txt": "Our services include room planning, furniture recommendations, color schemes, and space optimization tips."
        }
        for filename, content in samples.items():
            path = os.path.join(self.data_dir, filename)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(sanitize_text(content))

    def build_index(self):
        try:
            documents = SimpleDirectoryReader(
                self.data_dir,
                file_metadata=lambda x: {"filename": os.path.basename(x)}
            ).load_data()
            if not documents:
                raise ValueError("No documents found to index")
            nodes = self.node_parser.get_nodes_from_documents(documents)
            storage_context = StorageContext.from_defaults()
            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                show_progress=True
            )
            logger.info(f"Index built successfully with {len(nodes)} nodes")
            return index
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise

try:
    indexer = AdvancedIndexer()
    index = indexer.build_index()
    # Wrap the query_engine to always use chat prompt formatting
    class ChatQueryEngine:
        def __init__(self, base_engine):
            self.base_engine = base_engine
        def query(self, user_input):
            prompt = build_prompt(user_input)
            return self.base_engine.query(prompt)
    query_engine = ChatQueryEngine(
        index.as_query_engine(
            llm=indexer.llm,
            similarity_top_k=3,
            response_mode="compact",
            node_postprocessors=[
                MetadataReplacementPostProcessor(target_metadata_key="filename")
            ]
        )
    )
    logger.info("Query engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize query engine: {e}")
    query_engine = None
