# ResumeMind — High-Level Design (HLD)

---

## 1. System Overview

**ResumeMind** is an AI-powered resume analysis web application built for recruiters.  
A logged-in user pastes a **Job Description** (≤ 500 words), uploads up to **10 PDF resumes**, and the system returns a **1%–100% match score** along with a list of **matched skills** for each candidate — all ranked from highest to lowest.

---

## 2. Architecture Style

**Monolithic Web Application** with clean internal layering:

| Layer | Technology |
|---|---|
| Presentation | HTML5 + CSS3 + Vanilla JavaScript |
| Application | Flask (Python) |
| AI / ML | scikit-learn (TF-IDF + Cosine Similarity) |
| Persistence | MongoDB (via PyMongo) |
| Authentication | Google OAuth 2.0 (via Authlib) |

---

## 3. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER (Browser)                             │
│                      HTML + CSS + Vanilla JS                         │
│                                                                      │
│   Pages: Login | Dashboard | Results | History                       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │  HTTP/HTTPS (fetch / form submit / redirect)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION                            │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                      ROUTE LAYER                             │    │
│  │                                                              │    │
│  │  Auth Routes          Page Routes          API Routes        │    │
│  │  ─────────────        ──────────────       ──────────────    │    │
│  │  GET /login           GET /                POST /api/analyze │    │
│  │  GET /auth/callback   GET /dashboard       GET  /api/history │    │
│  │  GET /logout          GET /history         GET  /api/history/│    │
│  │                                            DELETE /api/hist..│    │
│  │                                            GET  /api/me      │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐    │
│  │                     SERVICE LAYER                            │    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │    │
│  │  │  Validators  │  │  PDF Parser  │  │   AI Engine      │   │    │
│  │  │  (Python)    │  │ (pdfplumber) │  │  (scikit-learn)  │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │              DB Service (PyMongo)                     │   │    │
│  │  └───────────────────────┬──────────────────────────────┘   │    │
│  └──────────────────────────┼──────────────────────────────────┘    │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
              ┌───────────────▼────────────────┐
              │          MONGODB               │
              │                                │
              │  Database: resume_mind_db      │
              │  Collections:                  │
              │    • users                     │
              │    • analyses                  │
              └────────────────────────────────┘

              ┌────────────────────────────────┐
              │   GOOGLE OAUTH 2.0 SERVER      │
              │   (External — Google Cloud)    │
              │   accounts.google.com          │
              └────────────────────────────────┘
```

---

## 4. Component Responsibilities

| Component | Technology | Responsibility |
|---|---|---|
| **Flask App** | `app.py` | Entry point, route registration, CORS setup, session config |
| **Auth Routes** | `routes/auth_routes.py` + Authlib | Google OAuth2 login, callback, token exchange, logout |
| **Page Routes** | `routes/page_routes.py` | Serves HTML pages (login, dashboard, history) via Jinja2 |
| **API Routes** | `routes/api_routes.py` | REST endpoints for analysis, history retrieval, profile |
| **Validators** | `utils/validators.py` | Enforces 500-word limit, 10-file limit, PDF-only check |
| **PDF Parser** | `utils/pdf_parser.py` + pdfplumber | Extracts raw text from uploaded PDF files |
| **AI Engine** | `utils/ai_engine.py` + scikit-learn | TF-IDF vectorization → cosine similarity → % score + skills |
| **DB Service** | `utils/db_service.py` + PyMongo | CRUD operations on MongoDB (users, analyses) |
| **Frontend** | `static/` + `templates/` | UI rendering, form input, JS fetch calls, result display |
| **MongoDB** | External service | Persistent document storage |
| **Google OAuth** | External service | Identity verification and user profile provider |

---

## 5. All System Flows

### Flow 1 — User Login (Google OAuth)

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────────
 1    Browser          User clicks "Login with Google" button
 2    Browser → Flask  GET /login
 3    Flask → Authlib  Generates OAuth state + redirect URI
 4    Flask → Browser  HTTP 302 → https://accounts.google.com/o/oauth2/auth
 5    Browser          User sees Google consent screen, grants permission
 6    Google → Browser HTTP 302 → http://localhost:5000/auth/callback?code=XXX&state=YYY
 7    Browser → Flask  GET /auth/callback?code=XXX&state=YYY
 8    Flask → Authlib  Exchanges auth code for access token
 9    Flask → Google   Fetches user profile (name, email, picture)
10    Flask → PyMongo  Upserts user record in `users` collection
11    Flask            Sets server-side session:
                        session['user_id']   = google_sub
                        session['user_name'] = "Roshani Devi"
                        session['user_email']= "roshani@gmail.com"
                        session['user_pic']  = avatar_url
                        session['logged_in'] = True
12    Flask → Browser  HTTP 302 → /dashboard
13    Browser          Dashboard page loads with user info
```

### Flow 2 — User Logout

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User clicks "Logout" button
 2    Browser → Flask  GET /logout
 3    Flask            Clears server-side session (session.clear())
 4    Flask → Browser  HTTP 302 → / (landing page)
 5    Browser          Landing page displays login button again
```

### Flow 3 — Access Protected Page (Unauthenticated)

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User navigates to /dashboard or /history directly
 2    Browser → Flask  GET /dashboard
 3    Flask            Checks session['logged_in'] → not found
 4    Flask → Browser  HTTP 302 → / (redirect to login page)
```

### Flow 4 — Resume Analysis (Core Feature)

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User types Job Description (≤500 words)
 2    Browser (JS)     Frontend validates word count in real-time
 3    Browser          User selects up to 10 PDF files
 4    Browser (JS)     Frontend validates: file count ≤ 10, all .pdf
 5    Browser → Flask  POST /api/analyze (multipart/form-data)
                        Body: { job_description: string, resumes: File[] }
 6    Flask            BACKEND VALIDATION:
                        • Check session['logged_in'] → 401 if missing
                        • Check JD word count ≤ 500 → 400 if exceeded
                        • Check file count ≤ 10 → 400 if exceeded
                        • Check all files end with .pdf → 400 if invalid
                        • Check JD is not empty → 400 if blank
 7    Flask → pdfplumber  For EACH PDF file:
                            • Open file stream
                            • Extract text from all pages
                            • Concatenate into single string
                            • Clean text (regex: lowercase, remove emails/phones)
 8    Flask → scikit-learn For EACH extracted resume text:
                            • Create TfidfVectorizer(stop_words='english')
                            • fit_transform([jd_text, resume_text])
                            • Compute cosine_similarity → match_percentage
                            • Find overlapping non-zero vector indices → matched_skills
 9    Flask             Sort results array by match_percentage descending
                         Assign rank 1, 2, 3...
10    Flask → PyMongo   Save analysis document to `analyses` collection:
                         {
                           user_id, jd_snippet, total_resumes,
                           created_at, results: [{ filename, score, skills }]
                         }
11    Flask → Browser   HTTP 200 JSON response:
                         {
                           status: "success",
                           analysis_id: "...",
                           results: [{ rank, filename, match_percentage, matched_skills }]
                         }
12    Browser (JS)      Parses JSON response
                         Dynamically creates ranked candidate cards:
                           • Progress bar showing percentage
                           • Skill badges for each matched skill
                           • Rank number and filename
```

### Flow 5 — View Analysis History (List)

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User navigates to History page
 2    Browser → Flask  GET /history (HTML page load)
 3    Flask            Verifies session → renders history.html template
 4    Browser (JS)     On page load: fetch('/api/history?limit=20&page=1')
 5    Browser → Flask  GET /api/history?limit=20&page=1
 6    Flask            Checks session['logged_in'] → 401 if missing
 7    Flask → PyMongo  Queries `analyses` collection:
                         filter: { user_id: session['user_id'] }
                         sort: { created_at: -1 }
                         limit: 20, skip: (page-1)*20
 8    Flask → Browser  HTTP 200 JSON:
                         {
                           status: "success",
                           total: 5,
                           page: 1,
                           history: [{ analysis_id, created_at, jd_snippet,
                                       total_resumes, top_candidate }]
                         }
 9    Browser (JS)     Renders list of history cards with summary info
```

### Flow 6 — View Single Analysis Detail

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User clicks on a history card
 2    Browser (JS)     fetch('/api/history/669f3c2a1b4e5d0012abc123')
 3    Browser → Flask  GET /api/history/669f3c2a1b4e5d0012abc123
 4    Flask            Checks session → 401 if missing
 5    Flask → PyMongo  Queries `analyses` by _id
 6    Flask            Verifies document.user_id == session['user_id']
                         → 403 if mismatch (prevents cross-user access)
                         → 404 if document not found
 7    Flask → Browser  HTTP 200 JSON:
                         {
                           status: "success",
                           analysis_id, created_at, jd_snippet,
                           total_resumes, results: [{ rank, filename,
                           match_percentage, matched_skills }]
                         }
 8    Browser (JS)     Renders full detail view with all candidates
```

### Flow 7 — Delete Analysis Record

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser          User clicks delete icon on a history card
 2    Browser (JS)     Confirmation dialog → user confirms
 3    Browser → Flask  DELETE /api/history/669f3c2a1b4e5d0012abc123
 4    Flask            Checks session → 401 if missing
 5    Flask → PyMongo  Finds document by _id
 6    Flask            Verifies ownership (user_id match) → 403 if not
 7    Flask → PyMongo  Deletes document from `analyses` collection
 8    Flask → Browser  HTTP 200 JSON:
                         { status: "success", message: "Analysis deleted." }
 9    Browser (JS)     Removes the card from DOM
```

### Flow 8 — Get Current User Profile

```
Step  Actor            Action
────  ───────────────  ──────────────────────────────────────────────
 1    Browser (JS)     On dashboard load: fetch('/api/me')
 2    Browser → Flask  GET /api/me
 3    Flask            Reads session data
 4    Flask → Browser  HTTP 200 JSON:
                         {
                           status: "success",
                           user: { name, email, picture }
                         }
 5    Browser (JS)     Updates avatar, name display in navbar
```

---

## 6. Deployment View (Local Development)

```
Developer Machine (localhost)
│
├── Flask Dev Server
│     Command: python app.py
│     URL:     http://127.0.0.1:5000
│     Serves:  HTML pages + /api/* routes
│
├── MongoDB Server
│     Command: mongod
│     URL:     mongodb://localhost:27017
│     DB:      resume_mind_db
│
├── .env File (Secrets — never committed to git)
│     FLASK_SECRET_KEY=...
│     GOOGLE_CLIENT_ID=...
│     GOOGLE_CLIENT_SECRET=...
│     MONGO_URI=mongodb://localhost:27017
│
└── Google Cloud Console
      Project: ResumeMind
      OAuth 2.0 Credentials configured
      Authorized redirect URI: http://localhost:5000/auth/callback
```

---

## 7. Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Response Time** | Analysis of 10 PDFs completes in < 10 seconds |
| **File Size** | Each PDF ≤ 5 MB |
| **Concurrency** | Single-user local development (Flask dev server) |
| **Security** | Secrets in `.env`, session-based auth, ownership validation on all data access |
| **Browser Support** | Modern browsers (Chrome, Firefox, Edge) |
| **Data Integrity** | All user data isolated by `user_id` — no cross-user access |
