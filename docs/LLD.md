# ResumeMind — Low-Level Design (LLD)

---

## 1. Project Folder Structure

```
resume_mind/
│
├── app.py                        ← Flask app factory, CORS, session config
├── config.py                     ← Config class loading from .env
├── requirements.txt              ← All pip dependencies
├── .env                          ← Secrets (NEVER commit to git)
├── .gitignore
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py            ← /login, /auth/callback, /logout
│   ├── page_routes.py            ← /, /dashboard, /history (HTML renderers)
│   └── api_routes.py             ← /api/analyze, /api/history, /api/me
│
├── utils/
│   ├── __init__.py
│   ├── pdf_parser.py             ← extract_text_from_pdf()
│   ├── ai_engine.py              ← calculate_match(), clean_text()
│   ├── validators.py             ← validate_word_count(), validate_files()
│   └── db_service.py             ← upsert_user(), save_analysis(), get_history()
│
├── static/
│   ├── css/
│   │   └── style.css             ← All styling
│   ├── js/
│   │   ├── main.js               ← Dashboard page: upload + analyze + render
│   │   └── history.js            ← History page: fetch + render past records
│   └── images/                   ← Logo, icons, etc.
│
├── templates/
│   ├── base.html                 ← Base layout (nav, footer, shared CSS/JS)
│   ├── login.html                ← Landing page with Google login button
│   ├── dashboard.html            ← JD input + file upload + results area
│   └── history.html              ← Past analysis sessions list + detail view
│
└── docs/
    ├── HLD.md
    ├── LLD.md
    └── API.md
```

---

## 2. Configuration Module

### `config.py`

```
Class: Config
│
├── Attributes (loaded from .env via python-dotenv):
│   ├── SECRET_KEY           : str   ← Flask session encryption key
│   ├── MONGO_URI            : str   ← MongoDB connection string
│   ├── MONGO_DB_NAME        : str   ← Default: "resume_mind_db"
│   ├── GOOGLE_CLIENT_ID     : str   ← From Google Cloud Console
│   ├── GOOGLE_CLIENT_SECRET : str   ← From Google Cloud Console
│   ├── GOOGLE_REDIRECT_URI  : str   ← Default: "http://localhost:5000/auth/callback"
│   ├── MAX_RESUMES          : int   ← Default: 10
│   ├── MAX_JD_WORDS         : int   ← Default: 500
│   └── MAX_FILE_SIZE_MB     : int   ← Default: 5
```

### `.env` File Template

```
FLASK_SECRET_KEY=your-random-secret-key-here
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
MONGO_URI=mongodb://localhost:27017
```

---

## 3. Flask Application Entry Point

### `app.py`

```
Function: create_app() → Flask
│
├── Step 1: Load config from Config class
├── Step 2: Initialize Flask app with SECRET_KEY
├── Step 3: Configure server-side sessions
├── Step 4: Add CORS middleware
│     └── Allow origins: ["http://localhost:5000", "http://127.0.0.1:5000"]
├── Step 5: Register OAuth client (Authlib)
│     └── google client with:
│           client_id, client_secret,
│           authorize_url: "https://accounts.google.com/o/oauth2/auth"
│           token_url:     "https://oauth2.googleapis.com/token"
│           userinfo_url:  "https://openidconnect.googleapis.com/v1/userinfo"
│           scope:         "openid email profile"
├── Step 6: Initialize PyMongo connection
│     └── db = MongoClient(MONGO_URI)[MONGO_DB_NAME]
├── Step 7: Register Blueprints
│     ├── auth_bp  (prefix: none)
│     ├── page_bp  (prefix: none)
│     └── api_bp   (prefix: /api)
├── Step 8: Mount static files directory
└── Step 9: Return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
```

---

## 4. Route Modules — Detailed Design

---

### 4.1 `routes/auth_routes.py`

**Blueprint:** `auth_bp`

---

#### `GET /login` — `login()`

```
PROCESS:
  1. Generate a random nonce for CSRF protection
  2. Use Authlib's oauth.google.authorize_redirect()
  3. Pass redirect_uri = Config.GOOGLE_REDIRECT_URI
  4. Return: HTTP 302 → Google consent screen URL

REDIRECTS TO:
  https://accounts.google.com/o/oauth2/auth
    ?client_id=XXX
    &redirect_uri=http://localhost:5000/auth/callback
    &response_type=code
    &scope=openid+email+profile
    &state=random_csrf_token
```

---

#### `GET /auth/callback` — `auth_callback()`

```
INPUTS (query params from Google redirect):
  code   : str  ← Authorization code
  state  : str  ← CSRF state token

PROCESS:
  1. Call oauth.google.authorize_access_token()
       → Sends POST to https://oauth2.googleapis.com/token
       → Exchanges code for access_token + id_token
  2. Parse id_token or call userinfo endpoint
       → Returns: { sub, name, email, picture }
  3. Call db_service.upsert_user() with user profile
  4. Set Flask session:
       session['user_id']    = user_info['sub']
       session['user_name']  = user_info['name']
       session['user_email'] = user_info['email']
       session['user_pic']   = user_info['picture']
       session['logged_in']  = True

OUTPUT:
  Success → HTTP 302 redirect to /dashboard
  Failure → HTTP 302 redirect to /?error=auth_failed

ERROR HANDLING:
  - If Google returns an error param → redirect to login with error message
  - If token exchange fails → redirect to login with error message
  - If userinfo fetch fails → redirect to login with error message
```

---

#### `GET /logout` — `logout()`

```
PROCESS:
  1. session.clear()  ← removes all session keys
  2. Return: HTTP 302 redirect to /

NO ERRORS — always succeeds
```

---

### 4.2 `routes/page_routes.py`

**Blueprint:** `page_bp`

Each page route follows this pattern:
```
1. Check session['logged_in']
2. If not logged in and page is protected → redirect to /
3. If logged in → render template with user data from session
```

---

#### `GET /` — `landing()`

```
PROCESS:
  1. If session.get('logged_in') is True:
       → HTTP 302 redirect to /dashboard
  2. Else:
       → render_template('login.html')
       → Pass error message from query param if present
```

---

#### `GET /dashboard` — `dashboard()`

```
GUARD: session['logged_in'] must be True → else redirect to /

PROCESS:
  1. Extract user data from session
  2. render_template('dashboard.html',
       user_name  = session['user_name'],
       user_email = session['user_email'],
       user_pic   = session['user_pic']
     )
```

---

#### `GET /history` — `history_page()`

```
GUARD: session['logged_in'] must be True → else redirect to /

PROCESS:
  1. render_template('history.html',
       user_name = session['user_name'],
       user_pic  = session['user_pic']
     )
  Note: Actual history data is loaded via JS fetch('/api/history')
```

---

### 4.3 `routes/api_routes.py`

**Blueprint:** `api_bp` (url_prefix = `/api`)

All API routes return JSON. All require active session.

---

#### `POST /api/analyze` — `analyze()`

```
GUARD: session['logged_in'] must be True → else return 401 JSON

INPUTS:
  request.form['job_description']  : str       ← Job description text
  request.files.getlist('resumes') : list[File] ← Uploaded PDF files

PROCESS:
  ┌─ STEP 1: VALIDATION ─────────────────────────────────────────┐
  │                                                                │
  │  a. If job_description is empty or whitespace-only:            │
  │     → return 400, error: "empty_job_description"               │
  │                                                                │
  │  b. If word count of job_description > 500:                    │
  │     → return 400, error: "job_description_too_long"            │
  │                                                                │
  │  c. If no files uploaded:                                      │
  │     → return 400, error: "no_resumes_provided"                 │
  │                                                                │
  │  d. If file count > 10:                                        │
  │     → return 400, error: "too_many_files"                      │
  │                                                                │
  │  e. For each file — if not filename.endswith('.pdf'):           │
  │     → return 400, error: "invalid_file_type"                   │
  │                                                                │
  └────────────────────────────────────────────────────────────────┘

  ┌─ STEP 2: TEXT EXTRACTION ─────────────────────────────────────┐
  │                                                                │
  │  For each validated PDF file:                                  │
  │    text = pdf_parser.extract_text_from_pdf(file.stream)        │
  │    cleaned = ai_engine.clean_text(text)                        │
  │    Store: { filename: file.filename, text: cleaned }           │
  │                                                                │
  │  If extraction fails for a file → skip it, log warning         │
  └────────────────────────────────────────────────────────────────┘

  ┌─ STEP 3: AI SCORING ─────────────────────────────────────────┐
  │                                                                │
  │  cleaned_jd = ai_engine.clean_text(job_description)            │
  │                                                                │
  │  For each resume with extracted text:                           │
  │    result = ai_engine.calculate_match(cleaned_jd, resume_text) │
  │    → returns { match_percentage: float, matched_skills: [] }   │
  │                                                                │
  │  Collect all results into array                                │
  └────────────────────────────────────────────────────────────────┘

  ┌─ STEP 4: RANKING ────────────────────────────────────────────┐
  │                                                                │
  │  Sort results by match_percentage DESCENDING                   │
  │  Assign rank = 1, 2, 3... to sorted results                   │
  └────────────────────────────────────────────────────────────────┘

  ┌─ STEP 5: PERSISTENCE ───────────────────────────────────────┐
  │                                                                │
  │  analysis_id = db_service.save_analysis(                       │
  │    user_id    = session['user_id'],                            │
  │    jd_snippet = job_description[:100] + "...",                 │
  │    results    = ranked_results_array                           │
  │  )                                                             │
  └────────────────────────────────────────────────────────────────┘

OUTPUT (200 OK):
  {
    "status": "success",
    "analysis_id": "669f3c2a...",
    "total_processed": 3,
    "results": [
      { "rank": 1, "filename": "...", "match_percentage": 91.5,
        "matched_skills": ["python", "flask", ...] },
      ...
    ]
  }

ERROR OUTPUT (4xx/5xx):
  { "status": "error", "error": "error_code", "message": "Human readable" }
```

---

#### Full design for remaining API routes — see [API.md](file:///c:/Users/amanj/OneDrive/Desktop/Roshani%20Project%20FIles/resume_mind/docs/API.md)

---

## 5. Utility Modules — Detailed Design

---

### 5.1 `utils/pdf_parser.py`

---

#### Function: `extract_text_from_pdf(file_stream: BinaryIO) → str`

```
INPUTS:
  file_stream  → Binary file-like object (e.g., from request.files['resume'])

ALGORITHM:
  1. pdf = pdfplumber.open(file_stream)
  2. all_text = ""
  3. FOR page IN pdf.pages:
  4.     page_text = page.extract_text()
  5.     IF page_text is not None:
  6.         all_text += page_text + "\n"
  7. pdf.close()
  8. RETURN all_text.strip()

EDGE CASES:
  - If pdfplumber.open() raises an exception → return ""
  - If all pages return None (scanned image PDF) → return ""
  - The caller should check for empty string and handle accordingly

DEPENDENCIES:
  - pdfplumber
```

---

### 5.2 `utils/ai_engine.py`

---

#### Function: `clean_text(raw_text: str) → str`

```
INPUTS:
  raw_text → Raw string from PDF or user input

ALGORITHM:
  1. text = raw_text.lower()
  2. text = re.sub(r'\S+@\S+', '', text)          ← Remove email addresses
  3. text = re.sub(r'\+?\d[\d\s\-]{8,}\d', '', text)  ← Remove phone numbers
  4. text = re.sub(r'http\S+', '', text)           ← Remove URLs
  5. text = re.sub(r'[^a-z0-9\s]', ' ', text)     ← Remove special chars
  6. text = re.sub(r'\s+', ' ', text).strip()      ← Collapse whitespace
  7. RETURN text

OUTPUT:
  Clean lowercase string with only alphanumeric words and spaces
```

---

#### Function: `calculate_match(jd_text: str, resume_text: str) → dict`

```
INPUTS:
  jd_text      → Cleaned job description string
  resume_text  → Cleaned resume text string

PRECONDITIONS:
  - Both strings should already be passed through clean_text()
  - Neither string should be empty (caller validates)

ALGORITHM:
  ┌─────────────────────────────────────────────────────────────┐
  │ Step 1: VECTORIZATION                                       │
  │   vectorizer = TfidfVectorizer(stop_words='english')        │
  │   tfidf_matrix = vectorizer.fit_transform(                  │
  │       [jd_text, resume_text]                                │
  │   )                                                         │
  │   # tfidf_matrix is a 2×N sparse matrix                     │
  │   # Row 0 = JD vector, Row 1 = Resume vector                │
  │   # N = number of unique meaningful words across both docs   │
  └─────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────┐
  │ Step 2: SIMILARITY SCORING                                   │
  │   feature_names = vectorizer.get_feature_names_out()         │
  │   jd_vector     = tfidf_matrix[0].toarray()[0]               │
  │   resume_vector = tfidf_matrix[1].toarray()[0]               │
  │                                                              │
  │   similarity = cosine_similarity(                            │
  │       tfidf_matrix[0:1], tfidf_matrix[1:2]                   │
  │   )                                                          │
  │   match_percentage = round(similarity[0][0] * 100, 1)        │
  │   # Result: float between 0.0 and 100.0                      │
  └─────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────┐
  │ Step 3: SKILL EXTRACTION                                     │
  │   matched_indices = np.where(                                │
  │       (jd_vector > 0) & (resume_vector > 0)                  │
  │   )[0]                                                       │
  │                                                              │
  │   matched_skills = [                                         │
  │       feature_names[i] for i in matched_indices              │
  │   ]                                                          │
  │   # These are words present in BOTH the JD and resume        │
  │   # with non-zero TF-IDF weight (stop words excluded)        │
  └─────────────────────────────────────────────────────────────┘

OUTPUT:
  {
    "match_percentage": 84.2,        ← float (0.0 to 100.0)
    "matched_skills": [              ← list of lowercase strings
      "python", "flask", "mongodb", "backend", "api"
    ]
  }

EDGE CASES:
  - If both texts are identical → returns 100.0%
  - If no common words → returns 0.0% with empty skills list
  - If resume_text is empty → return { match_percentage: 0.0, matched_skills: [] }
```

---

### 5.3 `utils/validators.py`

---

#### Function: `validate_word_count(text: str, limit: int = 500) → tuple[bool, str]`

```
ALGORITHM:
  1. words = text.strip().split()
  2. IF len(words) == 0:
       RETURN (False, "Job description cannot be empty")
  3. IF len(words) > limit:
       RETURN (False, f"Job description exceeds {limit} word limit ({len(words)} words)")
  4. RETURN (True, "OK")
```

---

#### Function: `validate_files(files: list) → tuple[bool, str]`

```
ALGORITHM:
  1. IF len(files) == 0:
       RETURN (False, "No resume files provided")
  2. IF len(files) > 10:
       RETURN (False, "Maximum 10 resume files allowed")
  3. FOR each file IN files:
       IF NOT file.filename.lower().endswith('.pdf'):
         RETURN (False, f"Invalid file type: {file.filename}. Only PDF files accepted")
  4. RETURN (True, "OK")
```

---

### 5.4 `utils/db_service.py`

---

#### Function: `upsert_user(db, user_info: dict) → None`

```
INPUTS:
  db         → PyMongo database instance
  user_info  → Dict with keys: sub, name, email, picture

ALGORITHM:
  db.users.update_one(
    filter = { "google_id": user_info["sub"] },
    update = {
      "$set": {
        "name":       user_info["name"],
        "email":      user_info["email"],
        "picture":    user_info["picture"],
        "last_login": datetime.utcnow()
      },
      "$setOnInsert": {
        "google_id":  user_info["sub"],
        "created_at": datetime.utcnow()
      }
    },
    upsert = True
  )

NOTES:
  - $set updates fields every login
  - $setOnInsert only runs on first creation
  - upsert=True → creates if not found, updates if found
```

---

#### Function: `save_analysis(db, user_id: str, jd_snippet: str, results: list) → str`

```
INPUTS:
  db          → PyMongo database instance
  user_id     → Google sub (from session)
  jd_snippet  → First 100 chars of job description
  results     → List of dicts: [{ filename, match_percentage, matched_skills }]

ALGORITHM:
  document = {
    "user_id":                  user_id,
    "job_description_snippet":  jd_snippet,
    "total_resumes":            len(results),
    "created_at":               datetime.utcnow(),
    "results":                  results
  }
  inserted = db.analyses.insert_one(document)
  RETURN str(inserted.inserted_id)
```

---

#### Function: `get_history(db, user_id: str, limit: int = 20, page: int = 1) → dict`

```
INPUTS:
  db       → PyMongo database instance
  user_id  → Google sub (from session)
  limit    → Number of records per page (default 20)
  page     → Page number (default 1)

ALGORITHM:
  skip_count = (page - 1) * limit

  total = db.analyses.count_documents({ "user_id": user_id })

  cursor = db.analyses.find(
    filter     = { "user_id": user_id },
    projection = {
      "user_id": 0               ← Exclude from response (already known)
    }
  ).sort("created_at", -1).skip(skip_count).limit(limit)

  records = []
  FOR doc IN cursor:
    doc["_id"] = str(doc["_id"])  ← Convert ObjectId to string
    # Add top_candidate summary
    IF doc["results"]:
      top = max(doc["results"], key=lambda r: r["match_percentage"])
      doc["top_candidate"] = {
        "filename": top["filename"],
        "match_percentage": top["match_percentage"]
      }
    records.append(doc)

  RETURN {
    "total": total,
    "page":  page,
    "history": records
  }
```

---

#### Function: `get_analysis_by_id(db, analysis_id: str, user_id: str) → tuple[dict | None, str]`

```
ALGORITHM:
  1. Convert analysis_id string to ObjectId
       If conversion fails → RETURN (None, "invalid_id")
  2. doc = db.analyses.find_one({ "_id": ObjectId(analysis_id) })
  3. IF doc is None → RETURN (None, "not_found")
  4. IF doc["user_id"] != user_id → RETURN (None, "forbidden")
  5. doc["_id"] = str(doc["_id"])
  6. RETURN (doc, "ok")
```

---

#### Function: `delete_analysis(db, analysis_id: str, user_id: str) → tuple[bool, str]`

```
ALGORITHM:
  1. Convert analysis_id string to ObjectId
       If conversion fails → RETURN (False, "invalid_id")
  2. doc = db.analyses.find_one({ "_id": ObjectId(analysis_id) })
  3. IF doc is None → RETURN (False, "not_found")
  4. IF doc["user_id"] != user_id → RETURN (False, "forbidden")
  5. db.analyses.delete_one({ "_id": ObjectId(analysis_id) })
  6. RETURN (True, "ok")
```

---

## 6. MongoDB Collection Schemas

---

### 6.1 `users` Collection

```json
{
  "_id":        ObjectId("669f3b001b4e5d0012abc100"),
  "google_id":  "118290764523847612345",
  "name":       "Roshani Devi",
  "email":      "roshani@gmail.com",
  "picture":    "https://lh3.googleusercontent.com/a/ACg8oc...",
  "created_at": ISODate("2026-07-03T14:00:00Z"),
  "last_login": ISODate("2026-07-03T18:30:00Z")
}
```

**Indexes:**
| Index | Fields | Type | Purpose |
|---|---|---|---|
| Primary | `_id` | Unique (auto) | MongoDB default |
| Google ID | `google_id` | Unique | Fast lookup on login |
| Email | `email` | Unique | Prevent duplicate accounts |

---

### 6.2 `analyses` Collection

```json
{
  "_id":                     ObjectId("669f3c2a1b4e5d0012abc123"),
  "user_id":                 "118290764523847612345",
  "job_description_snippet": "We are looking for a Python backend developer with experience in...",
  "total_resumes":           3,
  "created_at":              ISODate("2026-07-03T14:05:00Z"),
  "results": [
    {
      "candidate_filename":  "roshani_resume.pdf",
      "match_percentage":    91.5,
      "matched_skills":      ["python", "flask", "mongodb", "rest", "api", "authlib"]
    },
    {
      "candidate_filename":  "aman_resume.pdf",
      "match_percentage":    84.2,
      "matched_skills":      ["python", "flask", "mongodb", "rest", "api"]
    },
    {
      "candidate_filename":  "priya_resume.pdf",
      "match_percentage":    61.0,
      "matched_skills":      ["python", "mongodb"]
    }
  ]
}
```

**Indexes:**
| Index | Fields | Type | Purpose |
|---|---|---|---|
| Primary | `_id` | Unique (auto) | MongoDB default |
| User History | `user_id` + `created_at` | Compound | Fast history query sorted by date |

---

## 7. Frontend Module Design

---

### 7.1 `templates/base.html`

```
Base template providing:
  - <head> with meta tags, CSS link, Google Fonts
  - Navigation bar with:
      - Logo / App name
      - User avatar + name (from Jinja2 context)
      - Logout button
  - {% block content %} — overridden by child templates
  - Footer
  - <script> tags for page-specific JS
```

---

### 7.2 `static/js/main.js` (Dashboard Page)

```
RESPONSIBILITIES:
  1. Word counter — updates live count as user types in JD textarea
  2. File validator — checks file count ≤ 10 and all are .pdf before submit
  3. Form submission — constructs FormData, sends via fetch() to POST /api/analyze
  4. Loading state — shows spinner/progress during analysis
  5. Result renderer — parses JSON response and creates:
       • Ranked candidate cards
       • Animated progress bars (width = match_percentage%)
       • Skill badges for each matched_skill
       • Error message display for 4xx responses

FUNCTIONS:
  - countWords(text) → int
  - validateForm() → bool
  - submitAnalysis(formData) → Promise<JSON>
  - renderResults(data) → void (DOM manipulation)
  - renderError(errorData) → void
```

---

### 7.3 `static/js/history.js` (History Page)

```
RESPONSIBILITIES:
  1. On page load — fetch('/api/history') and render list
  2. Click handler — when user clicks a card, fetch detail by analysis_id
  3. Delete handler — confirm dialog → DELETE /api/history/<id> → remove card
  4. Pagination — load more button or page navigation

FUNCTIONS:
  - loadHistory(page) → void
  - renderHistoryCards(data) → void
  - viewDetail(analysisId) → void
  - deleteAnalysis(analysisId) → void
```

---

## 8. Dependencies (`requirements.txt`)

```
flask
authlib
pdfplumber
scikit-learn
pymongo
python-dotenv
requests
numpy
```

Install command:
```bash
pip install -r requirements.txt
```
