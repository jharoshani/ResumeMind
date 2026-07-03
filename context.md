I want to build a web application for AI Resume Analysis using Flask, MongoDB (pymongo), HTML/CSS/Vanilla JS, Authlib, pdfplumber, and scikit-learn. Named ResumeMind.

Please help me build this step-by-step using a modular architecture. Here is our execution plan. Do not generate all code at once; let's tackle it phase by phase.

### Core System Requirements
1. Google OAuth via Authlib. Protect all dashboard routes.
2. Form input that takes a Job Description and enforces a strict 200-word maximum constraint.
3. Multi-file uploader accepting up to 10 PDF resumes at a time.
4. AI Scoring: Clean text from parsed PDFs using pdfplumber, eliminate English stop words, use scikit-learn's TfidfVectorizer and cosine_similarity to produce a 1% to 100% score, and extract identical vocabulary features representing matched skills.
5. Save user operations, job description logs, and scores to MongoDB via pymongo.
6. Serve a clean HTML/CSS UI and use Vanilla JS fetch requests to handle file submittal and process UI updates dynamically without page reloads.

### Implementation Phases
- Phase 1: Environment architecture setup, .env files configuration, and PyMongo initialization.
- Phase 2: Google OAuth setup using Authlib with Flask Blueprints and secure session tracking.
- Phase 3: Text processing module containing the pdfplumber engine, word validation utility, and data sanitation routines.
- Phase 4: scikit-learn NLP analytics engine development to return percentage scores and overlapping string tokens.
- Phase 5: Flask Blueprint endpoint routes, DB injection logic, and frontend HTML/CSS/JS generation.

Let's begin with Phase 1. Provide the complete project directory layout structure and the initial configuration scripts.