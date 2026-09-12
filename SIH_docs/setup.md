# Local Setup & Execution Guide

## Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

This document provides complete, step-by-step instructions to run the entire sovereign AI workbench locally on Windows/Linux with zero cloud dependencies.

---

## 1. System Requirements & Prerequisites

### Hardware Requirements

* **GPU**: 12 GB – 16 GB VRAM recommended (e.g., NVIDIA RTX 3060 / 4060 / 4070 / 3080).
* **RAM**: Minimum 16 GB system RAM (32 GB recommended).
* **Storage**: At least 30 GB free SSD space (for OS, dependencies, and model weights).

### Installed Software

* **Python**: 3.11, 3.12, or 3.13 (Python 3.11/3.12 recommended for best pre-built wheel compatibility).
* **Node.js**: v18.13.0 to v22.x.x (Node 20 LTS recommended, managed via `fnm`) & **npm**.
* **Git**: Installed and accessible in PATH.
* **Ollama**: Local open-weight LLM runner ([Download Ollama for Windows](https://ollama.com/download)).
* **Docker Desktop** *(Optional but recommended)*: For running isolated Jupyter kernels and containerized OCR engines.

---

## 2. Step 1: Set Up & Run Local Open-Weight Models (Ollama)

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
# 1. Coding, Sandboxed Execution & Calculations (7B parameter)
ollama pull qwen2.5-coder:7b

# 2. General Reasoning, Approval Notes & Document Summaries (8B parameter)
ollama pull llama3.1:8b

# 3. Deep Reasoning & Logic (Distilled Reasoning Model)
ollama pull deepseek-r1:8b

# 4. Multimodal Vision (For P&ID drawings, inspection photos & charts)
ollama pull qwen2-vl:7b
# (Alternative vision model: ollama pull llava:7b)

# 5. Local Embedding Model (For Knowledge Base RAG)
ollama pull nomic-embed-text
```

### 2.3 Verify Local Models

Check that your models are available:

```powershell
ollama list
```

---

## 3. Step 2: Set Up & Run the Python Backend

The backend is built with FastAPI, SQLite, and ChromaDB.

### 3.1 Clone the Repository (If starting fresh)

```powershell
cd "d:\Me\Projects\Timepass Projects\SIH 2026"
git clone https://github.com/open-webui/open-webui.git
```

### 3.2 Navigate to the Backend Directory

Always navigate into the `backend` folder so Python can resolve the `open_webui` module:

```powershell
cd "d:\Me\Projects\Timepass Projects\SIH 2026\open-webui\backend"
```

### 3.3 Create & Activate Python Virtual Environment

```powershell
# Create virtual environment inside backend/
python -m venv .venv

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1
```

> **Note for Windows users**: If PowerShell blocks script activation with an `ExecutionPolicy` error, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 3.4 Install Backend Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt

# If using Python 3.13 (where standard audioop was removed):
pip install audioop-lts
```

> [!WARNING]
> Do **NOT** install `requirements-min.txt`. It is an incomplete work-in-progress Docker reference file that lacks required packages (such as `markdown`) and will cause startup crashes (`ModuleNotFoundError`). Always install from `requirements.txt`.

### 3.5 Configure Air-Gapped `.env` File (Mandatory)

An air-gapped `.env` file is **mandatory** for this sovereign on-premise deployment. It guarantees that the system operates in strict isolation with zero outbound network calls, disables all telemetry, tracking, and community hub requests, sets the authentication secret key, and routes vector embeddings strictly to your local Ollama instance.

Create the `.env` file in the root directory:

```powershell
# In PowerShell:
Set-Content -Path "..\.env" -Value @"
OLLAMA_BASE_URL=http://localhost:11434
WEBUI_SECRET_KEY=sovereign-workbench-secret-key-mrpl
WEBUI_AUTH=true
DO_NOT_TRACK=true
SCARF_NO_ANALYTICS=true
ANONYMIZED_TELEMETRY=false
ENABLE_COMMUNITY_SHARING=false
ENABLE_VERSION_CHECK=false
HF_HUB_OFFLINE=1
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text
RAG_OLLAMA_BASE_URL=http://localhost:11434
VECTOR_DB=chroma
CODE_EXECUTION_ENGINE=pyodide
ENABLE_WEB_SEARCH=false
WEB_SEARCH_ENGINE=none
"@
```

### 3.6 Start the Backend Server

Run Uvicorn from inside the `open-webui\backend` directory:

```powershell
python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
```

> [!TIP]
> Avoid passing unquoted wildcards like `--forwarded-allow-ips '*'` on Windows, as Windows shells expand `*` into directory file names.

*(The backend will initialize the database schema in `open-webui/backend/data/webui.db` and start listening on port `8080`).*

---

## 4. Step 3: Set Up & Run the Svelte Frontend

### 4.1 Open a Second PowerShell Terminal & Navigate to Frontend Root

```powershell
cd "d:\Me\Projects\Timepass Projects\SIH 2026\open-webui"
```

### 4.2 Install Fast Node Manager (`fnm`)

Open-WebUI specifies Node.js `>=18.13.0 <=22.x.x` (Node 20 LTS is strongly recommended). Install `fnm` to easily install and switch Node.js versions:

```powershell
# Install Fast Node Manager (fnm) via Windows Package Manager
winget install Schniz.fnm
```

> [!TIP]
> After installing `fnm`, restart your PowerShell terminal so that `fnm` is available in your PATH. If `winget` is unavailable, you can also download `fnm` from [Schniz/fnm releases](https://github.com/Schniz/fnm/releases).

### 4.3 Configure & Switch to Supported Node.js Version (Node 20 LTS via `fnm`)

Before running `fnm use`, you must initialize the `fnm` environment in your PowerShell session:

```powershell
# 1. Initialize fnm environment for current session (required before running fnm use)
fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression

# 2. Install Node 20 LTS (if not already installed)
fnm install 20

# 3. Switch to Node 20
fnm use 20

# 4. (Optional) Make fnm permanent across all future PowerShell windows:
if (!(Test-Path -Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force }
Add-Content -Path $PROFILE -Value 'fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression'

# 5. Verify active version (should be v20.x.x)
node -v
```

### 4.4 Install Node Dependencies

```powershell
npm install
```

> [!NOTE]
> If you are not using `fnm` and have Node.js v24+ installed globally, you can alternatively bypass the engine version check with:
> `npm install --engine-strict=false`

### 4.5 Start the Development Frontend Server

```powershell
npm run dev
```

By default, the Vite development server runs on **`http://localhost:5173`** (or `http://localhost:5050`) and automatically proxies backend API requests to `http://localhost:8080`.

*(Alternatively, to create a production build bundled directly into the backend, run `npm run build`, and the backend on port 8080 will serve both API and frontend).*

---

## 5. Step 4: Accessing & Configuring the Workbench

1. Open your browser and navigate to:

   ```
   http://localhost:5173
   ```
2. **First-Time Admin Setup**:

   * Click **Sign Up** and create the first account.
   * The first registered user is automatically designated as the **Local Admin**.
   * All account data is saved locally inside `backend/data/webui.db`.
3. **Verify Model Detection**:

   * On the chat page, click the model selector in the top-left corner.
   * Ensure `qwen2.5-coder:7b`, `llama3.1:8b`, `deepseek-r1:8b`, and `qwen2-vl:7b` appear in the list.
4. **Verify Knowledge Base (RAG)**:

   * Go to **Workspace $\rightarrow$ Knowledge**.
   * Click `+` to create a Knowledge Base (e.g., `MRPL-Refinery-SOPs`).
   * Upload sample industrial documents (PDFs, DOCX, CSV, TXT).
   * In chat, tag `#MRPL-Refinery-SOPs` to verify grounding.

---

## 6. Step 5: Setting Up Code Execution Sandbox (Optional / Advanced)

To run Python code and engineering calculations safely in an isolated sandbox:

### Option A: Pyodide (Default In-Browser Sandbox)

* Enabled out of the box in Open-WebUI via WebAssembly.
* Go to **Admin Panel $\rightarrow$ Settings $\rightarrow$ Code Execution** and set Engine to `pyodide`.

### Option B: Local Jupyter Kernel Sandbox (Recommended for Server/OS Execution)

1. Install Jupyter in your virtual environment:
   ```powershell
   pip install jupyter jupyter_kernel_gateway
   ```
2. Launch the local Jupyter Gateway:
   ```powershell
   jupyter kernelgateway --KernelGatewayApp.ip=127.0.0.1 --KernelGatewayApp.port=8888 --KernelGatewayApp.allow_origin='*'
   ```
3. In Open-WebUI **Admin Panel $\rightarrow$ Settings $\rightarrow$ Code Execution**:
   * Set **Code Execution Engine** to `jupyter`.
   * Set **Jupyter URL** to `http://127.0.0.1:8888`.

---

## 7. Quick Start Script Summary

| Component          | Working Directory      | Command                                                                             | URL                           |
| :----------------- | :--------------------- | :---------------------------------------------------------------------------------- | :---------------------------- |
| **Ollama**   | Any                    | `ollama serve`                                                                    | `http://localhost:11434`    |
| **Backend**  | `open-webui/backend` | `.\.venv\Scripts\Activate.ps1; python -m uvicorn open_webui.main:app --port 8080` | `http://localhost:8080/api` |
| **Frontend** | `open-webui`         | `npm run dev`                                                                     | `http://localhost:5173`     |

---

## 8. Common Troubleshooting

* **PowerShell ExecutionPolicy Error**:
  Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating `.venv`.
* **Port 8080 / 5173 Already in Use**:
  Pass alternative ports: `--port 8081` for backend, or `npm run dev -- --port 5174` for frontend.
* **Out of Memory (OOM) during Model Loading**:
  If GPU VRAM is constrained, run smaller quantized models (e.g., `qwen2.5-coder:1.5b`, `llama3.2:3b`, `qwen2-vl:2b`). Ollama automatically offloads excess layers to system RAM if VRAM is exceeded.
* **Air-Gap Verification**:
  To demonstrate zero cloud egress, disconnect your Wi-Fi/Ethernet or monitor active connections using:
  ```powershell
  Get-NetTCPConnection -State Established | Where-Object { $_.RemoteAddress -notlike "127.0.0.1" -and $_.RemoteAddress -notlike "192.168.*" }
  ```
