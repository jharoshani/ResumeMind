# ResumeMind — Project Summary

## What We're Building
An AI-powered resume analyzer where recruiters log in via Google, enter a Job Description (≤200 words), upload up to 10 PDF resumes, and receive ranked match scores (1%–100%) with highlighted matching skills per candidate.

## Finalized Tech Stack
| Component | Tool |
|---|---|
| Frontend | HTML5 + CSS3 + Vanilla JS (fetch API) |
| Backend | Flask (Python) |
| Authentication | Google OAuth 2.0 via Authlib |
| PDF Parsing | pdfplumber |
| AI Engine | scikit-learn (TfidfVectorizer + cosine_similarity) |
| Database | MongoDB via PyMongo |
| Secrets | python-dotenv (.env file) |
| Production Server | gunicorn |
| Deployment | Render.com (free) + MongoDB Atlas (free) |

## Core Constraints
1. Google OAuth required — unauthenticated users see only the login page
2. Job Description limited to 200 words (validated frontend + backend)
3. Maximum 10 PDF files per upload (backend enforced)
4. Each resume gets a % score AND a list of matched skills
5. All results saved to MongoDB for history

## Data Flow
```
Login → Enter JD → Upload PDFs → pdfplumber extracts text → 
scikit-learn scores each resume → Results ranked & saved to MongoDB → 
JS renders cards with progress bars + skill badges
```

## Implementation Phases
- **Phase 1:** Project setup, .env config, PyMongo connection
- **Phase 2:** Google OAuth (Authlib) + Flask session management
- **Phase 3:** PDF text extraction (pdfplumber) + input validators
- **Phase 4:** AI scoring engine (scikit-learn TF-IDF + cosine similarity)
- **Phase 5:** Flask routes, MongoDB persistence, frontend HTML/CSS/JS

## Documentation
- [HLD.md](docs/HLD.md) — Architecture, flows, components
- [LLD.md](docs/LLD.md) — Module design, functions, DB schemas
- [API.md](docs/API.md) — All 11 endpoints fully documented
