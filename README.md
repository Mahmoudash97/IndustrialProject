# Multimodal Chatbot Starter

# Advanced AI Chatbot - Full Stack Integration

A sophisticated chatbot application combining a modern Next.js frontend with a powerful FastAPI backend featuring RAG (Retrieval-Augmented Generation) capabilities.

## Features

- 🤖 Advanced AI chat interface with LlamaIndex RAG
- 🎨 Modern, responsive UI with dark mode support
- 📁 File upload and image processing
- 🔊 Text-to-speech and sound notifications
- 💾 Persistent chat history with local storage
- 🎯 Type-safe API integration
- 📱 Mobile-responsive design

## Quick Start

1. **Install Dependencies**
npm run install:all


2. **Start Development Servers**
npm run dev


3. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure
├── frontend/ # Next.js frontend application
├── backend/ # FastAPI backend application
├── package.json # Root workspace configuration
└── README.md # This file




## Development

- **Frontend**: Next.js with React, CSS Modules, and modern features
- **Backend**: FastAPI with LlamaIndex, Ollama, and HuggingFace embeddings
- **Integration**: Next.js rewrites for seamless API proxying

## Scripts

- `npm run dev` - Start both frontend and backend
- `npm run build` - Build frontend for production
- `npm run clean` - Clean build artifacts

## Environment Variables

See `.env.local` (frontend) and `.env` (backend) for configuration options.


Git Configuration

File: .gitignore
# Dependencies
node_modules/
*/node_modules/

# Production builds
.next/
out/
dist/
build/

# Environment variables
.env
.env.local
.env.production
.env.staging

# Logs
*.log
logs/

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Uploads
uploads/
temp/

# Testing
coverage/
.coverage
.pytest_cache/

# Cache
.cache/
.parcel-cache/


