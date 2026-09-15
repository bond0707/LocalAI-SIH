# Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work

## Problem Statement Details

**Problem Statement ID:** 26117

**Problem Statement Number:** SIH26117

**Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)

**Department:** Mangalore Refinery and Petrochemicals Limited (MRPL)

**Category:** Software

**Theme:** Smart Automation

**Dataset Link:** Open-source models and publicly available document samples (sample scanned PDFs, sample P&IDs from open datasets) to be used for demonstration; no proprietary data required.

---

## Background

Refineries, PSUs, defence-linked manufacturing units and government offices generate a lot of routine but sensitive knowledge work. Approval notes, board presentations, engineering calculations, code for internal tools, review of scanned drawings and inspection reports.

None of this can go through cloud AI assistants like Claude or Codex because the underlying data is confidential: Piping & Instrument Diagrams, financials, vendor negotiations, unreleased designs, internal correspondence, confidential business strategies etc.

Company policy keeps this data on premises, so people either do the work manually resulting in productivity gain, or they quietly paste confidential material into public tools anyway.

Open weight large reasoning models have reached a point where a genuinely useful assistant built on them is realistic. But nothing deployable exists today that industrial users can actually work with the way they use Claude or Codex.

---

## Proposed Solution

The idea is a self-hosted, air gapped AI workbench running entirely on the organization's own GPU server. Nothing leaves the premises.

The backend should not be locked to one model. It needs to support multiple open weight models at once and automatically pick the right one for a given task based on what that task needs, a coding request handled differently from a document summary request.

New open weight models should be addable later without redesigning the system, since this space is moving fast.

The assistant also needs to actually act like an agent. Plan out multi step work, call local tools such as:

* File read and write
* Code execution in a sandbox
* Spreadsheet work
* Internal document search
* Multi-step task execution
* Iterative task refinement

It needs to handle more than text too: scanned PDFs, handwritten notes, engineering drawings, photographs, read through on device OCR and vision models.

Output should be real deliverables, including:

* Approval notes
* PPT files
* Word files
* Excel files
* Working code
* Calculations with steps shown

The system should not merely provide chat replies.

The assistant should also ground itself in the organization's own manuals, SOPs and past correspondence through a local knowledge base connector, again with nothing going external.

---

## Expected Solution

A working local deployment, demonstrable on a single workstation or server with a mid range GPU (use a smaller open weight model if 120B class hardware isn't available at the venue), that demonstrates the following:

### 1. Model Auto-Selection

Demonstrate model auto selection across at least two different task types.

The system should be capable of selecting an appropriate open-weight model based on the requirements of the task rather than relying on a single model for every operation.

### 2. End-to-End Agentic Task

Demonstrate an agentic task carried through end to end.

Example:

1. Read a scanned inspection report.
2. Extract key findings.
3. Process and interpret the relevant information.
4. Draft an approval note.
5. Generate the approval note as a Word file.

### 3. Coding Task

Demonstrate a coding task that is:

* Executed by the system.
* Run inside a sandbox.
* Verified successfully.

### 4. Multimodal Task

Demonstrate understanding of multimodal inputs, such as:

* Images
* Scanned documents
* Scanned PDFs
* Engineering drawings
* Photographs

The system should use on-device OCR and/or vision models as appropriate.

### 5. Sovereign / Air-Gapped Operation

The system must demonstrate that no external calls are made at any point.

This should be shown through:

* System logs, or
* A visible network monitor.

This is the actual proof of the sovereign claim, not just a statement of it.

---

## Key Requirements

The proposed system should therefore provide:

* Fully self-hosted deployment.
* Air-gapped operation.
* No confidential data leaving the premises.
* Support for multiple open-weight models.
* Automatic model selection based on task type.
* Ability to add new open-weight models without redesigning the system.
* Agentic multi-step task execution.
* Local file read/write capabilities.
* Sandboxed code execution.
* Spreadsheet processing.
* Local internal-document search.
* Local knowledge-base integration.
* OCR for scanned documents.
* Vision-model support for images and engineering documents.
* Support for real deliverable generation.
* Grounding against organizational manuals, SOPs and past correspondence.
* Demonstrable absence of external network calls.
* Deployment on a single workstation or server.
* Operation on a mid-range GPU for the demonstration, with smaller open-weight models permitted where 120B-class hardware is unavailable.
