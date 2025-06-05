# Correct import structure
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

# --- Emoji Filter Pattern ---
EMOJI_PATTERN = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+", flags=re.UNICODE
)

def sanitize_text(text: str) -> str:
    """Remove emojis and normalize text"""
    return EMOJI_PATTERN.sub('', text).strip()

# --- Advanced Embedding Setup ---
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    embed_batch_size=32,
    pooling="mean"
)

# --- Optimized Index Construction ---
class AdvancedIndexer:
    def __init__(self, data_dir: str = "sample_data"):
        self.data_dir = data_dir
        self._ensure_sample_data()
        self.llm = Ollama(model="llama3", temperature=0.3, top_k=50)
        self.node_parser = SemanticSplitterNodeParser(
            buffer_size=2,
            breakpoint_percentile_threshold=95,
            embed_model=Settings.embed_model
        )

    def _ensure_sample_data(self):
        os.makedirs(self.data_dir, exist_ok=True)
        samples = {
            "doc1.txt": "Modern living room with green sofa and wooden floor. 🛋️",
            "doc2.txt": "Compact kitchen connected to bright open space. 🔪"
        }
        for filename, content in samples.items():
            path = os.path.join(self.data_dir, filename)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(sanitize_text(content))

    def build_index(self):
        documents = SimpleDirectoryReader(
            self.data_dir,
            file_metadata=lambda x: {"filename": x}
        ).load_data()
        
        nodes = self.node_parser.get_nodes_from_documents(documents)
        storage_context = StorageContext.from_defaults()
        return VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            show_progress=True
        )

# Initialize indexer (singleton pattern)
indexer = AdvancedIndexer()
index = indexer.build_index()
query_engine = index.as_query_engine(
    llm=indexer.llm,
    similarity_top_k=3,
    response_mode="compact",
    node_postprocessors=[
        MetadataReplacementPostProcessor(target_metadata_key="filename")
    ]
)
