# Docling OCR Setup Guide

Docling is an AI-powered document parsing engine by IBM Research that provides high-quality OCR and structure recognition for PDFs, images, Office documents, and more. Your project already has **full Docling integration** — you just need to run a Docling server and configure the connection.

---

## Architecture

```
┌────────────────────┐       HTTP POST        ┌──────────────────┐
│  Open WebUI        │  ──────────────────►   │  Docling Server  │
│  (Backend)         │  /v1/convert/file      │  (Separate)      │
│                    │  ◄──────────────────   │                  │
│  DoclingLoader     │  JSON (md_content)     │  OCR + Layout    │
└────────────────────┘                        └──────────────────┘
```

Open WebUI sends uploaded documents to the Docling server's REST API, receives parsed Markdown, and uses it for RAG retrieval.

---

## Step 1: Run the Docling Server

You have two options: **Docker** (recommended) or **pip install**.

### Option A: Docker (Recommended)

```bash
# Pull and run the official Docling server image (CPU)
docker run -d \
  --name docling-server \
  -p 5001:5001 \
  quay.io/docling-project/docling-serve-cpu
```

For **GPU-accelerated OCR** (NVIDIA GPUs):

```bash
docker run -d \
  --name docling-server \
  --gpus all \
  -p 5001:5001 \
  quay.io/docling-project/docling-serve
```

Verify it's running:

```bash
curl http://localhost:5001/health
# Should return: {"status": "ok"}
```

### Option B: pip Install

```bash
# Create a dedicated virtual environment
python -m venv docling-env
# Activate (Windows)
docling-env\Scripts\activate
# Activate (macOS/Linux)
source docling-env/bin/activate

# Install docling-serve
pip install docling-serve

# Run the server
docling-serve --host 0.0.0.0 --port 5001
```

> **Note:** The pip approach installs PyTorch and several ML models (~2-4 GB). Docker is simpler and more reproducible.

---

## Step 2: Configure in Open WebUI Admin Panel

1. **Open Admin Settings**  
   Navigate to: `Admin Panel` → `Settings` → `Documents`

2. **Set Content Extraction Engine**  
   In the **Content Extraction Engine** dropdown, select **`Docling`**

3. **Configure the fields that appear:**

   | Field | Value | Example |
   |-------|-------|---------|
   | **Docling Server URL** | The URL of your running Docling server | `http://localhost:5001` |
   | **API Key** | *(Optional)* API key if your server requires auth | Leave empty for local |
   | **Parameters** | *(Optional)* Additional Docling parameters as JSON | `{}` |

4. **Click Save** at the bottom of the settings page.

---

## Step 3: Verify the Connection

1. Upload any PDF, DOCX, PPTX, or image file to a Knowledge Base in Open WebUI
2. Check that the document gets processed without errors
3. The extracted text will appear in the document's content preview

---

## Supported Document Formats

Docling supports parsing the following formats:

| Format | Extensions | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Full OCR + layout analysis |
| Word | `.docx` | Structure preserved |
| PowerPoint | `.pptx` | Slide-by-slide extraction |
| Excel | `.xlsx` | Table extraction |
| Images | `.png`, `.jpg`, `.tiff`, `.bmp` | Pure OCR |
| HTML | `.html` | Structure preserved |
| Markdown | `.md` | Pass-through |
| AsciiDoc | `.adoc` | Structure preserved |

---

## Advanced Configuration

### Docling Parameters (JSON)

The **Parameters** field accepts a JSON object with additional form values sent to the Docling API. Examples:

```json
{
  "ocr_engine": "easyocr",
  "table_mode": "accurate",
  "force_ocr": "true"
}
```

Common parameters:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `ocr_engine` | `easyocr`, `tesseract`, `rapidocr` | OCR engine to use |
| `table_mode` | `fast`, `accurate` | Table structure detection quality |
| `force_ocr` | `true`, `false` | Force OCR even on text-based PDFs |
| `image_export_mode` | `placeholder`, `embedded`, `none` | How to handle images in output |

### Environment Variables (Alternative to UI)

You can also configure Docling via environment variables in your `.env` file or Docker setup:

```env
# In your Open WebUI .env file or Docker environment
CONTENT_EXTRACTION_ENGINE=docling
DOCLING_SERVER_URL=http://localhost:5001
DOCLING_API_KEY=           # optional
DOCLING_PARAMS={}          # optional, JSON string
```

---

## Running Docling with Docker Compose

If you want to run Docling alongside Open WebUI using Docker Compose, add a service to your `docker-compose.yaml`:

```yaml
services:
  # ... your existing open-webui service ...

  docling:
    image: quay.io/docling-project/docling-serve-cpu
    container_name: docling-server
    ports:
      - "5001:5001"
    restart: unless-stopped
    # Uncomment for GPU support (and change image to quay.io/docling-project/docling-serve):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
```

When using Docker Compose, set the Docling Server URL to use the Docker service name:
```
http://docling:5001
```

---

## Troubleshooting

### "Docling Server URL required."
- You selected `Docling` as the content extraction engine but didn't provide the server URL
- Enter the full URL including protocol and port (e.g., `http://localhost:5001`)

### "Error calling Docling API"
- Verify the server is running: `curl http://localhost:5001/health`
- Check that the URL is accessible from the Open WebUI backend (network/firewall)
- If using Docker, ensure both containers are on the same Docker network

### Connection refused
- The Docling server might not be running or is on a different port
- Check Docker logs: `docker logs docling-server`
- For pip install: check if the process is still running

### Slow processing
- Docling performs deep layout analysis and OCR, which can be CPU-intensive
- Consider using GPU acceleration for faster processing
- Large documents (50+ pages) can take several minutes on CPU

### SSL/TLS errors
- If your Docling server uses HTTPS with a self-signed certificate, you may need to configure SSL verification in the Open WebUI backend settings

---

## How Docling is Integrated in the Codebase

For developer reference, here's where Docling lives in the code:

| Component | File | Description |
|-----------|------|-------------|
| Backend Loader | `backend/open_webui/retrieval/loaders/main.py` | `DoclingLoader` class (line 238) |
| Config Mapping | `backend/open_webui/retrieval/utils.py` | Maps env vars to config keys (line 108) |
| Settings UI | `src/lib/components/admin/Settings/Documents.svelte` | Admin panel configuration form (line 677) |
