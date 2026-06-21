# Graph-Augmented RAG (GraphRAG)

A powerful, multimodal Graph-Augmented Retrieval-Augmented Generation (RAG) system. This application parses complex documents (including images and tables), builds an interactive knowledge graph, and uses a Vision-Language Model (Groq / local MLX VLM) to provide highly accurate, visually-cited answers.

## Architecture
- **Backend:** Python (FastAPI), PyTorch, ChromaDB, IBM Docling, NetworkX
- **Frontend:** React, Vite, ReactFlow
- **Database:** MongoDB (Optional, falls back to in-memory for local-only execution)
- **LLM:** Groq API

---

## 🚀 Setup Guide

Because this application runs heavy Machine Learning embedding models (PyTorch, SentenceTransformers), it requires at least **2GB to 4GB of RAM** to run smoothly. It is highly recommended to run the backend locally.

### 1. Prerequisites
Before starting, ensure you have installed:
- **Python 3.9+** (Ensure Python is added to your system environment variables/PATH)
- **Node.js 18+**
- **Git**

You will also need:
1. **Groq API Key:** For lightning-fast LLM inference.
2. **MongoDB URI (Optional):** For storing the GraphRAG document state and chat history. If not provided, the application will run in local-only in-memory mode (data will not persist after restarting the backend).

---

### 2. OS-Specific Backend Setup

Choose the guide below matching your operating system:

#### 🍎 Option A: macOS Setup Guide

1. **Open Terminal** and navigate to the project's backend directory:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required Python dependencies:**
   - **For Apple Silicon (M1/M2/M3/M4) Macs:**
     Install the full dependency suite, including native local MLX Vision-Language Model acceleration:
     ```bash
     pip install -r requirements.txt
     ```
   - **For Intel Macs:**
     Install the lightweight dependency suite (excludes Apple Silicon-specific MLX packages):
     ```bash
     pip install -r Win_requirements.txt
     ```

4. **Configure Environment Variables:**
   Create a new file named `.env` inside the `backend` directory (`backend/.env`) and add your keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   MONGO_URI=your_mongodb_connection_string_here  # Optional: Leave empty or omit for in-memory mode
   ```

5. **Start the Python Backend:**
   With the virtual environment active, run the following command from the `backend` directory:
   ```bash
   python -m uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload --env-file .env
   ```
   *The API server will run at `http://127.0.0.1:8000`.*

---

#### 🪟 Option B: Windows Setup Guide

1. **Open PowerShell or Command Prompt (CMD)** and navigate to the project's backend directory:
   ```powershell
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   
   # If using PowerShell:
   .\venv\Scripts\Activate.ps1
   
   # If using Command Prompt:
   .\venv\Scripts\activate.bat
   ```

3. **Install the required Python dependencies:**
   Windows must use `Win_requirements.txt` to avoid macOS-specific `mlx` and Windows-incompatible `uvloop` libraries:
   ```powershell
   pip install -r Win_requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a new file named `.env` inside the `backend` directory (`backend/.env`) and add your keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   MONGO_URI=your_mongodb_connection_string_here  # Optional: Leave empty or omit for in-memory mode
   ```

5. **Start the Python Backend:**
   With the virtual environment active, run the following command from the `backend` directory:
   ```powershell
   python -m uvicorn app.api:app --host 127.0.0.1 --port 8000 --reload --env-file .env
   ```
   *The API server will run at `http://127.0.0.1:8000`.*

---

### 3. Frontend Setup

The frontend is a Vite-powered React application with interactive ReactFlow graphs.

1. **Open a new terminal / command prompt window** and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Access the Application:**
   Open your browser and navigate to the URL provided by Vite (usually `http://localhost:5180`).

---

## 🛠️ Usage
1. **Sign Up / Login:** Create an account on the local dashboard (works in both MongoDB and in-memory fallback modes).
2. **Upload a Document:** Navigate to the Dashboard and upload a PDF or DOCX. The backend will parse the text, tables, and images, embed them into ChromaDB, and build a NetworkX knowledge graph.
3. **Explore the Graph:** Click on the generated nodes in the right-hand panel to see semantic relationships and entity extraction.
4. **Chat:** Ask questions about the document. The system will retrieve the most relevant semantic chunks and graph edges, and the LLM will generate an answer with inline citations (e.g., `(Fig. 1)` or `(Page 3)`).

---

## 🌟 Hackathon Stretch Goals Achieved

This project successfully implements all the bonus features requested in the hackathon problem statement:

1. **Agentic Reasoning & Adversarial Robustness:**
   - **Query Decomposition:** Complex, multi-hop user questions (e.g. "Compare revenue in Q1 and Q2") are automatically broken down into atomic sub-queries and routed to Groq (`llama-3.3-70b-versatile`) for highly targeted semantic retrieval.
   - **Robust System Prompt:** The LLM is explicitly instructed to avoid hallucinations and confidently state when a question is unanswerable based on the provided document context, successfully handling "trick" questions.

2. **Cross-Document QA (Global Knowledge Base):**
   - The system maintains a unified ChromaDB collection (`global_collection`) and a global NetworkX graph (`global_graph`).
   - The UI's Sidebar features a "Global Knowledge Base" mode. Selecting it allows users to search across *all* uploaded documents simultaneously!

3. **Explainability Mode:**
   - The LLM generates inline citations for every factual claim.
   - The ChatPanel includes a collapsible "Sources Used" accordion. Clicking this expands a list of `SourceCard` components displaying the exact snippet, type (paragraph/table/image), and page number where the information was sourced.

4. **Real-Time Ingestion (Streaming):**
   - The `/api/upload` endpoint defers the heavy ingestion workload (MLX embedding and IBM Docling layout extraction) to FastAPI `BackgroundTasks`.
   - A Server-Sent Events (SSE) `/api/upload/stream/{doc_id}` endpoint broadcasts ingestion progress to the frontend.
   - `UploadCard.jsx` listens to the SSE stream and renders an animated progress bar, giving the user real-time feedback on extraction, graph building, and summarization phases.

---

## ✨ Latest Polish & Updates
- **Document-Specific RAG Filtering:** Chat history and retrieval now correctly filter context by `doc_id` to prevent cross-document leakage when analyzing a single document.
- **Graph Explorer Overhaul:** Replaced the chaotic BFS DAG layout with a **Sequential Wrapping Grid** layout, perfectly mapping the native document reading order and preventing disconnected sections from rendering as separate graphs.
- **Fast Document Parsing:** Migrated from `unstructured` to IBM Docling for 5-10x faster document ingestion, with excellent support for PDFs, DOCXs, PPTXs, and more.
- **UI & UX Refinements:**
  - Added beautiful center-aligned empty states for the Chat History and Graph Explorer when no documents are active.
  - Implemented an interactive "Try Again" error handling flow for failed document uploads.
  - Aligned Dropdown components and streamlined the "New Chat" button styling for a premium aesthetic.
