# macOS Local Setup & Execution Guide

## Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

This document provides complete, step-by-step instructions to run the entire sovereign AI workbench locally on **macOS** (Apple Silicon M1/M2/M3/M4 or Intel) with zero cloud dependencies and hardware-accelerated local inference via Apple Metal.

---

## 1. System Requirements & Prerequisites

### Hardware Requirements

* **Processor**: Apple Silicon (M1/M2/M3/M4 Pro, Max, or Ultra recommended) or Intel Core i7/i9.
* **Unified Memory / RAM**: 
  * Minimum 16 GB Unified Memory (runs 8B/9B models comfortably).
  * 32 GB – 64 GB+ Unified Memory recommended for running larger models or multiple models concurrently.
* **Storage**: At least 30 GB free SSD space for macOS, virtual environments, and Ollama model weights.

### Installed Software

* **Homebrew**: Package manager for macOS ([https://brew.sh](https://brew.sh)).
* **Xcode Command Line Tools**: Required for compiling C/C++ extensions:
  ```bash
  xcode-select --install
  ```
* **Python**: 3.11 or 3.12 (recommended for best pre-compiled wheel compatibility):
  ```bash
  brew install python@3.11
  ```
* **Node.js**: v18.13.0 to v22.x.x (Node 20 LTS managed via `fnm`) & **npm**.
* **Git**: Pre-installed with Xcode tools or via Homebrew (`brew install git`).
* **Ollama for Mac**: Native Metal-accelerated open-weight LLM runner ([Download Ollama for macOS](https://ollama.com/download/mac)).
* **Docker Desktop for Mac** *(Optional)*: For running isolated sandboxed Jupyter kernels.

---

## 2. Step 1: Set Up & Run Local Open-Weight Models (Ollama)

Ollama runs natively on macOS and automatically leverages Apple Silicon's Unified Memory architecture and Metal GPU acceleration for fast local inference.

### 2.1 Install & Launch Ollama

1. Download and install [Ollama for Mac](https://ollama.com/download/mac), or install via Homebrew:
   ```bash
   brew install --cask ollama
   ```
2. Launch Ollama from your Applications folder or via terminal:
   ```bash
   ollama serve
   ```
   *(If Ollama is already running in your macOS menu bar, the background service is already active).*

### 2.2 Pull Required Open-Weight Models

Open a Terminal window (`zsh`) and pull the recommended open-weight models aligned with MRPL problem statement tasks:

```bash
# 1. Primary Reasoning, Coding & Analysis (9B parameter, ~6.6 GB)
ollama pull qwen3.5:9b

# 2. Deep Reasoning & Logic (Distilled Reasoning Model, 8B parameter, ~5.2 GB)
ollama pull deepseek-r1:8b

# 3. Lightweight Fast Tasks & Calculations (1.7B parameter, ~1.8 GB)
ollama pull smollm2:1.7b

# 4. Ultra-Compact Fast Reasoning & Edge Execution (0.8B parameter, ~1.0 GB)
ollama pull qwen3.5:0.8b

# Optional: Local Embedding Model (For Knowledge Base RAG via Ollama)
ollama pull nomic-embed-text
```

### 2.3 Verify Local Models

Verify that your models are installed and accessible:

```bash
ollama list
```

Expected output:
```text
NAME              ID              SIZE      MODIFIED
qwen3.5:9b        6488c96fa5fa    6.6 GB    2 days ago
qwen3.5:0.8b      f3817196d142    1.0 GB    2 days ago
smollm2:1.7b      cef4a1e09247    1.8 GB    3 days ago
deepseek-r1:8b    6995872bfe4c    5.2 GB    3 days ago
```

---

## 3. Step 2: Set Up & Run the Python Backend

The backend is built with FastAPI, SQLite, and ChromaDB.

### 3.1 Clone the Repository (If starting fresh)

```bash
cd ~/Projects
git clone https://github.com/open-webui/open-webui.git
cd open-webui
```

### 3.2 Navigate to the Backend Directory

Always navigate into the `backend` folder so Python resolves the `open_webui` module path correctly:

```bash
cd backend
```

### 3.3 Create & Activate Python Virtual Environment

```bash
# Create virtual environment inside backend/ using Python 3.11 or 3.12
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### 3.4 Install Backend Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> [!WARNING]
> Do **NOT** install `requirements-min.txt`. It is an incomplete work-in-progress Docker reference file that lacks required packages (such as `markdown`) and will cause startup crashes (`ModuleNotFoundError`). Always install from `requirements.txt`.

### 3.5 Configure Air-Gapped `.env` File (Mandatory)

An air-gapped `.env` file is **mandatory** for this sovereign on-premise deployment. It guarantees that the workbench operates in strict isolation with zero outbound network calls, disables all external telemetry, tracking, and community hub requests, sets the authentication secret key, and routes vector embeddings strictly to your local Ollama instance.

Create the `.env` file in the project root directory (`open-webui/.env`):

```bash
cat << 'EOF' > ../.env
# ==============================================================================
# SOVEREIGN ON-PREMISE AIR-GAPPED CONFIGURATION (SIH PS 26117 - MRPL)
# ==============================================================================

# --- Local LLM & Ollama Configuration ---
OLLAMA_BASE_URL=http://localhost:11434

# --- Security & Authentication ---
WEBUI_SECRET_KEY=sovereign-workbench-secret-key-mrpl
WEBUI_AUTH=true

# --- Strict Air-Gap & Telemetry Disabling ---
DO_NOT_TRACK=true
SCARF_NO_ANALYTICS=true
ANONYMIZED_TELEMETRY=false
ENABLE_COMMUNITY_SHARING=false
ENABLE_VERSION_CHECK=false
HF_HUB_OFFLINE=1

# --- Local Vector DB & Embeddings (Zero External Calls) ---
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text
RAG_OLLAMA_BASE_URL=http://localhost:11434
VECTOR_DB=chroma

# --- Sandboxed Code Execution ---
CODE_EXECUTION_ENGINE=pyodide
CODE_EXECUTION_JUPYTER_URL=http://127.0.0.1:8888

# --- Offline Document & Web Loading ---
ENABLE_WEB_SEARCH=false
WEB_SEARCH_ENGINE=none
EOF
```

### 3.6 Start the Backend Server

Start Uvicorn from inside the `backend` directory with the virtual environment activated:

```bash
python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
```

*(The backend will run database migrations in `backend/data/webui.db` and start listening on `http://0.0.0.0:8080`).*

---

## 4. Step 3: Set Up & Run the Svelte Frontend

### 4.1 Open a Second Terminal Window & Navigate to Frontend Root

Open a new terminal window or tab (`Cmd + T`) and navigate to the project root:

```bash
cd ~/Projects/open-webui
```

### 4.2 Install Fast Node Manager (`fnm`)

Open-WebUI requires Node.js `>=18.13.0 <=22.x.x` (Node 20 LTS is strongly recommended). Install `fnm` via Homebrew or the official installation script:

```bash
# Option A: Install via Homebrew (Recommended on macOS)
brew install fnm

# Option B: Install via official curl installer
curl -fsSL https://fnm.vercel.app/install | bash
```

### 4.3 Configure & Switch to Supported Node.js Version (Node 20 LTS via `fnm`)

Before running `fnm use`, initialize the `fnm` shell environment in your terminal session:

```bash
# 1. Initialize fnm environment for current session (required before running fnm use)
eval "$(fnm env --use-on-cd --shell zsh)"

# 2. Install Node 20 LTS (if not already installed)
fnm install 20

# 3. Switch to Node 20
fnm use 20

# 4. (Optional) Make fnm permanent across all future terminal windows:
echo 'eval "$(fnm env --use-on-cd --shell zsh)"' >> ~/.zshrc

# 5. Verify active version (should display v20.x.x)
node -v
```

### 4.4 Install Node Dependencies

```bash
npm install
```

> [!NOTE]
> If you are not using `fnm` and have Node.js v24+ installed globally, you can alternatively bypass the engine version check with:
> `npm install --engine-strict=false`

### 4.5 Start the Development Frontend Server

```bash
npm run dev
```

By default, the Vite development server runs on **`http://localhost:5173`** (or `http://localhost:5050`) and automatically proxies backend API requests to `http://localhost:8080`.

*(Alternatively, to create a production build bundled directly into the backend, run `npm run build`, and the backend on port 8080 will serve both the web UI and API).*

---

## 5. Step 4: Accessing & Configuring the Workbench

1. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```
2. **First-Time Admin Setup**:
   * Click **Sign Up** and create your primary account.
   * The first registered user is automatically designated as the **Local Admin**.
   * All user accounts and encrypted passwords reside strictly on-premise in `backend/data/webui.db`.
3. **Verify Model Detection**:
   * On the chat page, click the model selector in the top-left corner.
   * Verify that `qwen3.5:9b`, `deepseek-r1:8b`, `smollm2:1.7b`, and `qwen3.5:0.8b` appear in the dropdown.
4. **Verify Knowledge Base (RAG)**:
   * Go to **Workspace $\rightarrow$ Knowledge**.
   * Click `+` to create a Knowledge Base (e.g., `MRPL-Refinery-SOPs`).
   * Upload sample industrial documents (PDFs, DOCX, CSV, TXT).
   * In chat, tag `#MRPL-Refinery-SOPs` to test sovereign grounded retrieval.

---

## 6. Step 5: Setting Up Code Execution Sandbox (Optional / Advanced)

To run Python code and engineering calculations safely in an isolated sandbox:

### Option A: Pyodide (Default In-Browser Sandbox)

* Enabled out of the box in Open-WebUI via WebAssembly.
* In Open-WebUI, go to **Admin Panel $\rightarrow$ Settings $\rightarrow$ Code Execution** and ensure Engine is set to `pyodide`.

### Option B: Local Jupyter Kernel Sandbox (Recommended for Server/OS Execution)

1. In your backend virtual environment, install Jupyter Gateway:
   ```bash
   pip install jupyter jupyter_kernel_gateway
   ```
2. Launch the local Jupyter Gateway:
   ```bash
   jupyter kernelgateway --KernelGatewayApp.ip=127.0.0.1 --KernelGatewayApp.port=8888 --KernelGatewayApp.allow_origin='*'
   ```
3. In Open-WebUI **Admin Panel $\rightarrow$ Settings $\rightarrow$ Code Execution**:
   * Set **Code Execution Engine** to `jupyter`.
   * Set **Jupyter URL** to `http://127.0.0.1:8888`.

---

## 7. Quick Start Script Summary

| Component | Working Directory | Command | URL |
| :--- | :--- | :--- | :--- |
| **Ollama** | Any | `ollama serve` | `http://localhost:11434` |
| **Backend** | `open-webui/backend` | `source .venv/bin/activate && python -m uvicorn open_webui.main:app --port 8080` | `http://localhost:8080/api` |
| **Frontend** | `open-webui` | `npm run dev` | `http://localhost:5173` |

---

## 8. Common macOS Troubleshooting

* **AirPlay Receiver Port Conflict (Port 5000 / 7000)**:
  macOS uses port 5000 and 7000 for AirPlay Receiver. If Vite defaults to 5000, either specify `--port 5173`:
  ```bash
  npm run dev -- --port 5173
  ```
  Or disable AirPlay Receiver in **System Settings $\rightarrow$ General $\rightarrow$ AirDrop & AirPlay $\rightarrow$ AirPlay Receiver** (toggle OFF).
* **Port 8080 Already in Use**:
  Check what process is using port 8080:
  ```bash
  lsof -i :8080
  ```
  Pass an alternative port if needed: `--port 8081`.
* **Apple Silicon Metal Allocation / Memory Pressure**:
  On Apple Silicon, macOS dynamically allocates system unified memory to the GPU. To prevent excessive memory swapping with multiple models:
  ```bash
  # Check system unified memory usage
  top -o mem
  ```
  If memory pressure is high, unload inactive models via `ollama stop <model_name>` or use smaller variants (e.g., `smollm2:1.7b` or `qwen3.5:0.8b`).
* **Air-Gap Verification on macOS**:
  To confirm zero cloud egress, disconnect Wi-Fi / Ethernet or monitor active outbound sockets:
  ```bash
  netstat -an -f inet | grep ESTABLISHED
  ```
  Verify that all connections are strictly bound to `127.0.0.1` or local subnet addresses (`192.168.*` / `10.*`).

