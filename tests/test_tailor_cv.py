"""
Test script for the /tailor-cv endpoint
Tests PDF generation for CV and Cover Letter
"""
import httpx
import asyncio
import json
import base64
from pathlib import Path

async def test_tailor_cv():
    """Test the CV tailoring endpoint with PDF generation"""
    
    base_url = "http://localhost:8000"
    
    # Test data
    request_data = {
        "title": "Senior Backend Developer",
        "company": "Tech Innovations Inc",
        "description": """
We are seeking a Senior Backend Developer with expertise in:
- Python and FastAPI
- PostgreSQL and database optimization
- RESTful API design
- Microservices architecture
- Docker and Kubernetes
- CI/CD pipelines
- Strong problem-solving skills

Requirements:
- 5+ years of backend development experience
- Expert in Python web frameworks
- Experience with cloud platforms (AWS/GCP)
- Strong understanding of software design patterns
        """
    }
    
    print("=" * 80)
    print("Testing /tailor-cv endpoint (PDF Generation)")
    print("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("\n📤 Sending request to /tailor-cv...")
            print(f"Job Title: {request_data['title']}")
            print(f"Company: {request_data['company']}\n")
            
            response = await client.post(
                f"{base_url}/tailor-cv",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"\nMessage: {result.get('message')}")
                print(f"API Key Used: {result.get('api_key_used')}")
                print(f"Attempt: {result.get('attempt')}")
                
                # Save PDFs to files
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                
                # Save CV PDF
                if result.get('cv_pdf'):
                    cv_pdf_data = base64.b64decode(result['cv_pdf'])
                    cv_filename = output_dir / f"CV_{request_data['title'].replace(' ', '_')}.pdf"
                    with open(cv_filename, 'wb') as f:
                        f.write(cv_pdf_data)
                    print(f"\n📄 CV PDF saved to: {cv_filename}")
                
                # Save Cover Letter PDF
                if result.get('cover_letter_pdf'):
                    cl_pdf_data = base64.b64decode(result['cover_letter_pdf'])
                    cl_filename = output_dir / f"CoverLetter_{request_data['title'].replace(' ', '_')}.pdf"
                    with open(cl_filename, 'wb') as f:
                        f.write(cl_pdf_data)
                    print(f"📄 Cover Letter PDF saved to: {cl_filename}")
                
                # Display text versions
                print("\n" + "=" * 80)
                print("TAILORED CV (Text Preview):")
                print("=" * 80)
                cv_text = result.get('cv_text', 'No CV text returned')
                print(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)
                
                print("\n" + "=" * 80)
                print("COVER LETTER (Text Preview):")
                print("=" * 80)
                cl_text = result.get('cover_letter_text', 'No cover letter text returned')
                print(cl_text[:500] + "..." if len(cl_text) > 500 else cl_text)
                print("=" * 80)
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
    
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Check API keys status
    print("\n" + "=" * 80)
    print("Checking API Keys Status")
    print("=" * 80)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api-keys/status")
            if response.status_code == 200:
                status = response.json()
                print(json.dumps(status, indent=2))
            else:
                print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_tailor_cv())

