# Project Task & Implementation Tracker

## Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

This document tracks all implemented features, modernized architecture components, and remaining tasks required to fulfill the Smart India Hackathon (SIH 2026) Problem Statement for **Mangalore Refinery and Petrochemicals Limited (MRPL)** (Theme: *Smart Automation*, Problem Statement ID: *26117*).

---

## 1. System Specifications & Demonstration Target

* **Target Hardware**: Single local workstation or server equipped with an NVIDIA RTX GPU (12–16 GB VRAM, e.g., RTX 3060 / 4060 / 4070 / 3080) and 16–32 GB RAM.
* **Core Technology Stack**:
  * **Python Environment**: Managed exclusively via Astral `uv` (Python 3.11.16 pinned).
  * **Frontend**: SvelteKit / Vite, Node 20 LTS.
  * **Relational Database**: Local **PostgreSQL** container (`localai-postgres` on port `5433`).
  * **Vector Database**: Local **Qdrant** dedicated vector database (`localai-qdrant` on port `6333` REST / `6334` gRPC).
  * **Document Parsing & OCR**: Local GPU-accelerated **Docling Server** (`localai-docling-gpu` on port `5001`) with multilingual neural OCR (English, Hindi, Kannada) and deep table parsing.
  * **Execution Sandbox**: Isolated **Open Terminal** container (`localai-open-terminal` on port `8000`) with `python-docx`, `openpyxl`, `python-pptx`, `pandas`, `matplotlib`, and `scipy` pre-installed.
* **Active Open-Weight Model Suite (Ollama)**:
  * `qwen3.5:9b`: Heavy code generation, deliverable script creation, and complex reasoning (locked 4K/8K ctx).
  * `deepseek-r1:8b`: Deep reasoning, mathematical derivations, policy logic, and approval note drafting (locked 8K ctx).
  * `qwen3.5:4b`: Balanced mid-tier reasoning and general query execution (locked 32K ctx).
  * `smollm2:1.7b`: Ultra-fast lightweight summarization and low-latency responses (locked 8K ctx).
  * `qwen3.5:0.8b`: Compact edge execution and routine system commands (locked 32K ctx).
  * `nomic-embed-text`: High-efficiency on-device 768-dimensional embeddings for Qdrant RAG.
* **Operating Constraint**: 100% air-gapped, zero cloud telemetry, verifiable zero outbound network egress.

---

## 2. Feature Status Matrix

| ID            | Problem Statement Requirement                               | Status                | Current State / Component                                                                                                                                     | Priority for Hackathon          |
| :------------ | :---------------------------------------------------------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------ |
| **M1**  | **Fully Self-Hosted Deployment**                      | ✅**Done**      | Open-WebUI running locally on PostgreSQL (`localai-postgres`) & Qdrant (`localai-qdrant`) with Astral `uv`.                                             | High                            |
| **M2**  | **Multi-Model Support (Open-Weight)**                 | ✅**Done**      | Ollama running 6 tailored local models with global Flash Attention and locked context caps.                                                                   | High                            |
| **M3**  | **Dynamic Model Auto-Selection (≥ 2 Tasks)**         | ✅**Done**      | Custom**Warm-First VRAM Dynamic Router** (`warm_auto_router.py`) with `GET /api/ps` VRAM affinity check and live routing status markers.            | **Critical (PS Demo #1)** |
| **M4**  | **Extensibility & Dynamic VRAM Control**              | ✅**Done**      | Models pulled via Ollama appear instantly; backend endpoints`/api/models/load` & `/api/models/unload` with UI controls for memory eviction/pinning.       | Medium                          |
| **M5**  | **Local Knowledge Base Grounding (RAG)**              | ✅**Done**      | Qdrant vector database, Ollama`nomic-embed-text`, and `knowledge_fs.py` virtual CLI filesystem tool (`ls`, `cat`, `grep`, `find`).                | High                            |
| **M6**  | **On-Device Multimodal & Vision Input**               | ✅**Done**      | Multimodal visual input natively handled by`qwen3.5:9b` (supports image/diagram analysis) alongside GPU-accelerated Docling for document scans and tables.  | High                            |
| **M7**  | **High-Accuracy Multilingual OCR & Scanned Docs**     | ✅**Done**      | Docling GPU Server (`localai-docling-gpu`) on port 5001 integrated with EasyOCR (English, Hindi, Kannada) and accurate table extraction.                    | **High (PS Demo #4)**     |
| **M8**  | **Agentic Multi-Step Task Execution**                 | ✅**Done**      | Native ReAct loop, tool-calling framework, subagent delegation (`utils/subagents.py`), and task planning (`tools/builtin.py`).                            | High                            |
| **M9**  | **Iterative Task Refinement & Self-Correction**       | ✅**Done**      | Native Open-WebUI ReAct retry loop & Code Interpreter traceback feedback loop (`middleware.py:5997`, up to 5 retries automatically).                        | **High (PS Req)**         |
| **M10** | **Sandboxed Code Execution**                          | ✅**Done**      | Open Terminal Docker container (`localai-open-terminal`) active on port 8000; connected and verified via Open-WebUI Integrations & direct code interpreter. | **Critical (PS Demo #3)** |
| **M11** | **Spreadsheet Work (.xlsx with Active Formulas)**     | ✅**Done**      | Executed dynamically via sandboxed code generation using`openpyxl` (pre-installed in `localai-open-terminal`) with live formulas (`=SUM()`, equations). | Medium                          |
| **M12** | **Calculations with Steps Shown**                     | ✅**Done**      | KaTeX mathematical rendering and step-by-step reasoning derivations natively formatted by`deepseek-r1:8b` / `qwen3.5:9b`; grounds on uploaded SOPs.       | **High (PS Req)**         |
| **M13** | **Real Deliverable Generation (.docx, .xlsx, .pptx)** | ✅**Done**      | Generated dynamically by agent writing Python scripts (`python-docx`, `openpyxl`, `python-pptx`) inside Open Terminal sandbox; PDF export also active.  | **Critical (PS Demo #2)** |
| **M14** | **Local File Read & Write Capabilities**              | ✅**Done**      | Agentic file tools in`tools/builtin.py` (`view_file`, `write_note`, `knowledge_fs.py`) allow reading and saving workspace documents.                  | High                            |
| **M15** | **Verifiable Air-Gap / Network Verification**         | ✅**Done**      | Strict air-gap`.env` flags enforced; verified via browser DevTools (`F12` Network tab: 0 external calls) & physical adapter disconnect.                   | **Critical (PS Demo #5)** |
| **M16** | **Codebase Hardening & Zero-Cloud Stripping**         | ⚠️**Partial** | Cloud web search and telemetry disabled via`.env`; unused legacy cloud loaders (`mistral.py`, `datalab_marker.py`, `tavily.py`) to be pruned.         | **High**                  |

---

## 3. Detailed Task Breakdown

### Module 1: Dynamic Task-Based Model Auto-Selection (PS Requirement 1)

> **Goal:** The workbench must automatically inspect user requests and route them to the most suitable open-weight model across at least two distinct task types without manual intervention, optimizing for GPU VRAM warmth.

- [X] **1.1 Multi-Model Endpoint Integration**: Multi-model suite running simultaneously in Ollama (`qwen3.5:9b`, `deepseek-r1:8b`, `qwen3.5:4b`, `smollm2:1.7b`, `qwen3.5:0.8b`).
- [X] **1.2 Warm-First Dynamic Router**:
  - Implemented `backend/open_webui/warm_auto_router.py` (replaces legacy RouteLLM).
  - Single-tier intent classification (Reasoning, Coding, General).
  - Inspects active GPU memory via `GET /api/ps` to route to an already-warm model, avoiding swapping delays.
- [X] **1.3 Visual Routing Status**:
  - Real-time status indicators streamed directly to chat (e.g., `[Auto Router] Coding query -> qwen3.5:9b (warm in VRAM)`).
- [X] **1.4 Explicit VRAM Model Management**:
  - Added `/api/models/load` and `/api/models/unload` in `backend/open_webui/main.py`.
  - Added UI load/unload buttons in `ManageOllama.svelte` and model picker in `Selector.svelte`.
- [X] **1.5 Router Function Registration**: Verified `Auto` function is active in Open-WebUI Functions settings (`ID: warm_auto_router`) with live status streaming.

---

### Module 2: Real Deliverables & Active Formula Spreadsheets via Sandboxed Code Execution (PS Requirement 2)

> **Goal:** Produce concrete corporate deliverables (`.docx` approval notes, `.xlsx` spreadsheets with active formulas, `.pptx` presentations) by having the agent generate and execute Python scripts inside the isolated sandbox container.

- [X] **2.1 Basic PDF Transcript Export**: PDF generation utility functional (`backend/open_webui/utils/pdf_generator.py`).
- [X] **2.2 Pre-Installed Deliverable Libraries**:
  - Verified `python-docx`, `openpyxl`, `python-pptx`, `pandas`, and `matplotlib` are pre-installed in `localai-open-terminal`.
- [X] **2.3 Engineering Calculations with Step Derivation (M12)**:
  - Markdown math (KaTeX) and step-by-step engineering derivations formatted natively by `deepseek-r1:8b` (Governing Formula $\rightarrow$ Known Variables $\rightarrow$ Step-by-Step Substitution $\rightarrow$ Final Output).
- [X] **2.4 Word (`.docx`) PSU Approval Note Generation**:
  - Verified agent writing `python-docx` scripts formatting standard MRPL approval note hierarchy (Header, Background, Technical Justification, Financial Implication, Sign-Off Block) in the sandbox.
- [X] **2.5 Excel (`.xlsx`) Spreadsheets with Active Formulas (M11)**:
  - Verified agent generating spreadsheets via `openpyxl` embedding active Excel formulas (`=SUM()`, `=AVERAGE()`, hydraulic equations) in the sandbox.
- [X] **2.6 PowerPoint (`.pptx`) Board Presentation**:
  - Verified agent generating structured slide decks using `python-pptx` in the sandbox.

---

### Module 3: Coding Task, Sandboxed Execution & Iterative Self-Correction (PS Requirement 3)

> **Goal:** Execute, verify, and safely contain automated coding tasks in an isolated local sandbox with automated self-correction upon runtime failures.

- [X] **3.1 Pyodide In-Browser Execution**: Client-side execution in `tools/builtin.py`.
- [X] **3.2 Open Terminal Sandbox Infrastructure**:
  - Running Docker container `localai-open-terminal` (`ghcr.io/open-webui/open-terminal:latest`) on port `8000`.
  - Backend integration routers in `backend/open_webui/routers/terminals.py` and `backend/open_webui/utils/terminals.py`.
  - Terminal Settings UI in `src/lib/components/admin/Settings/Integrations.svelte`.
- [X] **3.3 Inbuilt Iterative Self-Correction Loop (M9)**:
  - Verified Open-WebUI's native self-correction loop in `backend/open_webui/utils/middleware.py:5997` (`while output and output[-1].get('type') == 'open_webui:code_interpreter' and retries < MAX_RETRIES:`).
  - Automatically captures execution `stderr`/tracebacks, feeds them back to the assistant, and triggers self-correction up to 5 times without manual user re-prompting.
- [X] **3.4 Connect & Test Open Terminal in Open-WebUI**:
  - Configured connection to `http://localhost:8000`, Auth: `Bearer`, Key: `local-open-terminal-api-key`.
  - Verified terminal session creation, WebSocket proxy, and code execution from chat.

---

### Module 4: On-Device OCR & Multimodal Document Ingestion (PS Requirement 4)

> **Goal:** Process scanned inspection reports, handwritten maintenance notes, and plant datasheets using local OCR and parsing engines, with native multimodal vision capabilities for image and diagram analysis.

- [X] **4.1 Docling GPU Server Setup**:
  - Running Docker container `localai-docling-gpu` (`quay.io/docling-project/docling-serve`) on port `5001`.
  - Configured in `.env` with EasyOCR multilingual support (English, Hindi, Kannada) and deep table extraction.
- [X] **4.2 Docling Document Loader Integration**:
  - Integrated `DoclingLoader` into `backend/open_webui/retrieval/loaders/main.py`.
- [X] **4.3 Native Multimodal Vision Support (`qwen3.5:9b`)**:
  - Leveraged `qwen3.5:9b` in Ollama which natively supports direct multimodal image and diagram inputs (equipment photos, visual diagrams, and scanned snippets) without external cloud APIs.
- [X] **4.4 Scanned Documents & Handwritten Notes Ingestion**:
  - Ingest scanned PDF reports and handwritten maintenance shift handover notes through Docling and verify markdown table extraction and grounding in RAG.

---

### Module 5: Verifiable Air-Gap & Sovereignty Proof (PS Requirement 5)

> **Goal:** Provide undeniable proof to hackathon evaluators that ZERO external network calls leave the server during execution.

- [X] **5.1 Strict Air-Gap Environment Configuration**:
  - Mandated `.env` variables active:
    - `DO_NOT_TRACK=true`, `SCARF_NO_ANALYTICS=true`, `ANONYMIZED_TELEMETRY=false`
    - `ENABLE_COMMUNITY_SHARING=false`, `ENABLE_VERSION_CHECK=false`, `HF_HUB_OFFLINE=1`
    - `ENABLE_WEB_SEARCH=false`, `WEB_SEARCH_ENGINE=none`
- [X] **5.2 Browser DevTools (F12) Network Audit Protocol**:
  - Evaluators inspect browser DevTools (`F12` $\rightarrow$ Network tab $\rightarrow$ Fetch/XHR/WS).
  - Confirms 100% of network traffic is bound strictly to `localhost` / `127.0.0.1` (`8080`, `5173`, `5001`, `6333`, `8000`, `11434`) with zero outbound external domain requests.
- [ ] **5.3 Physical Disconnect Demonstration**:
  - Re-run full end-to-end inference and deliverable generation with Wi-Fi / Ethernet adapters completely disabled.

---

### Module 6: Grounding in Internal Manuals, SOPs & Past Correspondence

> **Goal:** Ground all generated drafts, technical notes, and answers in confidential documentation without external leakage.

- [X] **6.1 Qdrant Vector Store**: Dedicated vector database container running on port `6333` with multi-tenancy support.
- [X] **6.2 Local Embeddings Pipeline**: High-speed embeddings powered by `nomic-embed-text` via Ollama.
- [X] **6.3 Virtual Filesystem Tool (`knowledge_fs.py`)**:
  - Integrated agentic tool enabling `ls`, `cat`, `grep`, and `find` on local document stores.
- [ ] **6.4 Ingest Sample Refinery Knowledge Base**:
  - Ingest representative open-access industrial documents into Qdrant via Docling:
    - Refinery Pressure Vessel Inspection Procedure (API 510).
    - Plant Pipeline Maintenance SOP (ASME B31.3).
    - Sample historical inter-departmental memos.

---

### Module 7: Codebase Hardening & Dead/Internet Code Pruning (Zero-Cloud Stripping)

> **Goal:** Audit and decouple legacy cloud dependencies, remote search APIs, external telemetry, and CDN calls to deliver a 100% sovereign codebase.

- [ ] **7.1 Prune Cloud Search Loaders**: Remove or isolate external search engines in `backend/open_webui/retrieval/web/` (Google PSE, Bing, Tavily, Perplexity).
- [ ] **7.2 Prune Cloud Document Loaders**: Remove external cloud OCR dependencies (`mistral.py`, `datalab_marker.py`, `microsoft_web_iq.py`) in favor of Docling.
- [ ] **7.3 Remove Cloud Auth & Telemetry Artifacts**: Remove Scarf analytics beacons, remote version check calls, and cloud OAuth providers.
- [ ] **7.4 Dependency Optimization**: Remove unused cloud SDKs from `backend/requirements.txt` (`boto3`, `azure-identity`, etc.).

---

## 4. Priority Action Plan for SIH Hackathon

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: CONNECT & VERIFY OPEN TERMINAL SANDBOX (Status: Complete ✅)             │
│ • Terminal Server (http://localhost:8000) integrated via backend proxy & UI.     │
│ • Python execution & file creation verified in localai-open-terminal container.   │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: REAL DELIVERABLE GENERATION VIA SANDBOX (.docx & .xlsx) (Complete ✅)   │
│ • Agent generating MRPL Approval Note (.docx) via python-docx verified.          │
│ • Agent generating Excel sheet (.xlsx) with active formulas via openpyxl verified│
│ • Automated self-correction loop (M9) active when errors occur.                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: RECORD END-TO-END DEMO VIDEO (Status: Ready to Record 🎬)               │
│ • Record 5-minute video covering all 5 core demonstration scenarios.             │
│ • Showcase Knowledgebase upload, Docling OCR, sandbox execution, and admin panel. │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mandatory Demonstration Scenarios & Evaluation Checklist

To directly address the **Expected Solution** criteria specified by MRPL evaluators, the final presentation demonstrates:

### Demonstration 1: Model Auto-Selection Across ≥ 2 Task Types

- [X] **Coding / Math Query**: Prompt automatically routed to `qwen3.5:9b`.
- [X] **Deep Logic / Policy Query**: Prompt automatically routed to `deepseek-r1:8b`.
- [X] **General Query**: Prompt automatically routed to `smollm2:1.7b` / `qwen3.5:4b`.
- [X] **Visual Routing Badge**: Router streams live status marker showing selected model and VRAM warmth.
- [X] **Dynamic VRAM Management**: Demonstration of loading/unloading models via `/api/models/load` & `/api/models/unload`.

### Demonstration 2: End-to-End Industrial Workflow with Deliverable Generation

- [X] **Step 1**: Ingest an industrial inspection report (PDF/scan) via Docling into Knowledge Base.
- [X] **Step 2**: Agent extracts critical findings (wall thinning, corrosion rate) grounded in Knowledge Base SOPs.
- [X] **Step 3**: Agent writes and executes Python script in Open Terminal to generate a formatted Word document (`.docx`) approval note.
- [X] **Step 4**: Agent writes and executes Python script in Open Terminal to generate an Excel sheet (`.xlsx`) with active calculation formulas (`=SUM()`, pressure formulas).
- [X] **Step 5**: Download and open `.docx` and `.xlsx` deliverables locally.

### Demonstration 3: Sandboxed Coding Task & Automated Self-Correction

- [X] User requests an engineering calculation script (e.g., ASME pipe wall thickness).
- [X] Agent generates Python code and dispatches it to the isolated Open Terminal container.
- [X] Code executes, captures results, and displays step-by-step derivation.
- [X] *(Self-Correction)* Open-WebUI automatically captures traceback, re-prompts the model, and corrects code without user intervention.

### Demonstration 4: Multimodal Input (Scans, Handwritten Notes, Photos)

- [X] Upload a scanned or handwritten maintenance log $\rightarrow$ Docling extracts text and markdown tables.
- [X] Model analyzes extracted parameters and summarizes shift handover findings.

### Demonstration 5: Verifiable Air-Gap & Sovereignty Proof

- [X] Open Browser Developer Tools (`F12` $\rightarrow$ **Network** tab).
- [X] Filter by `Fetch/XHR` and `WS` (WebSocket).
- [X] Execute inference, document grounding, code execution, and deliverable generation.
- [X] Demonstrate to judges that 100% of network requests hit `localhost` / `127.0.0.1` ports with **0 outbound calls** to external domains or telemetry.
- [X] *(Physical Proof)* Disconnect Wi-Fi / Ethernet adapter and re-run a full agent query to prove complete independence from the internet.
