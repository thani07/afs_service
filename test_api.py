"""
Test Script for LLM Document Validator API
Run the server first: uvicorn main:app --reload
Then run this script: python test_api.py
"""

import requests
import base64
import json

BASE_URL = "http://localhost:8000"


def encode_to_base64(content: str) -> str:
    """Encode string content to Base64."""
    return base64.b64encode(content.encode()).decode()


def encode_file_to_base64(file_path: str) -> str:
    """Encode a file to Base64."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def test_validation(question: str, base64_content: str, description: str):
    """Test the validation endpoint."""
    print(f"\n{'='*70}")
    print(f"📋 Test: {description}")
    print(f"❓ Question: {question}")
    print(f"📦 Base64 (first 50 chars): {base64_content[:50]}...")
    
    payload = {
        "question": question,
        "base64_text": base64_content
    }
    
    try:
        response = requests.post(f"{BASE_URL}/validate", json=payload)
        result = response.json()
        
        status_icon = "✅" if result.get("valid") else "❌"
        print(f"\n{status_icon} Result:")
        print(json.dumps(result, indent=2))
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure it's running!")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n" + "="*70)
    print("🚀 LLM Document Validator API - Test Suite")
    print("="*70)
    
    # Test 1: JSON Configuration File
    json_config = json.dumps({
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "employees_db"
        },
        "api": {
            "rate_limit": 1000,
            "timeout": 30
        }
    })
    test_validation(
        question="Does this configuration contain database connection settings?",
        base64_content=encode_to_base64(json_config),
        description="JSON Config - Database Settings"
    )
    
    # Test 2: Employee Data JSON
    employee_data = json.dumps({
        "employees": [
            {"id": 1, "name": "John Doe", "department": "Engineering", "salary": 85000},
            {"id": 2, "name": "Jane Smith", "department": "Marketing", "salary": 75000}
        ],
        "total_count": 2
    })
    test_validation(
        question="Does this document contain employee salary information?",
        base64_content=encode_to_base64(employee_data),
        description="JSON - Employee Salary Data"
    )
    
    # Test 3: Unrelated Content
    unrelated_content = """
    Welcome to our cooking blog!
    Today we'll learn how to make the perfect chocolate chip cookies.
    Ingredients: flour, sugar, butter, eggs, chocolate chips.
    """
    test_validation(
        question="Does this document contain financial quarterly reports?",
        base64_content=encode_to_base64(unrelated_content),
        description="Unrelated Content - Cooking Blog vs Financial Reports"
    )
    
    # Test 4: JWT Token
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0"
    test_validation(
        question="Is this an authentication token with admin privileges?",
        base64_content=encode_to_base64(jwt_token),
        description="JWT Token - Admin Privileges Check"
    )
    
    # Test 5: HTML Document
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Privacy Policy</title></head>
    <body>
        <h1>Privacy Policy</h1>
        <p>We collect personal data including name, email, and browsing history.</p>
        <p>Your data may be shared with third-party analytics providers.</p>
    </body>
    </html>
    """
    test_validation(
        question="Does this document describe data collection practices?",
        base64_content=encode_to_base64(html_content),
        description="HTML - Privacy Policy Data Collection"
    )
    
    # Test 6: PDF Magic Bytes (simulated header)
    # This is a partial PDF header to test PDF detection
    pdf_header = "%PDF-1.7\n%Test PDF content about sales report Q3 2024\nRevenue: $1.2M\nExpenses: $800K\nProfit: $400K"
    test_validation(
        question="Does this PDF contain sales revenue information?",
        base64_content=encode_to_base64(pdf_header),
        description="PDF Header - Sales Revenue Data"
    )
    
    # Test 7: Empty/Invalid Content
    test_validation(
        question="What information is in this document?",
        base64_content=encode_to_base64(""),
        description="Empty Content Test"
    )
    
    # Test 8: Medical Records
    medical_data = json.dumps({
        "patient": {
            "id": "P12345",
            "name": "John Doe",
            "dob": "1985-03-15"
        },
        "diagnosis": "Type 2 Diabetes",
        "medications": ["Metformin 500mg", "Lisinopril 10mg"],
        "last_visit": "2024-01-15"
    })
    test_validation(
        question="Does this contain patient medical diagnosis and medications?",
        base64_content=encode_to_base64(medical_data),
        description="JSON - Medical Records"
    )
    
    print(f"\n{'='*70}")
    print("✨ Test Suite Completed!")
    print("="*70)


if __name__ == "__main__":
    # Check health first
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"🏥 Health Check: {health.json()}")
    except:
        print("⚠️  Server not running. Start with: uvicorn main:app --reload")
        exit(1)
    
    main()
