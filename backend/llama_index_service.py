from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import os

# --- Use local embeddings instead of OpenAI ---
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# --- Setup data ---
DATA_DIR = "sample_data"
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DATA_DIR, "doc1.txt")):
    with open(os.path.join(DATA_DIR, "doc1.txt"), "w") as f:
        f.write("This is a modern living room with a green sofa and wooden floor.")
if not os.path.exists(os.path.join(DATA_DIR, "doc2.txt")):
    with open(os.path.join(DATA_DIR, "doc2.txt"), "w") as f:
        f.write("There is a small kitchen area connected to a bright open space.")

# --- Build index ---
documents = SimpleDirectoryReader(DATA_DIR).load_data()
index = VectorStoreIndex.from_documents(documents)

# --- Use Ollama LLM ---
llm = Ollama(model="llama3")  # Or "phi3", "mistral", etc.
query_engine = index.as_query_engine(llm=llm, similarity_top_k=3, response_mode="compact")

def chat_with_index(query, image_bytes):
    if not query:
        return {"message": "Please enter a text query.", "results": []}
    response = query_engine.query(query)
    return {
        "message": str(response),
        "results": []
    }
