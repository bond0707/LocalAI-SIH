# Setting up LocalAI - A Sovereign On-Premise Agentic AI Workbench (SIH26117)

This document provides complete, step-by-step instructions to run the entire LocalAI workbench locally on macOS (Apple Silicon M-series or Intel) with zero cloud dependencies.

## 1. System Requirements & Prerequisites

### Hardware Requirements

* **Processor / GPU**: Apple Silicon (M1/M2/M3/M4 Pro, Max, or Ultra recommended with unified GPU acceleration via Apple Metal) or Intel Core i7/i9.
* **Unified Memory / RAM**: Minimum 16 GB Unified Memory (32 GB – 64 GB+ recommended for running 8B/9B models and concurrent pipelines).
* **Storage**: At least 30 GB free SSD space (for macOS, dependencies, container images, and model weights).

### Installed Software

* **Homebrew**: Package manager for macOS ([Install Homebrew](https://brew.sh)):
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
* **Xcode Command Line Tools**: Required for native compilation:
  ```bash
  xcode-select --install
  ```
* **UV**: Fast, modern Python package, virtual environment, and runtime manager. ([Install UV](https://docs.astral.sh/uv/getting-started/installation/)). All Python versions, virtual environments, package installations, and backend executions in this workbench are powered exclusively by `uv`.
  ```bash
  brew install uv
  # or: curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Python**: v3.11.16 installed and managed directly via `uv python install 3.11.16` (no manual Python installers or system PATH modifications required).
* **Node.js**: v20.20.2 (Node 20 LTS recommended, managed via `fnm`: `brew install fnm`) & **npm**.
* **Git**: Installed and accessible in PATH (`brew install git` or pre-installed via Xcode tools).
* **Ollama**: Local open-weight LLM runner with native Apple Silicon Metal acceleration ([Download Ollama for Mac](https://ollama.com/download/mac) or `brew install --cask ollama`).
* **Docker Desktop for Mac**: For running PostgreSQL, Qdrant vector database, Docling OCR, and isolated Open Terminal sandbox containers ([Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)).
* **PostgreSQL**: Relational database replacing SQLite for robust, concurrent persistent storage of users, chats, and configurations.
* **Qdrant**: High-performance dedicated vector search database for knowledge base embeddings and semantic retrieval.
* **Docling Server**: AI-powered document parsing and OCR engine by IBM Research for extracting clean Markdown and tables from scanned PDFs, images, and Office documents.
* **Open Terminal**: Containerized agent workspace providing isolated execution environments for Python scripts, calculations, and shell tasks.

---

## 2. Set Up & Run Local Open-Weight Models (Ollama)

Open-WebUI connects to local model runners without sending any prompt or data outside your local network. On macOS, Ollama natively utilizes Apple Silicon Unified Memory and the Metal performance shaders for rapid inference.

### 2.1 Start the Ollama Service

Open a Terminal window (`zsh`) and verify Ollama is running:

```bash
ollama serve
```

*(If Ollama is already running in your macOS menu bar, this step is handled automatically).*

### 2.2 Pull Required Open-Weight Models

Pull the recommended open-weight models aligned with MRPL problem statement tasks:

```bash
# 1. Primary Reasoning, Coding & Analysis (9B parameter, ~6.6 GB)
ollama pull qwen3.5:9b

# 2. Deep Reasoning & Logic (Distilled Reasoning Model, 8B parameter, ~5.2 GB)
ollama pull deepseek-r1:8b

# 3. Lightweight Fast Tasks & Calculations (1.7B parameter, ~1.8 GB)
ollama pull smollm2:1.7b

# 4. Ultra-Compact Fast Reasoning & Edge Execution (0.8B parameter, ~1.0 GB)
ollama pull qwen3.5:0.8b

# 5. Another Light-weight model for basic tasks (4B parameter, ~3.6 GB)
ollama pull hf.co/unsloth/Qwen3.5-4B-GGUF:UD-Q4_K_XL

# 6. Local Embedding Model (Required for Knowledge Base RAG & Qdrant, ~274 MB)
ollama pull nomic-embed-text
```

### 2.3 Enable Flash Attention Globally (Memory & Metal Optimization)

On Apple Silicon (M1/M2/M3/M4) and modern GPUs, **Flash Attention** is an IO-aware algorithm that significantly reduces the memory overhead of the Key-Value (KV) cache and accelerates prompt processing.

On macOS, configure the environment variable for both GUI applications (the Ollama menu bar app) and terminal sessions:

```bash
# 1. Set for GUI apps launched via Finder/menu bar
launchctl setenv OLLAMA_FLASH_ATTENTION 1

# 2. Persist in shell profile for terminal sessions (zsh)
echo 'export OLLAMA_FLASH_ATTENTION=1' >> ~/.zshrc
source ~/.zshrc
```

*(After setting this, quit the Ollama menu bar app from the macOS top status bar and relaunch Ollama).*

### 2.4 Lock Model Context Limits (Prevent Unified Memory Exhaustion & Swap)

Models such as **Qwen 3.5** and **DeepSeek-R1** advertise context lengths of **262,144 (256K)** or **131,072 (128K)** tokens in their GGUF metadata. On macOS systems with unified memory (e.g. 16 GB or 24 GB), attempting to allocate context for 262K tokens exhausts wired GPU memory, triggering heavy disk swapping and severe thermal throttling.

Locking tailored context caps into each model's local manifest ensures snappy responses and keeps memory consumption predictable across all UI clients and scripts:

#### Recommended Context Allocation (for 16 GB – 36 GB Unified Memory):

| Model | Parameters | Native GGUF Ctx | Locked Default Ctx | Memory Footprint | Offload Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `qwen3.5:0.8b` | 873M | 262,144 | **32,768 (32K)** | ~1.4 GB | **100% GPU (Metal)** |
| `smollm2:1.7b` | 1.7B | 8,192 | **8,192 (8K)** / **16,384** | ~2.4 GB | **100% GPU (Metal)** |
| `qwen3.5:4b` | 4.2B | 262,144 | **32,768 (32K)** | ~4.1 GB | **100% GPU (Metal)** |
| `deepseek-r1:8b` | 8.2B | 131,072 | **8,192 (8K)** | ~6.2 GB | **100% GPU (Metal)** |
| `qwen3.5:9b` | 9.7B | 262,144 | **4,096 (4K)** *(or 8,192)* | ~5.5 GB | **100% GPU (Metal)** |
| `nomic-embed-text` | Embedding | 8,192 | Default (8,192) | ~350 MB | **100% GPU (Metal)** |

#### Run the Context Locking Script in Terminal (`zsh` / `bash`):

```bash
# 1. qwen3.5:0.8b -> 32K context
cat << 'EOF' > Modelfile.tmp
FROM qwen3.5:0.8b
PARAMETER num_ctx 32768
EOF
ollama create qwen3.5:0.8b -f Modelfile.tmp

# 2. smollm2:1.7b -> 8K context
cat << 'EOF' > Modelfile.tmp
FROM smollm2:1.7b
PARAMETER num_ctx 8192
EOF
ollama create smollm2:1.7b -f Modelfile.tmp

# 3. qwen3.5:4b -> 32K context
cat << 'EOF' > Modelfile.tmp
FROM qwen3.5:4b
PARAMETER num_ctx 32768
EOF
ollama create qwen3.5:4b -f Modelfile.tmp

# 4. deepseek-r1:8b -> 8K context
cat << 'EOF' > Modelfile.tmp
FROM deepseek-r1:8b
PARAMETER num_ctx 8192
EOF
ollama create deepseek-r1:8b -f Modelfile.tmp

# 5. qwen3.5:9b -> 4K context (or 8192)
cat << 'EOF' > Modelfile.tmp
FROM qwen3.5:9b
PARAMETER num_ctx 4096
EOF
ollama create qwen3.5:9b -f Modelfile.tmp

# Clean up temporary Modelfile
rm Modelfile.tmp
```

### 2.5 Verify Local Models & Active Offloading

1. Verify that your models exist and have updated tags:
   ```bash
   ollama list
   ```

2. Verify that the context limit is locked into the model parameters:
   ```bash
   ollama show --parameters deepseek-r1:8b
   ```

3. While a model is running, monitor active offloading:
   ```bash
   ollama ps
   ```

---

## 3. Set Up & Launch Supporting Container Services (PostgreSQL, Qdrant, Docling OCR & Open Terminal)

All supporting infrastructure is run via lightweight Docker containers: **PostgreSQL** (relational database), **Qdrant** (vector database), **Docling** (document OCR & parsing), and **Open Terminal** (isolated code execution sandbox).

### 3.1 Option A: Launch via Docker Desktop (Recommended)

Run the following commands in your terminal (`zsh`/`bash`) to spin up each service container:

```bash
# 1. Launch PostgreSQL (Port 5433 mapped to container 5432, Database: localai)
# Note: For PostgreSQL 18+ (postgres:latest), the volume mount target is /var/lib/postgresql
docker run -d \
  --name localai-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=localai \
  -p 5433:5432 \
  -v pgdata:/var/lib/postgresql \
  --restart unless-stopped \
  postgres:latest

# 2. Launch Qdrant Vector DB (Port 6333 REST & 6334 gRPC)
docker run -d \
  --name localai-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  --restart unless-stopped \
  qdrant/qdrant:latest

# 3. Launch Docling OCR Server (Port 5001)
# Note: On macOS, Docker runs inside a virtualized Linux kernel without NVIDIA CUDA,
# so the --gpus flag is omitted. Docling utilizes multi-threaded CPU / ONNX inference.
docker run -d \
  --name localai-docling \
  -p 5001:5001 \
  --restart unless-stopped \
  quay.io/docling-project/docling-serve

# 4. Launch Open Terminal Code Execution Sandbox (Port 8000)
docker run -d \
  --name localai-open-terminal \
  -p 8000:8000 \
  -v open-terminal-data:/home/user \
  -e OPEN_TERMINAL_API_KEY=local-open-terminal-api-key \
  --restart unless-stopped \
  ghcr.io/open-webui/open-terminal:latest
```

### 3.2 Verify Container Service Status

Ensure all four containers are running and healthy:

```bash
# 1. Check active Docker containers
docker ps

# 2. Verify connection to PostgreSQL container (Port 5433)
nc -zv 127.0.0.1 5433

# 3. Verify connection to Qdrant container (Port 6333)
nc -zv 127.0.0.1 6333

# 4. Verify connection to Docling OCR container
curl http://localhost:5001/health

# 5. Verify connection to Open Terminal container
curl http://localhost:8000/api/config
```

---

## 4. Set Up & Run the Python Backend

The backend environment is managed entirely through `uv`. Dependencies are pinned directly in `backend/requirements.txt`, which acts as the single source of truth.

### 4.1 Install & Pin Python via UV

Use `uv` to download, install, and pin the exact Python version for the workspace:

```bash
# 1. Download and install Python 3.11.16
uv python install 3.11.16

# 2. Pin Python version for the repository (creates .python-version)
uv python pin 3.11.16
```

Pinning writes `.python-version` to the project root, ensuring all subsequent `uv` commands automatically use Python 3.11.16 without needing manual `--python` flags.

### 4.2 Create & Activate Python Virtual Environment

Navigate into the `backend` directory, create the virtual environment, and activate it:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
uv venv

# Activate virtual environment (macOS / Zsh / Bash)
source .venv/bin/activate
```

### 4.3 Install Backend Dependencies

Install all core backend packages using `uv pip`:

```bash
uv pip install -r requirements.txt
```

Whenever you need to add or update dependencies, edit `backend/requirements.txt` directly and run `uv pip install -r requirements.txt`.

### 4.4 Configure Air-Gapped `.env` File

An air-gapped `.env` file is **mandatory** for this sovereign on-premise deployment. It configures PostgreSQL, Qdrant, Docling, local Ollama embeddings, disables external telemetry, and guarantees zero outbound cloud calls.

Create or update the `.env` file in the project root:

```bash
# From the backend directory, write to the project root .env:
cat << 'EOF' > ../.env
# --- Local LLM & Ollama Configuration ---
OLLAMA_BASE_URL=http://localhost:11434

# --- Security & Authentication ---
WEBUI_SECRET_KEY=sovereign-workbench-secret-key-mrpl
WEBUI_AUTH=true

# --- Strict Air-Gap & Zero Telemetry ---
DO_NOT_TRACK=true
SCARF_NO_ANALYTICS=true
ANONYMIZED_TELEMETRY=false
ENABLE_COMMUNITY_SHARING=false
ENABLE_VERSION_CHECK=false
HF_HUB_OFFLINE=1

# --- PostgreSQL Relational Database ---
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/localai

# --- Qdrant Vector Database ---
VECTOR_DB=qdrant
QDRANT_URI=http://localhost:6333
ENABLE_QDRANT_MULTITENANCY_MODE=true

# --- Local Embeddings via Ollama ---
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text
RAG_OLLAMA_BASE_URL=http://localhost:11434

# --- Docling Document Content Extraction & OCR ---
CONTENT_EXTRACTION_ENGINE=docling
DOCLING_SERVER_URL=http://localhost:5001
DOCLING_API_KEY=
DOCLING_PARAMS={}

# --- Offline Mode ---
ENABLE_WEB_SEARCH=false
WEB_SEARCH_ENGINE=none
EOF
```

### 4.5 Start the Backend Server

Launch the Uvicorn application server using `uv run` from within the `backend` directory:

```bash
uv run uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
```

*(On initial startup, Open-WebUI automatically initializes database schemas and tables in PostgreSQL under database `localai` and registers collections in Qdrant).*

---

## 5. Set Up & Run the Frontend

You can run the frontend in either of two ways:
* **Workflow 1 (Vite Dev Server)**: Recommended for active development with hot-reloading.
* **Workflow 2 (Single-Port Production Build)**: Bundles the UI into static assets served directly by the FastAPI backend at `http://localhost:8080`, requiring only one terminal process.

### 5.1 Configure Node.js in project root (Node 20 LTS via `fnm`)

Open-WebUI requires Node.js `>=18.13.0 <=22.x.x` (Node 20 LTS recommended):

```bash
# 1. Initialize fnm environment for current session
eval "$(fnm env --use-on-cd --shell zsh)"

# 2. Install and switch to Node 20
fnm install 20
fnm use 20

# 3. Verify active version (v20.x.x)
node -v
```

*(Note: The `eval "$(fnm env --use-on-cd --shell zsh)"` initialization command must be executed in each new terminal session prior to running `fnm use` or invoking Node, or added to your `~/.zshrc`).*

### 5.2 Install Node Dependencies

```bash
npm install
```

---

### 5.3 Running the Frontend: Choose Your Workflow

#### Workflow 1: Vite Development Server (Hot-Reload)

```bash
npm run dev
```

* The Vite development server runs on **`http://localhost:5173`** and automatically proxies backend API calls to `http://localhost:8080`.
* Access the workbench at: **`http://localhost:5173`**

#### Workflow 2: Single-Port Production Build (Alternative / Recommended for Demo)

Instead of running two separate terminal processes for frontend and backend:

1. Build the production frontend assets:
   ```bash
   npx vite build
   ```
   *(Bundles the Svelte UI into the `build/` directory, which the FastAPI backend is pre-configured to serve).*

2. Launch the backend server via `uv` (from the `backend/` directory):
   ```bash
   uv run uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
   ```

3. Open your browser and navigate directly to:
   ```
   http://localhost:8080
   ```
   *The backend on port 8080 serves both the application UI and all backend APIs from a single unified port.*

---

## 6. Accessing & Configuring the Workbench

1. Open your browser and navigate to:
   * **`http://localhost:8080`** (if using Single-Port Build)
   * **`http://localhost:5173`** (if using Vite Dev Server)

2. **First-Time Admin Setup**:
   * Click **Sign Up** and create the first account.
   * The first registered user is automatically designated as the **Local Admin**.
   * All user accounts, credentials, and settings are saved securely in **PostgreSQL** under the `localai` database.

3. **Verify Model Detection**:
   * On the chat page, click the model selector in the top-left corner.
   * Ensure local models (`qwen3.5:9b`, `deepseek-r1:8b`, `smollm2:1.7b`, `qwen3.5:0.8b`, `qwen3.5:4b`) appear.

4. **Connect Open Terminal Execution Sandbox**:
   * Navigate to **Admin Panel $\rightarrow$ Settings $\rightarrow$ Integrations** (or **Terminals**).
   * Under **Terminal Servers**, click **`+` (Add Connection)**:
     * **Name**: `Local Open Terminal`
     * **URL**: `http://localhost:8000`
     * **Auth Type**: `bearer`
     * **API Key**: `local-open-terminal-api-key`
   * Click **Verify**. Open-WebUI will query the endpoint and display a green success indicator detecting `terminal` / `orchestrator`.
   * Click **Save** at the bottom of the page.
   * *Chat Execution Test*: Ask the model in chat to run a Python calculation script. The script executes securely inside the `localai-open-terminal` Docker container, returning stdout and charts directly to chat without host system access.

5. **Verify Docling Content Extraction in Admin Panel**:
   * Navigate to: **Admin Panel $\rightarrow$ Settings $\rightarrow$ Documents**.
   * Verify that **Content Extraction Engine** is set to **`Docling`**.
   * Verify **Docling Server URL** is set to `http://localhost:5001`.
   * *(Optional)* Fine-tune Docling parameters as JSON:
     ```json
     {
       "ocr_engine": "easyocr",
       "table_mode": "accurate",
       "force_ocr": "true"
     }
     ```
   * Click **Save** at the bottom of the page.

6. **Verify Knowledge Base (RAG with Docling + Qdrant)**:
   * Go to **Workspace $\rightarrow$ Knowledge**.
   * Click `+` to create a Knowledge Base (e.g., `MRPL-SOPs`).
   * Upload sample industrial documents (PDFs, scans, DOCX, CSV, TXT).
   * **Pipeline execution check**:
     1. Docling receives the document and extracts OCR text & tables.
     2. Ollama (`nomic-embed-text`) calculates 768-dim embeddings.
     3. Qdrant indexes the vectors in local storage.
   * In chat, tag `#MRPL-Refinery-SOPs` to verify grounded responses.

---
## 7. Multi-Service Docker Compose Setup

If you prefer running all four supporting container services (PostgreSQL, Qdrant, Docling OCR, and Open Terminal Sandbox) with a single command, you can create a `docker-compose.services.yaml` in project root and paste the following contents in it:

```yaml
services:
  postgres:
    image: postgres:latest
    container_name: localai-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: localai
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    container_name: localai-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: unless-stopped

  docling:
    image: quay.io/docling-project/docling-serve
    container_name: localai-docling
    ports:
      - "5001:5001"
    restart: unless-stopped

  open-terminal:
    image: ghcr.io/open-webui/open-terminal:latest
    container_name: localai-open-terminal
    ports:
      - "8000:8000"
    environment:
      - OPEN_TERMINAL_API_KEY=local-open-terminal-api-key
    volumes:
      - open-terminal-data:/home/user
    restart: unless-stopped

volumes:
  pgdata:
  qdrant_storage:
  open-terminal-data:
```

After that you can just launch all services simultaneously by running the following command:
```bash
docker compose -f docker-compose.services.yaml up -d
```

---
## 8. Codebase Reference for Developers

| Component | File Path | Purpose |
| :--- | :--- | :--- |
| **Terminal Utilities & Orchestrator** | `backend/open_webui/utils/terminals.py` | Detects orchestrator vs plain terminal, formats URLs, manages context IDs |
| **Terminal Routers** | `backend/open_webui/routers/terminals.py` | Proxies chat and automation terminal commands to Open Terminal backend |
| **Terminal Settings UI** | `src/lib/components/admin/Settings/Integrations.svelte` | Admin panel interface for managing terminal connections |
| **Docling Loader** | `backend/open_webui/retrieval/loaders/main.py` (`DoclingLoader`) | Dispatches uploaded files to Docling REST API and extracts Markdown |
| **PostgreSQL Engine** | `backend/open_webui/internal/db.py` | Async PostgreSQL engine using `psycopg` v3 and Alembic migrations |
| **Qdrant Vector Client** | `backend/open_webui/retrieval/vector/dbs/qdrant.py` | Connects Open-WebUI knowledge base to Qdrant REST/gRPC endpoints |
