# 🤖 LLM Document Validator API

A FastAPI service that validates Base64-encoded documents against user questions using **Azure OpenAI GPT-4o** for intelligent semantic analysis.

## ✨ Features

- 🔐 **Base64 Decoding** - Automatically decodes and processes Base64 content
- 📄 **Multi-format Support** - PDF, JSON, HTML, JWT, images, and plain text
- 🧠 **LLM-Powered Analysis** - Uses GPT-4o for semantic understanding
- 📊 **PDF Text Extraction** - Extracts text from PDF documents
- ✅ **Structured JSON Response** - Clean, consistent API responses

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client        │────▶│   FastAPI       │────▶│   Azure OpenAI  │
│   (Question +   │     │   Service       │     │   GPT-4o        │
│    Base64)      │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   Content       │
                        │   Extraction    │
                        │   (PDF/JSON/    │
                        │    Text)        │
                        └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
nano .env
```

**Required Environment Variables:**
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
python test_api.py
```

## 📡 API Endpoints

### POST `/validate`

Validates Base64-encoded content against a question using LLM analysis.

**Request:**
```json
{
  "question": "Does this document contain employee salary information?",
  "base64_text": "eyJlbXBsb3llZXMiOlt7Im5hbWUiOiJKb2huIiwic2FsYXJ5Ijo4NTAwMH1dfQ=="
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "reason": "The document contains employee data including salary information for multiple employees."
}
```

### GET `/health`

Returns service health status and configuration.

```json
{
  "status": "healthy",
  "pdf_support": true,
  "azure_openai_configured": true,
  "deployment": "gpt-4o"
}
```

## 📋 Supported Content Types

| Type | Detection | Processing |
|------|-----------|------------|
| **PDF** | `%PDF` magic bytes | Full text extraction via PyMuPDF |
| **JSON** | `{` or `[` prefix | Pretty-printed parsing |
| **JWT** | `eyJ` prefix | Decoded as text |
| **HTML** | `<!DOCTYPE` or `<html>` | Raw HTML text |
| **Images** | PNG/JPEG signatures | Binary detection only |
| **Text** | Default fallback | UTF-8 decoding |

## 🔧 Example Usage

### Python
```python
import requests
import base64

# Encode your content
content = '{"name": "John", "role": "Admin"}'
base64_content = base64.b64encode(content.encode()).decode()

# Make API request
response = requests.post(
    "http://localhost:8000/validate",
    json={
        "question": "Does this contain user role information?",
        "base64_text": base64_content
    }
)

print(response.json())
```

### cURL
```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Is this a configuration file?",
    "base64_text": "eyJob3N0IjogImxvY2FsaG9zdCIsICJwb3J0IjogODA4MH0="
  }'
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'Does this contain API keys?',
    base64_text: btoa('{"api_key": "sk-xxx", "secret": "abc123"}')
  })
});

const result = await response.json();
console.log(result);
```

## 🛡️ Error Handling

| Scenario | Response |
|----------|----------|
| Empty question | `valid: false`, reason explains issue |
| Invalid Base64 | `valid: false`, decoding error message |
| LLM API failure | `success: false`, API error details |
| Unrelated content | `valid: false`, LLM explains mismatch |

## 📁 Project Structure

```
document_validator_llm/
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
├── test_api.py       # Test suite
└── README.md         # Documentation
```

## 🔒 Security Notes

- Never expose `.env` file or API keys
- Use environment variables in production
- Consider rate limiting for production deployments
- Validate input size limits for Base64 content

## 📄 License

MIT License
