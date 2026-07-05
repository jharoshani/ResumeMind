# ResumeMind 🧠

An AI-powered Resume Analysis web application built with Flask, MongoDB, and scikit-learn.

Upload up to 10 PDF resumes, enter a Job Description, and get ranked candidates with match percentages and highlighted skills — powered by TF-IDF and Cosine Similarity.

---

## Features

- **Google OAuth Login** — Secure authentication via Authlib
- **Job Description Input** — Text area with 500-word limit validation
- **Bulk Resume Upload** — Upload up to 10 PDF resumes at once
- **AI Matching Engine** — TF-IDF vectorization + cosine similarity scoring (1%–100%)
- **Skill Extraction** — Highlights matching skills between JD and each resume
- **Ranked Results** — Candidates sorted by match score with visual progress bars
- **Analysis History** — View, revisit, and delete past analyses
- **MongoDB Storage** — Persistent storage for users and analysis results

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Flask (Python) |
| Authentication | Google OAuth 2.0 via Authlib |
| AI/ML Engine | scikit-learn (TF-IDF + Cosine Similarity) |
| PDF Parsing | pdfplumber |
| Database | MongoDB (PyMongo) |
| Deployment | Render (free tier) |

---

## Project Structure

```
resume_mind/
├── app.py                  ← Flask entry point
├── config.py               ← Environment config loader
├── requirements.txt
├── Procfile                ← Production server config
├── .env                    ← Secrets (not in git)
├── routes/
│   ├── auth_routes.py      ← Login, callback, logout
│   ├── page_routes.py      ← HTML page renderers
│   └── api_routes.py       ← REST API endpoints
├── utils/
│   ├── pdf_parser.py       ← PDF text extraction
│   ├── ai_engine.py        ← TF-IDF scoring + skill matching
│   ├── validators.py       ← Input validation
│   └── db_service.py       ← MongoDB operations
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── history.html
└── docs/
    ├── HLD.md              ← High-Level Design
    ├── LLD.md              ← Low-Level Design
    └── API.md              ← API Specification
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- MongoDB installed and running locally
- Google Cloud Console project with OAuth 2.0 credentials

### Setup

```bash
# Clone the repo
git clone https://github.com/your-username/resume_mind.git
cd resume_mind

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your credentials

# Run the app
python app.py
```

### `.env` File Format

```
FLASK_SECRET_KEY=your-random-secret-key
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
MONGO_URI=mongodb://localhost:27017
```

Open `http://localhost:5000` in your browser.

---

## Deployment (Render — Free)

1. Push code to GitHub
2. Create a free account on [render.com](https://render.com)
3. New → Web Service → Connect your GitHub repo
4. Set environment variables (same as `.env`)
5. Use **MongoDB Atlas** free tier for cloud database
6. Deploy — Render reads the `Procfile` automatically

---

## Documentation

- [High-Level Design (HLD)](docs/HLD.md) — Architecture, flows, components
- [Low-Level Design (LLD)](docs/LLD.md) — Module design, functions, schemas
- [API Specification](docs/API.md) — All 11 endpoints with request/response formats

---

## Author

Built as a college project for MCA (AI/ML specialization).

---

## License

This project is for educational purposes.
