# Setting up LocalAI - A Sovereign On-Premise Agentic AI Workbench (SIH26117)

This document provides complete, step-by-step instructions to run the entire LocalAI workbench locally on Windows with zero cloud dependencies.

## 1. System Requirements & Prerequisites

### Hardware Requirements

* **GPU**: 12 GB – 16 GB VRAM recommended (e.g., NVIDIA RTX 3060 / 4060 / 4070 / 3080).
* **RAM**: Minimum 16 GB system RAM (32 GB recommended).
* **Storage**: At least 30 GB free SSD space (for OS, dependencies, and model weights).

### Installed Software

* **UV**: Fast, modern Python package, virtual environment, and runtime manager. ([Install UV](https://docs.astral.sh/uv/getting-started/installation/)). All Python versions, virtual environments, package installations, and backend executions in this workbench are powered exclusively by `uv`.
* **Python**: v3.11.16 installed and managed directly via `uv python install 3.11.16` (no manual Python installers or system PATH modifications required).
* **Node.js**: v20.20.2 (Node 20 LTS recommended, managed via `fnm`) & **npm**.
* **Git**: Installed and accessible in PATH.
* **Ollama**: Local open-weight LLM runner ([Download Ollama for Windows](https://ollama.com/download)).
* **Docker Desktop**: For running PostgreSQL, Qdrant vector database, Docling OCR, and isolated Open Terminal sandbox containers ([Download Docker Desktop](https://www.docker.com/products/docker-desktop/)).
* **PostgreSQL**: Relational database replacing SQLite for robust, concurrent persistent storage of users, chats, and configurations.
* **Qdrant**: High-performance dedicated vector search database for knowledge base embeddings and semantic retrieval.
* **Docling Server**: AI-powered document parsing and OCR engine by IBM Research for extracting clean Markdown and tables from scanned PDFs, images, and Office documents.
* **Open Terminal**: Containerized agent workspace providing isolated execution environments for Python scripts, calculations, and shell tasks.

---

## 2. Set Up & Run Local Open-Weight Models (Ollama)

Open-WebUI connects to local model runners without sending any prompt or data outside your local network.

### 2.1 Start the Ollama Service

Open a PowerShell terminal and verify Ollama is running:

```powershell
ollama serve
```

*(If Ollama is already running in your system tray, this step is handled automatically).*

### 2.2 Pull Required Open-Weight Models

Pull the recommended open-weight models aligned with MRPL problem statement tasks:

```powershell
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

### 2.3 Enable Flash Attention Globally (VRAM & Speed Optimization)

Modern NVIDIA GPUs (RTX 3000 / 4000 / 5000 series) support **Flash Attention**, an exact IO-aware tiling algorithm that dramatically reduces the memory footprint of the Key-Value (KV) cache and speeds up prompt processing by 2x–4x.

Enabling it globally ensures Ollama initializes all models with Flash Attention every time Windows starts, allowing larger context windows to fit 100% inside GPU VRAM without spilling over to CPU RAM:

```powershell
# Set OLLAMA_FLASH_ATTENTION=1 permanently in Windows User environment variables
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")
```

*(After setting this variable, right-click the Ollama icon in the Windows taskbar system tray, select **Quit Ollama**, and relaunch Ollama from the Start Menu).*

### 2.4 Lock Model Context Limits (Prevent CPU Offloading)

By default, models such as **Qwen 3.5** and **DeepSeek-R1** advertise context lengths of **262,144 (256K)** or **131,072 (128K)** tokens in their GGUF metadata. When a frontend or API client connects without explicitly restricting `num_ctx`, Ollama attempts to reserve gigabytes of VRAM for the full 256K KV cache. On 8 GB–12 GB GPUs, this forces Ollama to dump 20+ model layers onto system CPU RAM, causing generation speed to drop to a crawl.

To fix this, lock tailored default context limits into each model's local manifest using in-place Modelfiles. This takes ~1 second per model (no redownloading) and ensures that all frontends, APIs, and CLI sessions automatically inherit these context caps without needing manual configuration:

#### Recommended Context Allocation (for 8 GB – 12 GB GPUs):

| Model                | Parameters | Native GGUF Ctx | Locked Default Ctx                      | VRAM Footprint | Offload Status                                     |
| :------------------- | :--------- | :-------------- | :-------------------------------------- | :------------- | :------------------------------------------------- |
| `qwen3.5:0.8b`     | 873M       | 262,144         | **32,768 (32K)**                  | ~1.4 GB        | **100% GPU**                                 |
| `smollm2:1.7b`     | 1.7B       | 8,192           | **8,192 (8K)** / **16,384** | ~2.4 GB        | **100% GPU**                                 |
| `qwen3.5:4b`       | 4.2B       | 262,144         | **32,768 (32K)**                  | ~4.1 GB        | **100% GPU** (33/33 layers)                  |
| `deepseek-r1:8b`   | 8.2B       | 131,072         | **8,192 (8K)**                    | ~6.2 GB        | **100% GPU** (37/37 layers)                  |
| `qwen3.5:9b`       | 9.7B       | 262,144         | **4,096 (4K)** *(or 8,192)*     | ~5.5 GB        | **100% GPU** at 4K *(at 8K: 33/34 layers)* |
| `nomic-embed-text` | Embedding  | 8,192           | Default (8,192)                         | ~350 MB        | **100% GPU**                                 |

#### Run the Context Locking Script in PowerShell:

```powershell
# 1. qwen3.5:0.8b -> 32K context
@"
FROM qwen3.5:0.8b
PARAMETER num_ctx 32768
"@ | Set-Content Modelfile.tmp; ollama create qwen3.5:0.8b -f Modelfile.tmp

# 2. smollm2:1.7b -> 8K context
@"
FROM smollm2:1.7b
PARAMETER num_ctx 8192
"@ | Set-Content Modelfile.tmp; ollama create smollm2:1.7b -f Modelfile.tmp

# 3. qwen3.5:4b -> 32K context
@"
FROM qwen3.5:4b
PARAMETER num_ctx 32768
"@ | Set-Content Modelfile.tmp; ollama create qwen3.5:4b -f Modelfile.tmp

# 4. deepseek-r1:8b -> 8K context
@"
FROM deepseek-r1:8b
PARAMETER num_ctx 8192
"@ | Set-Content Modelfile.tmp; ollama create deepseek-r1:8b -f Modelfile.tmp

# 5. qwen3.5:9b -> 4K context (or 8192)
@"
FROM qwen3.5:9b
PARAMETER num_ctx 4096
"@ | Set-Content Modelfile.tmp; ollama create qwen3.5:9b -f Modelfile.tmp

# Clean up temporary Modelfile
Remove-Item Modelfile.tmp
```

### 2.5 Verify Local Models & Active Offloading

1. Verify that your models exist and have updated tags:

   ```powershell
   ollama list
   ```
2. Verify that the context limit is locked into the model parameters:

   ```powershell
   ollama show --parameters deepseek-r1:8b
   ```
3. While a model is running, monitor its VRAM usage and confirm **100% GPU** offloading:

   ```powershell
   ollama ps
   ```

---

## 3. Set Up & Launch Supporting Container Services (PostgreSQL, Qdrant, Docling OCR & Open Terminal)

All supporting infrastructure is run via lightweight Docker containers: **PostgreSQL** (relational database), **Qdrant** (vector database), **Docling** (document OCR & parsing), and **Open Terminal** (isolated code execution sandbox).

### 3.1 Option A: Launch via Docker Desktop (Recommended)

Run the following commands in PowerShell to spin up each service container:

```powershell
# 1. Launch PostgreSQL (Port 5433 mapped to container 5432, Database: localai)
# Note: For PostgreSQL 18+ (postgres:latest), the volume mount target is /var/lib/postgresql
docker run -d `
  --name localai-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=localai `
  -p 5433:5432 `
  -v pgdata:/var/lib/postgresql `
  --restart unless-stopped `
  postgres:latest

# 2. Launch Qdrant Vector DB (Port 6333 REST & 6334 gRPC)
docker run -d `
  --name localai-qdrant `
  -p 6333:6333 `
  -p 6334:6334 `
  -v qdrant_storage:/qdrant/storage `
  --restart unless-stopped `
  qdrant/qdrant:latest

# 3. Launch Docling OCR Server (Port 5001) - GPU Accelerated (NVIDIA)
docker run -d `
  --name localai-docling-gpu `
  --gpus all `
  -p 5001:5001 `
  --restart unless-stopped `
  quay.io/docling-project/docling-serve

# 4. Launch Open Terminal Code Execution Sandbox (Port 8000)
docker run -d `
  --name localai-open-terminal `
  -p 8000:8000 `
  -v open-terminal-data:/home/user `
  -e OPEN_TERMINAL_API_KEY=local-open-terminal-api-key `
  --restart unless-stopped `
  ghcr.io/open-webui/open-terminal:latest
```

### 3.2 Verify Container Service Status

Ensure all four containers are running and healthy:

```powershell
# 1. Check active Docker containers
docker ps

# 2. Verify connection to PostgreSQL container (Port 5433)
Test-NetConnection -ComputerName 127.0.0.1 -Port 5433

# 3. Verify connection to Qdrant container (Port 6333)
Test-NetConnection -ComputerName 127.0.0.1 -Port 6333

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

```powershell
# 1. Download and install Python 3.11.16
uv python install 3.11.16

# 2. Pin Python version for the repository (creates .python-version)
uv python pin 3.11.16
```

Pinning writes `.python-version` to the project root, ensuring all subsequent `uv` commands automatically use Python 3.11.16 without needing manual `--python` flags.

### 4.2 Create & Activate Python Virtual Environment

Navigate into the `backend` directory, create the virtual environment, and activate it:

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
uv venv

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1
```

> [!TIP]
> If PowerShell blocks virtual environment activation with a script execution error, run:
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
>
> and then re-run `.\.venv\Scripts\Activate.ps1`.

### 4.3 Install Backend Dependencies

Install all core backend packages using `uv pip`:

```powershell
uv pip install -r requirements.txt
```

Whenever you need to add or update dependencies, edit `backend/requirements.txt` directly and run `uv pip install -r requirements.txt`.

### 4.4 Configure Air-Gapped `.env` File

An air-gapped `.env` file is **mandatory** for this sovereign on-premise deployment. It configures PostgreSQL, Qdrant, Docling, local Ollama embeddings, disables external telemetry, and guarantees zero outbound cloud calls.

Create or update the `.env` file in the project root:

```powershell
# From the backend directory, write to the project root .env:
Set-Content -Path "..\.env" -Value @"
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
"@
```

### 4.5 Start the Backend Server

Launch the Uvicorn application server using `uv run` from within the `backend` directory:

```powershell
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

```powershell
# 1. Initialize fnm environment for current session
fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression

# 2. Install and switch to Node 20
fnm install 20
fnm use 20

# 3. Verify active version (v20.x.x)
node -v
```

*(Note: The `fnm env` initialization command must be executed in each new PowerShell session prior to running `fnm use` or invoking Node).*

### 5.2 Install Node Dependencies

```powershell
npm install
```

---

### 5.3 Running the Frontend: Choose Your Workflow

#### Workflow 1: Vite Development Server (Hot-Reload)

```powershell
npm run dev
```

* The Vite development server runs on **`http://localhost:5173`** and automatically proxies backend API calls to `http://localhost:8080`.
* Access the workbench at: **`http://localhost:5173`**

#### Workflow 2: Single-Port Production Build (Alternative / Recommended for Demo)

Instead of running two separate terminal processes for frontend and backend:

1. Build the production frontend assets:

   ```powershell
   npx vite build
   ```

   *(Bundles the Svelte UI into the `build/` directory, which the FastAPI backend is pre-configured to serve).*
2. Launch the backend server via `uv` (from the `backend/` directory):

   ```powershell
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

If you prefer running all four supporting container services (PostgreSQL, Qdrant, Docling OCR, and Open Terminal Sandbox) with a single command, you can create a `docker-compose.services.yaml` in project root and paste the following contents in it

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
    container_name: localai-docling-gpu
    ports:
      - "5001:5001"
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

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

```powershell
docker compose -f docker-compose.services.yaml up -d
```

---

## 8. Codebase Reference for Developers

| Component                                   | File Path                                                            | Purpose                                                                   |
| :------------------------------------------ | :------------------------------------------------------------------- | :------------------------------------------------------------------------ |
| **Terminal Utilities & Orchestrator** | `backend/open_webui/utils/terminals.py`                            | Detects orchestrator vs plain terminal, formats URLs, manages context IDs |
| **Terminal Routers**                  | `backend/open_webui/routers/terminals.py`                          | Proxies chat and automation terminal commands to Open Terminal backend    |
| **Terminal Settings UI**              | `src/lib/components/admin/Settings/Integrations.svelte`            | Admin panel interface for managing terminal connections                   |
| **Docling Loader**                    | `backend/open_webui/retrieval/loaders/main.py` (`DoclingLoader`) | Dispatches uploaded files to Docling REST API and extracts Markdown       |
| **PostgreSQL Engine**                 | `backend/open_webui/internal/db.py`                                | Async PostgreSQL engine using`psycopg` v3 and Alembic migrations        |
| **Qdrant Vector Client**              | `backend/open_webui/retrieval/vector/dbs/qdrant.py`                | Connects Open-WebUI knowledge base to Qdrant REST/gRPC endpoints          |
