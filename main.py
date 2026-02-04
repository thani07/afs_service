"""
Document Validation API with Azure OpenAI LLM Integration
Validates whether Base64-encoded content is relevant to a given question using GPT-4o.
"""

import os
import base64
import json
import re
import io
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PDF Support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# ============== Configuration ==============

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Initialize Azure OpenAI Client
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION
)

# ============== FastAPI App ==============

app = FastAPI(
    title="LLM Document Validator API",
    description="Validates Base64-encoded documents against questions using Azure OpenAI GPT-4o",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Request/Response Models ==============

class ValidationRequest(BaseModel):
    question: str
    base64_text: str

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Does this document contain employee information?",
                "base64_text": "JVBERi0xLjcNCg=="
            }
        }


class ValidationResponse(BaseModel):
    success: bool
    valid: bool
    reason: str


# ============== Helper Functions ==============

def decode_base64(encoded_string: str) -> tuple[bytes, str]:
    """
    Decode Base64 string and return raw bytes and detected content type.
    """
    try:
        # Clean the base64 string (remove whitespace, newlines)
        cleaned = re.sub(r'\s+', '', encoded_string)
        decoded_bytes = base64.b64decode(cleaned)
        
        # Detect content type based on magic bytes
        content_type = detect_content_type(decoded_bytes)
        
        return decoded_bytes, content_type
    except Exception as e:
        raise ValueError(f"Failed to decode Base64: {str(e)}")


def detect_content_type(data: bytes) -> str:
    """
    Detect content type based on magic bytes/signatures.
    """
    if data.startswith(b'%PDF'):
        return 'pdf'
    elif data.startswith(b'{') or data.startswith(b'['):
        return 'json'
    elif data.startswith(b'eyJ'):
        return 'jwt'
    elif b'<!DOCTYPE html' in data[:100] or b'<html' in data[:100]:
        return 'html'
    elif data.startswith(b'\x89PNG'):
        return 'image/png'
    elif data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    elif data.startswith(b'PK'):
        return 'zip/docx/xlsx'
    else:
        return 'text'


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text content from PDF bytes.
    """
    if not PDF_SUPPORT:
        return "[PDF detected but PyMuPDF not installed - install with: pip install PyMuPDF]"
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"[Page {page_num}]\n{page_text}")
        doc.close()
        return "\n\n".join(text_parts) if text_parts else "[PDF contains no extractable text]"
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"


def extract_content(decoded_bytes: bytes, content_type: str) -> str:
    """
    Extract readable text content based on content type.
    """
    if content_type == 'pdf':
        return extract_pdf_text(decoded_bytes)
    elif content_type == 'json':
        try:
            json_data = json.loads(decoded_bytes.decode('utf-8'))
            return json.dumps(json_data, indent=2)
        except:
            return decoded_bytes.decode('utf-8', errors='ignore')
    elif content_type in ['image/png', 'image/jpeg']:
        return f"[Binary image content detected: {content_type}]"
    elif content_type == 'zip/docx/xlsx':
        return "[Office document or ZIP archive detected - binary content]"
    else:
        try:
            return decoded_bytes.decode('utf-8', errors='ignore')
        except:
            return "[Unable to decode as text]"


def validate_with_llm(question: str, extracted_content: str, content_type: str) -> dict:
    """
    Use Azure OpenAI GPT-4o to validate content against the question.
    """
    
    system_prompt = """You are an intelligent document validation engine that determines if a provided document satisfies a given question or request.

Your task:
1. Carefully read and understand what the user is asking for in their question
2. Analyze the document content to see if it provides what was requested
3. Be flexible and understanding - the document doesn't need to use exact keywords from the question
4. Focus on whether the document semantically and contextually satisfies the request

Validation Guidelines:
- If the question asks for a specific type of document (e.g., "fire inspection report"), check if the content IS that type of document
- If the question asks for evidence/proof of something (e.g., "compliance with fire code"), check if the document DEMONSTRATES that
- The document may use different terminology but still satisfy the request
- Consider the PURPOSE of the question - what information is the user trying to obtain?
- Only mark as INVALID if the document is clearly unrelated, missing critical information, or is the wrong type entirely

Response Format:
You MUST respond with ONLY valid JSON in this exact format:
{
  "valid": true or false,
  "reason": "Clear explanation of why the document does or does not satisfy the question"
}

Do not include any text before or after the JSON."""

    user_prompt = f"""Question/Request: {question}

Content Type Detected: {content_type}

Document Content:
---
{extracted_content[:12000]}
---

Determine if this document satisfies the user's question/request and respond with validation JSON."""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        llm_response = response.choices[0].message.content.strip()
        result = json.loads(llm_response)
        
        return {
            "success": True,
            "valid": result.get("valid", False),
            "reason": result.get("reason", "No reason provided by LLM")
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": True,
            "valid": False,
            "reason": f"LLM response parsing error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "valid": False,
            "reason": f"LLM API error: {str(e)}"
        }


# ============== API Endpoints ==============

@app.post("/validate", response_model=ValidationResponse)
async def validate_document(request: ValidationRequest):
    """
    Validate whether Base64-encoded content is relevant to the question using Azure OpenAI.
    """
    try:
        # Input validation
        if not request.question or not request.question.strip():
            return ValidationResponse(
                success=True,
                valid=False,
                reason="Question is empty or missing."
            )
        
        if not request.base64_text or not request.base64_text.strip():
            return ValidationResponse(
                success=True,
                valid=False,
                reason="Base64 content is empty or missing."
            )
        
        # Decode Base64
        try:
            decoded_bytes, content_type = decode_base64(request.base64_text)
        except ValueError as e:
            return ValidationResponse(
                success=True,
                valid=False,
                reason=f"Invalid Base64 encoding: {str(e)}"
            )
        
        # Extract readable content
        extracted_content = extract_content(decoded_bytes, content_type)
        
        # Check for extraction errors (but don't reject valid content that happens to start with [)
        if not extracted_content or extracted_content.strip() == "":
            return ValidationResponse(
                success=True,
                valid=False,
                reason="Content extraction failed: No readable content found."
            )
        
        # Check for actual error messages from extraction
        error_indicators = [
            "[PDF detected but PyMuPDF not installed",
            "[PDF extraction error:",
            "[Binary image content detected:",
            "[Office document or ZIP archive detected",
            "[Unable to decode as text]",
            "[PDF contains no extractable text]"
        ]
        
        for error_indicator in error_indicators:
            if extracted_content.startswith(error_indicator):
                return ValidationResponse(
                    success=True,
                    valid=False,
                    reason=f"Content extraction issue: {extracted_content}"
                )
        
        # Validate with LLM
        result = validate_with_llm(
            question=request.question,
            extracted_content=extracted_content,
            content_type=content_type
        )
        
        return ValidationResponse(**result)
        
    except Exception as e:
        return ValidationResponse(
            success=False,
            valid=False,
            reason=f"Unexpected error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint with configuration status."""
    return {
        "status": "healthy",
        "pdf_support": PDF_SUPPORT,
        "azure_openai_configured": bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY),
        "deployment": AZURE_OPENAI_DEPLOYMENT
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "LLM Document Validator",
        "version": "2.0.0",
        "endpoints": {
            "POST /validate": "Validate Base64 content against a question",
            "GET /health": "Health check"
        }
    }


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Render sets PORT env variable
    uvicorn.run(app, host="0.0.0.0", port=port)
