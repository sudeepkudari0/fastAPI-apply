# JobSpy API - FastAPI Application

A professional FastAPI application for job scraping and AI-powered CV/cover letter tailoring.

## Features

✅ **Job Scraping** - Scrape jobs from Indeed, LinkedIn, ZipRecruiter  
✅ **AI CV Tailoring** - Tailor CVs to specific job descriptions using Groq AI  
✅ **Cover Letter Generation** - Automatically generate tailored cover letters  
✅ **PDF Generation** - Professional PDF output for CVs and cover letters  
✅ **Multi-Key API Management** - Automatic failover between multiple Groq API keys  
✅ **Rate Limit Handling** - Smart cooldown and rotation for rate-limited keys  

## Project Structure

```
Fast_api_apply/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py         # API router aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py  # Health check endpoints
│   │           ├── jobs.py    # Job scraping endpoints
│   │           └── cv.py      # CV tailoring endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   ├── logging.py         # Logging setup
│   │   └── api_key_manager.py # API key management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── groq_service.py    # Groq AI service
│       ├── pdf_service.py     # PDF generation
│       └── job_service.py     # Job scraping
├── tests/
│   ├── __init__.py
│   └── test_tailor_cv.py
├── requirements.txt
├── render.yaml
├── API_KEYS_CONFIG.md
└── README.md
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Fast_api_apply
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:

```env
# Groq API Keys (comma-separated)
GROQ_API_KEYS=gsk_key1_here,gsk_key2_here,gsk_key3_here

# Optional settings (defaults shown)
# GROQ_MODEL=llama-3.3-70b-versatile
# GROQ_TIMEOUT=60.0
# GROQ_MAX_TOKENS=2000
# GROQ_TEMPERATURE=0.7
# API_KEY_COOLDOWN_MINUTES=5
# HOST=0.0.0.0
# PORT=8000
# DEBUG=False
```

## Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Using Python directly

```bash
python -m app.main
```

## API Endpoints

### Health & Status

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api-keys/status` - Check API keys status

### Job Scraping

- `POST /scrape` - Scrape job listings

**Request Body:**
```json
{
  "sites": ["indeed", "linkedin", "zip_recruiter"],
  "search_term": "developer",
  "location": "Remote",
  "results_wanted": 20,
  "hours_old": 72,
  "is_remote": true,
  "country_indeed": "USA",
  "experience_level": "entry"
}
```

### CV Tailoring

- `POST /tailor-cv` - Generate tailored CV and cover letter

**Request Body:**
```json
{
  "title": "Full Stack Developer",
  "company": "Tech Corp",
  "description": "Job description here...",
  "cv_template": "Optional custom CV template"
}
```

**Response:**
```json
{
  "success": true,
  "cv_pdf": "base64_encoded_pdf",
  "cover_letter_pdf": "base64_encoded_pdf",
  "cv_text": "Plain text CV",
  "cover_letter_text": "Plain text cover letter",
  "job_title": "Full Stack Developer",
  "company": "Tech Corp",
  "api_key_used": "gsk_abc123...",
  "attempt": 1,
  "message": "CV and Cover Letter PDFs generated successfully"
}
```

## Testing

Run the test script:

```bash
python tests/test_tailor_cv.py
```

## Deployment

### Render.com

This project is configured for deployment on Render.com. The `render.yaml` file contains the deployment configuration.

1. Connect your repository to Render
2. Set the `GROQ_API_KEYS` environment variable in Render dashboard
3. Deploy!

## Architecture

### Core Layer (`app/core/`)
- **config.py**: Centralized configuration using Pydantic settings
- **logging.py**: Logging setup and utilities
- **api_key_manager.py**: Smart API key rotation and failover

### API Layer (`app/api/`)
- **deps.py**: Dependency injection functions
- **v1/**: API version 1 endpoints
  - Organized by feature (health, jobs, cv)
  - Version-specific routing

### Services Layer (`app/services/`)
- **groq_service.py**: Business logic for AI-powered CV/cover letter generation
- **pdf_service.py**: PDF generation utilities
- **job_service.py**: Job scraping business logic

### Models Layer (`app/models/`)
- **schemas.py**: Pydantic models for request/response validation

## Benefits of This Structure

✅ **Separation of Concerns** - Each module has a single responsibility  
✅ **Testability** - Easy to unit test individual components  
✅ **Scalability** - Easy to add new endpoints and features  
✅ **Maintainability** - Clear organization makes code easy to find and update  
✅ **API Versioning** - Built-in support for multiple API versions  
✅ **Dependency Injection** - Clean dependency management  
✅ **Configuration Management** - Centralized, type-safe settings  

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GROQ_API_KEYS` | Comma-separated Groq API keys | Yes | - |
| `GROQ_MODEL` | Groq model to use | No | llama-3.3-70b-versatile |
| `GROQ_TIMEOUT` | API timeout in seconds | No | 60.0 |
| `GROQ_MAX_TOKENS` | Max tokens for AI generation | No | 2000 |
| `GROQ_TEMPERATURE` | AI temperature setting | No | 0.7 |
| `API_KEY_COOLDOWN_MINUTES` | Cooldown for failed keys | No | 5 |
| `HOST` | Server host | No | 0.0.0.0 |
| `PORT` | Server port | No | 8000 |
| `DEBUG` | Debug mode | No | False |

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.

