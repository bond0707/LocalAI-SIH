# Project Task & Implementation Tracker

## Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

This document tracks all implemented features, partially completed modules, and remaining tasks required to fulfill the Smart India Hackathon (SIH 2026) Problem Statement for **Mangalore Refinery and Petrochemicals Limited (MRPL)** (Theme: *Smart Automation*, Problem Statement ID: *26117*).

---

## 1. System Specifications & Demonstration Target

* **Target Hardware**: Single local workstation or server equipped with a mid-range GPU (e.g., NVIDIA RTX 3060 / 4060 / 4070 / 3080 with 12–16 GB VRAM, or Apple Silicon with 16–36 GB Unified Memory).
* **Model Class**: Open-weight models (7B–8B parameter tier) optimized for fast local inference and zero external dependencies:
  * `qwen2.5-coder:7b` (Code generation, scripting & math calculations)
  * `llama3.1:8b` / `deepseek-r1:8b` (General reasoning, approval note drafting & deep logic)
  * `qwen2-vl:7b` / `llava:7b` (Multimodal vision, P&IDs, scanned documents & photographs)
  * `nomic-embed-text` (Local vector embeddings for Knowledge Base RAG)
* **Operating Constraint**: 100% air-gapped, zero cloud telemetry, verifiable zero outbound network egress.

---

## 2. Feature Status Matrix


| ID      | Problem Statement Requirement                         | Status          | Current State / Component                                                                                                             | Priority for Hackathon    |
| :------ | :---------------------------------------------------- | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------ | :------------------------ |
| **M1**  | **Fully Self-Hosted Deployment**                      | ✅**Done**      | Open-WebUI running on local server/workstation with SQLite & ChromaDB.                                                                | High                      |
| **M2**  | **Multi-Model Support (Open-Weight)**                 | ✅**Done**      | Local Ollama/vLLM integration running Qwen-2.5, Llama-3.1, DeepSeek-R1, Qwen2-VL.                                                     | High                      |
| **M3**  | **Dynamic Model Auto-Selection (≥ 2 Tasks)**         | ✅**Done**      | RouteLLM Sovereign Task Router integrated with auto-classification across Coding, Vision, Reasoning, and live Visual Routing Badges.  | **Critical (PS Demo #1)** |
| **M4**  | **Extensibility (New Models on the Fly)**             | ✅**Done**      | New open-weight models pulled via Ollama appear instantly without redesigning or rebuilding the system.                               | Medium                    |
| **M5**  | **Local Knowledge Base Grounding (RAG)**              | ✅**Done**      | ChromaDB local vector DB, BM25 hybrid search, and`knowledge_fs` virtual CLI filesystem tool.                                          | High                      |
| **M6**  | **On-Device Multimodal & Vision Input**               | ✅**Done**      | Chat image upload connected to local vision LLMs (`qwen2-vl:7b`, `llava:7b`) for drawings and photos.                                 | High                      |
| **M7**  | **On-Device OCR (Scanned PDFs & Handwritten Notes)**  | ⚠️**Partial** | Digital PDFs handled via`PyPDFLoader`; `paddleocr_vl.py` loader integrated; needs automated fallback for scanned/handwritten bitmaps. | **High (PS Demo #4)**     |
| **M8**  | **Engineering Drawings & P&ID Processing**            | ⚠️**Partial** | Vision models accept diagrams; needs specialized prompt templates for P&ID tag, valve, and line symbol extraction.                    | Medium                    |
| **M9**  | **Agentic Multi-Step Task Execution**                 | ✅**Done**      | Native ReAct loop, tool-calling framework, subagent delegation (`utils/subagents.py`), and task planning (`tools/builtin.py`).        | High                      |
| **M10** | **Iterative Task Refinement & Self-Correction**       | ⚠️**Partial** | Interactive chat editing works; needs automated closed-loop code self-correction upon sandbox execution error.                        | **High (PS Req)**         |
| **M11** | **Sandboxed Code Execution**                          | ⚠️**Partial** | In-browser Pyodide sandbox functional; local Jupyter Kernel Gateway connector (`utils/code_interpreter.py`) needs hookup.             | **Critical (PS Demo #3)** |
| **M12** | **Spreadsheet Work (.xlsx with Active Formulas)**     | ⚠️**Partial** | Tabular markdown and CSV display work; automated`.xlsx` generator with live mathematical formulas needed.                             | Medium                    |
| **M13** | **Calculations with Steps Shown**                     | ⚠️**Partial** | Markdown math rendering (KaTeX) works; needs structured engineering calculation templates showing full intermediate steps.            | **High (PS Req)**         |
| **M14** | **Real Deliverable Generation (.docx, .xlsx, .pptx)** | ❌**Remaining** | PDF transcript export exists; formal PSU Word (`.docx`) approval note builder and PowerPoint (`.pptx`) deck tools needed.             | **Critical (PS Demo #2)** |
| **M15** | **Local File Read & Write Capabilities**              | ✅**Done**      | Agentic file tools in`tools/builtin.py` (`view_file`, `write_note`, `knowledge_fs`) allow reading and saving workspace documents.     | High                      |
| **M16** | **Verifiable Air-Gap / Network Monitor**              | ❌**Remaining** | Air-gap`.env` flags enforced; needs visual real-time network traffic audit badge proving 0 outbound packets to judges.                | **Critical (PS Demo #5)** |
| **M17** | **Codebase Hardening & Zero-Cloud Stripping**         | ❌**Remaining** | Strip external search loaders, cloud OAuth, Gravatar, Scarf analytics, and prune unused cloud dependencies.                           | **High**                  |

---

## 3. Detailed Task Breakdown

### Module 1: Dynamic Task-Based Model Auto-Selection (PS Requirement 1)

> **Goal:** The workbench must automatically inspect user requests and route them to the most suitable open-weight model across at least two distinct task types without requiring manual model selection.

- [X]  **1.1** Support multiple open-weight LLM endpoints simultaneously via Ollama.
- [X]  **1.2 Use RouteLLM to implement the functionality** (Integrated `SovereignTaskRouter` into RouteLLM with on-premise classification & fallbacks).
- [X]  **1.3 Add Visual Routing Badge:** Display which model was chosen and the reason (e.g., *"Auto-routed to Qwen-3.5"* / *"Auto-routed to DeepSeek-R1"* with task category and confidence).

---

### Module 2: Real Deliverables & Calculation Generator (PS Requirement 2)

> **Goal:** The system must produce concrete corporate deliverables (`.docx` approval notes, `.xlsx` spreadsheets, `.pptx` presentations) and transparent engineering calculations with step-by-step derivations—not merely chat replies.

- [X]  **2.1** Basic chat transcript export to PDF ([`pdf_generator.py`](backend/open_webui/utils/pdf_generator.py)).
- [ ]  **2.2 Word (`.docx`) Approval Note Builder:**
  - Create a custom Tool (`backend/open_webui/tools/approval_note_generator.py`) using `python-docx`.
  - Format output using standard PSU / MRPL approval note hierarchy:
    - Header: Note No., Department, Date, Subject, Initiator
    - Section 1: Executive Summary & Background
    - Section 2: Technical Justification & Reference Standards (e.g., API 510, OISD)
    - Section 3: Financial & Procurement Implications
    - Section 4: Specific Recommendation & Sign-Off Approval Block
  - Render an inline download card with a one-click `.docx` download button.
- [ ]  **2.3 Excel (`.xlsx`) Spreadsheet Generator with Active Formulas:**
  - Create a custom Tool (`backend/open_webui/tools/excel_generator.py`) using `openpyxl`.
  - Output tables with live Excel formulas (`=SUM()`, `=AVERAGE()`, pressure/flow loss equations) rather than static numerical values.
- [ ]  **2.4 Board Presentation (`.pptx`) Generator:**
  - Create a custom Tool (`backend/open_webui/tools/pptx_generator.py`) using `python-pptx` to generate executive summary slide decks for board/management reviews.
- [ ]  **2.5 Engineering Calculations with Steps Shown:**
  - Standardize prompt format for engineering calculations (e.g., pipe minimum wall thickness per ASME B31.3, relief valve sizing per API 520).
  - Explicitly display: Governing Formula $\rightarrow$ Known Variables with Units $\rightarrow$ Intermediate Substitution Steps $\rightarrow$ Final Calculated Value $\rightarrow$ Safety Factor Check.

---

### Module 3: Coding Task, Sandboxed Execution & Iterative Self-Correction (PS Requirement 3)

> **Goal:** Demonstrate an automated coding task executed, verified, and safely contained in a local sandbox with iterative self-correction.

- [X]  **3.1** In-browser Pyodide execution ([`tools/builtin.py`](backend/open_webui/tools/builtin.py#L621-L711)).
- [X]  **3.2** Jupyter Kernel client connector ([`utils/code_interpreter.py`](backend/open_webui/utils/code_interpreter.py)).
- [ ]  **3.3 Configure & Test Local Jupyter Kernel Gateway:**
  - Start local Jupyter Kernel Gateway on `http://127.0.0.1:8888`.
  - Configure `code_interpreter.engine = 'jupyter'` in Open-WebUI settings.
  - Verify execution of calculations (e.g., Reynolds number, hydraulic pressure drops) capturing stdout, stderr, and plots.
- [ ]  **3.4 Iterative Self-Correction Loop:**
  - Verify that when generated code produces a runtime error or syntax error in the sandbox, the agent automatically intercepts the traceback, refines the script, and re-executes until success.

---

### Module 4: On-Device OCR & Multimodal Understanding (PS Requirement 4)

> **Goal:** Process scanned inspection reports, handwritten maintenance notes, engineering drawings (P&IDs), and plant photographs using local vision and OCR models.

- [X]  **4.1** Multimodal image upload connected to local vision LLMs (`qwen2-vl:7b`, `llava:7b`).
- [X]  **4.2** Text extraction from clean, digital PDFs ([`retrieval/loaders/main.py`](backend/open_webui/retrieval/loaders/main.py)).
- [X]  **4.3** `paddleocr_vl.py` loader integrated into the retrieval loader pipeline.
- [ ]  **4.4 Automatic Fallback for Scanned Bitmaps & Handwritten Notes:**
  - Enable automatic fallback to local OCR / Vision when a PDF contains rasterized scans with zero extractable text.
  - Test handwriting recognition on simulated shift handover notes and equipment inspection tags.
- [ ]  **4.5 P&ID & Engineering Drawing Analysis:**
  - Provide specialized prompts for interpreting Piping & Instrumentation Diagrams:
    - Extract valve numbers, line sizes, instrument tags (e.g., `PT-101`, `FCV-204`), and flow direction.

---

### Module 5: Verifiable Air-Gap & Sovereignty Proof (PS Requirement 5)

> **Goal:** Provide undeniable proof to hackathon evaluators that ZERO external network calls leave the server during execution.

- [X]  **5.1** Strict air-gap environment variables configured in mandatory `.env`:
  - `DO_NOT_TRACK=true`, `SCARF_NO_ANALYTICS=true`, `ANONYMIZED_TELEMETRY=false`
  - `ENABLE_COMMUNITY_SHARING=false`, `ENABLE_VERSION_CHECK=false`, `HF_HUB_OFFLINE=1`
  - `ENABLE_WEB_SEARCH=false`, `WEB_SEARCH_ENGINE=none`
- [ ]  **5.2 Live Network Traffic Monitor Widget:**
  - Build a backend audit endpoint (`/api/v1/network/audit`) polling local socket connections.
  - Add a visible UI badge on the top navigation bar:
    - Green Shield: *"Sovereign Air-Gap: 0 Outbound Packets"*.
    - Interactive modal showing real-time socket connections bound strictly to `127.0.0.1` / local subnet.
- [ ]  **5.3 Physical Disconnect Demonstration:**
  - Prepare a demonstration proving full platform functionality with Wi-Fi / Ethernet adapters completely disabled.

---

### Module 6: Grounding in Internal Manuals, SOPs & Past Correspondence

> **Goal:** Ground all generated drafts, technical notes, and answers in the organization's confidential documentation without external leakage.

- [X]  **6.1** ChromaDB local vector store configured for on-premise embeddings.
- [X]  **6.2** Knowledge Base UI supporting document collections, auto-chunking, and `#` tag retrieval.
- [X]  **6.3** `knowledge_fs.py` virtual filesystem tool ([`tools/knowledge_fs.py`](backend/open_webui/tools/knowledge_fs.py)) allowing agents to run `ls`, `cat`, `grep`, and `find` on internal document repositories.
- [ ]  **6.4 Curate Sample Industrial Knowledge Base:**
  - Ingest representative open-access industrial documents:
    - Refinery Pressure Vessel Inspection Procedure (aligned with API 510)
    - Plant Pipeline Maintenance SOP
    - Sample historical inter-departmental correspondence / memos

---

### Module 7: Codebase Hardening & Dead/Internet Code Pruning (Zero-Cloud Stripping)

> **Goal:** Audit, decouple, and strip all cloud dependencies, remote search APIs, external telemetry, and CDN calls to deliver a clean, 100% self-contained codebase.

- [ ]  **7.1 Strip Cloud Search Engines:** Disable/prune external search APIs (Google PSE, Bing, Brave, Tavily, Perplexity, Firecrawl) in `backend/open_webui/retrieval/web/`.
- [ ]  **7.2 Strip Cloud Document Loaders:** Remove external cloud OCR/parsing dependencies (`mistral.py` cloud OCR, `microsoft_web_iq.py`, `datalab_marker.py`) in `backend/open_webui/retrieval/loaders/`.
- [ ]  **7.3 Remove Remote Telemetry & Hub Integration:** Remove Scarf analytics beacons, remote version pings (`api.openwebui.com`), and Community Hub sharing buttons.
- [ ]  **7.4 Strip Cloud Auth & External SaaS:** Disable cloud OAuth providers (Google OAuth, Azure AD, Okta, SCIM cloud sync) in favor of strictly local authentication.
- [ ]  **7.5 Localize Frontend Assets & Avatars:** Replace external Gravatar calls with local SVG avatars; serve fonts and icons entirely from local static bundles.
- [ ]  **7.6 Dependency Pruning:** Clean unused cloud SDK packages (`azure-identity`, `boto3`, etc.) from `requirements.txt` and unused packages from `package.json`.

---

## 4. Priority Action Plan for SIH Hackathon

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DYNAMIC MODEL AUTO-ROUTER (Est: 2 hrs)                        │
│ • Write Open-WebUI Pipe Function for task-based model selection.       │
│ • Auto-route: Coding -> Qwen-Coder | Vision -> Qwen-VL | Notes -> Llama│
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: REAL DELIVERABLE & CALCULATION GENERATORS (Est: 3-4 hrs)      │
│ • Create python-docx Tool for formatted MRPL Approval Notes (.docx).   │
│ • Create openpyxl Tool for calculation sheets (.xlsx) with formulas.   │
│ • Standardize step-by-step engineering calculation formatting.         │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: VERIFIABLE AIR-GAP AUDIT MONITOR (Est: 1-2 hrs)               │
│ • Implement backend network connection auditor (0 external packets).   │
│ • Display "Sovereignty Verified: Air-Gapped" live badge on UI header.  │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: EXECUTE & VALIDATE 5 MANDATORY EVALUATION SCENARIOS (Est: 2h) │
│ • Run and record all 5 evaluation demonstrations defined in Section 5. │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mandatory Demonstration Scenarios & Evaluation Checklist

To directly address the **Expected Solution** criteria specified by MRPL evaluators, the final presentation must demonstrate:

### Demonstration 1: Model Auto-Selection Across ≥ 2 Task Types

- [X]  Enter a coding/calculation prompt $\rightarrow$ Workbench automatically assigns `qwen2.5-coder:7b` (or available `qwen3.5:9b`).
- [X]  Enter an inspection/drawing prompt $\rightarrow$ Workbench automatically assigns `qwen2-vl:7b` (or available vision/multimodal fallback).
- [X]  Enter a policy/approval prompt $\rightarrow$ Workbench automatically assigns `deepseek-r1:8b` (or `llama3.1:8b`).
- [X]  Verify visual routing badge displays chosen model and reasoning.

### Demonstration 2: End-to-End 5-Step Industrial Workflow

- [ ]  **Step 1**: Ingest a scanned industrial inspection report (PDF/image).
- [ ]  **Step 2**: Agent extracts critical inspection findings (e.g., wall thinning, corrosion rate, crack depth).
- [ ]  **Step 3**: Ground findings against internal SOPs/standards in ChromaDB knowledge base.
- [ ]  **Step 4**: Agent drafts a formal PSU approval note with technical justification and recommendation.
- [ ]  **Step 5**: Workbench exports a formatted Word document (`.docx`) available for instant local download.

### Demonstration 3: Sandboxed Coding Task & Self-Correction

- [ ]  User requests an engineering calculation script (e.g., ASME pipe wall thickness or heat exchanger duty).
- [ ]  Agent generates Python code and dispatches it to the isolated sandbox (Pyodide / Jupyter).
- [ ]  Code executes, captures results, and displays step-by-step calculation output.
- [ ]  *(Self-Correction)* Inject intentional code error $\rightarrow$ verify agent reads traceback, repairs code, and successfully completes execution.

### Demonstration 4: Multimodal Input (Drawings, Scans, Handwritten Notes, Photos)

- [ ]  Upload an engineering drawing (P&ID schematic) $\rightarrow$ Model identifies line numbers, tags, and valves.
- [ ]  Upload a scanned or handwritten maintenance log $\rightarrow$ OCR extracts text and parameters.
- [ ]  Upload a plant photograph (e.g., pipe corrosion) $\rightarrow$ Model assesses visual defects.

### Demonstration 5: Verifiable Air-Gap & Sovereignty Proof

- [ ]  Open the live Network Traffic Monitor widget on screen.
- [ ]  Execute inference, document grounding, and deliverable generation.
- [ ]  Verify that 100% of network traffic remains bound to `127.0.0.1` / local subnet with **0 outbound packets** to public IP addresses.
- [ ]  *(Optional)* Disconnect physical network adapter and re-run a full agent query to prove complete independence from the internet.
