# 📄 DocuSummarize AI

**Multimodal Document Summarization Platform** — powered by Tesseract OCR, Google Gemini 2.5 Flash, Llama (via Ollama), and LangChain. Built with Streamlit. Deployed via Docker on Azure.

---

## ✨ Features

| Feature | Details |
|---|---|
| **File types** | PDF, DOCX, PNG, JPG, TIFF, BMP |
| **OCR engine** | Tesseract with multi-language support (English, Hindi, Spanish, French, German, Arabic, Chinese) |
| **LLMs** | Gemini 2.5 Flash (cloud) · Llama 3 via Ollama (local) |
| **Summary styles** | Concise · Detailed · Bullet points · Executive brief |
| **Orchestration** | LangChain PromptTemplate |
| **Deployment** | Docker · Docker Compose · Azure Container Instances |
| **CI/CD** | GitHub Actions → Azure Container Registry |

---

## 🚀 Quick Start (local, no Docker)

### 1. Install system dependencies

**macOS**
```bash
brew install tesseract poppler
```

**Ubuntu / Debian**
```bash
sudo apt-get install tesseract-ocr poppler-utils
# Extra OCR languages:
sudo apt-get install tesseract-ocr-hin tesseract-ocr-spa
```

**Windows** — Download Tesseract from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH.

### 2. Clone & install Python packages

```bash
git clone https://github.com/your-username/multimodal-summarizer.git
cd multimodal-summarizer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. (Optional) Start Ollama for Llama support

```bash
# Install Ollama from https://ollama.ai
ollama pull llama3
ollama serve
```

### 5. Run the app

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## 🐳 Docker (recommended)

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY in .env

docker compose up --build
# App: http://localhost:8501
# Ollama: http://localhost:11434

# Pull a Llama model into Ollama container:
docker exec -it docusummarize-ollama ollama pull llama3
```

---

## ☁️ Azure Deployment

### Prerequisites
- Azure CLI installed and logged in
- Azure Container Registry (ACR)
- Azure Resource Group

### Deploy

```bash
# 1. Build and push image to ACR
az acr login --name <your-acr-name>
docker build -t <your-acr>.azurecr.io/docusummarize:latest .
docker push <your-acr>.azurecr.io/docusummarize:latest

# 2. Deploy with Bicep
az deployment group create \
  --resource-group <your-resource-group> \
  --template-file azure-deploy.bicep \
  --parameters \
    containerImage=<your-acr>.azurecr.io/docusummarize:latest \
    geminiApiKey=<your-api-key>
```

### CI/CD with GitHub Actions

Add these secrets to your GitHub repository (`Settings → Secrets`):

| Secret | Value |
|---|---|
| `ACR_LOGIN_SERVER` | e.g. `myacr.azurecr.io` |
| `ACR_USERNAME` | ACR username |
| `ACR_PASSWORD` | ACR password |
| `AZURE_CREDENTIALS` | JSON from `az ad sp create-for-rbac` |
| `AZURE_RESOURCE_GROUP` | Your resource group name |
| `GEMINI_API_KEY` | Your Google API key |

Push to `main` → GitHub Actions builds, pushes, and deploys automatically.

---

## 🗂️ Project Structure

```
multimodal-summarizer/
├── app.py                        # Streamlit UI (main entry point)
├── ocr/
│   └── extractor.py              # PDF / DOCX / image text extraction
├── llm/
│   ├── gemini_client.py          # Google Gemini 2.5 Flash client
│   └── llama_client.py           # Ollama / Llama client
├── utils/
│   └── langchain_chain.py        # LangChain prompt builder
├── .streamlit/
│   └── config.toml               # Streamlit theme & settings
├── .github/
│   └── workflows/deploy.yml      # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── azure-deploy.bicep
├── requirements.txt
└── .env.example
```

---

## 🔑 Getting API Keys

### Google Gemini
1. Go to https://aistudio.google.com/
2. Click **Get API key**
3. Copy and paste into `.env` or the sidebar

### Ollama (Llama — free, local)
1. Install from https://ollama.ai
2. Run `ollama pull llama3` (or `llama3.1`, `mistral`, etc.)
3. Run `ollama serve` (starts on `http://localhost:11434`)

---

## 📖 How It Works

```
Upload (PDF/DOCX/Image)
        │
        ▼
DocumentExtractor (ocr/extractor.py)
  ├── PDF  → pdfplumber (native text) + pytesseract (fallback)
  ├── DOCX → python-docx
  └── Image→ Pillow preprocessing → pytesseract
        │
        ▼
SummarizationChain (utils/langchain_chain.py)
  └── LangChain PromptTemplate with style + language + length
        │
        ▼
   ┌────┴────┐
   │         │
Gemini    Llama
2.5 Flash  (Ollama)
   │         │
   └────┬────┘
        │
        ▼
  Summary → Streamlit UI → Download
```

---

## 📄 License

MIT
