Intelligent Photo Search Chatbot

Advanced AI-Powered Film Location Discovery System

A sophisticated multimodal chatbot application that revolutionizes photo collection search for Studio Scott BV, combining cutting-edge AI with modern web technologies to enable natural language and image-based queries.
🚀 Features

    🤖 Intelligent Conversational AI - Powered by Meta Llama 3 with LlamaIndex RAG for context-aware responses

    🔍 Multimodal Search - Support for both text descriptions and image similarity search

    🎨 Modern Responsive UI - Clean React/Next.js interface with interactive chat experience

    📸 Image Processing - Advanced CLIP-based embeddings for visual similarity matching

    🗄️ Vector Database - Qdrant integration for efficient similarity search at scale

    📱 Mobile-Responsive Design - Optimized for desktop and mobile devices

    ⚡ Real-time Results - Fast semantic search with confidence scoring

    🎯 Location-Specific Search - Film location discovery with detailed metadata

🏗️ Architecture
System Overview

text
[User Interface] ↔ [FastAPI Backend] ↔ [Qdrant Vector DB]
                          ↓
                    [AI Models Layer]
                 ┌─────────┬─────────┐
            [Llama 3]  [CLIP]  [SentenceT.]

Technology Stack
Component	Technology	Purpose
Frontend	React, Next.js	Interactive chatbot UI
Backend	FastAPI (Python)	REST API, AI integration
Database	Qdrant	Vector storage & similarity search
Embeddings	open-clip-torch, SentenceTransformers	Image & text vectorization
Conversational AI	Meta Llama 3, LlamaIndex	Natural language understanding
Containerization	Docker	Database deployment
🚀 Quick Start
Prerequisites

    Python 3.10+

    Node.js 18+

    Docker

    Git

Installation

    Clone the repository

bash
git clone https://github.com/Mahmoudash97/IndustrialProject.git
cd IndustrialProject

Set up the vector database

bash
docker run -p 6333:6333 qdrant/qdrant

Install and start backend

bash
cd backend
conda create -n photochatbot python=3.10 -y
conda activate photochatbot
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000

Install and start frontend

    bash
    cd ../frontend
    npm install
    npm run dev

    Access the application

        Frontend: http://localhost:3000

        Backend API: http://localhost:8000

        API Documentation: http://localhost:8000/docs

        Qdrant Dashboard: http://localhost:6333/dashboard

📁 Project Structure

text
IndustrialProject/
├── frontend/                 # Next.js frontend application
│   ├── components/          # React components
│   ├── styles/             # CSS modules
│   ├── pages/              # Next.js pages
│   └── package.json        # Frontend dependencies
├── backend/                 # FastAPI backend application
│   ├── app.py              # Main FastAPI application
│   ├── vector_service.py   # Qdrant integration
│   ├── llama_index_service.py # AI model integration
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment configuration
├── docs/                   # Project documentation
├── package.json           # Root workspace configuration
└── README.md              # This file

🔧 Configuration
Backend Environment (.env)

text
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=film_locations

# AI Model Configuration
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
LLM_MODEL=llama3

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

Frontend Environment (.env.local)

text
NEXT_PUBLIC_API_URL=http://localhost:8000

🎯 Usage
Text-Based Search

text
User: "Show me modern kitchens in Amsterdam"
Bot: Found 5 matching locations with modern kitchen features...

Image-Based Search

    Click the image upload button

    Select a reference image

    Receive visually similar location matches

Combined Search

    Enter text description + upload reference image

    Get results matching both criteria with weighted scoring

🏢 Client Information

Project: Intelligent Photo Search Chatbot
Client: Studio Scott BV
Purpose: Streamline photo collection search and discovery
Industry: Film Production & Location Scouting
🛠️ Development
Key Features Implemented

    Multimodal Embedding Generation - Text and image vectorization using state-of-the-art models

    Semantic Similarity Search - Qdrant-powered vector database with cosine similarity

    Conversational Interface - Natural language processing with context awareness

    Real-time Chat Experience - Interactive UI with loading states and result visualization

    Scalable Architecture - Modular design supporting future enhancements

API Endpoints

    POST /chat - Main chatbot interaction endpoint

    GET /health - System health check

    GET /locations/search - Direct location search

    GET /collections/info - Database statistics

🚧 Known Limitations

    Multi-criteria Queries - Complex multi-location searches need refinement

    Output Formatting - Chat response presentation being enhanced

    Hardware Requirements - GPU recommended for optimal performance

📋 Requirements
Python Dependencies

text
fastapi==0.115.12
uvicorn==0.33.0
sentence-transformers==3.2.1
torch==2.4.1
qdrant-client
open-clip-torch
llama-index-core==0.11.23

Node.js Dependencies

json
{
  "next": "latest",
  "react": "latest",
  "framer-motion": "latest"
}

🤝 Contributing

    Fork the repository

    Create a feature branch

    Commit your changes

    Push to the branch

    Create a Pull Request

📄 License

This project is developed for Studio Scott BV as part of an industrial collaboration.
👥 Team

Developers: Mahmoud and Badr
Client: Studio Scott BV
Date: June 2025
