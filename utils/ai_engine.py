import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean_text(raw_text):
    """
    Clean raw text by removing emails, phone numbers, URLs, and special characters.

    Args:
        raw_text: Raw string from PDF extraction or user input.

    Returns:
        str: Cleaned lowercase string with only alphanumeric words and spaces.
    """
    if not raw_text:
        return ""

    text = raw_text.lower()
    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)
    # Remove phone numbers
    text = re.sub(r"\+?\d[\d\s\-]{8,}\d", "", text)
    # Remove URLs
    text = re.sub(r"http\S+", "", text)
    # Remove special characters, keep only alphanumeric and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def calculate_match(raw_jd, raw_resume):
    """
    Calculate a multi-factor match percentage and compile diagnostics / coaching tips
    between a job description and a resume.

    Scores are broken down into:
      1. Core Match (40%): TF-IDF similarity (30%) + Job Title Alignment (10%)
      2. Experience & Tenure (30%): YoE Match (20%) + Seniority Alignment (10%)
      3. Impact & Quality (20%): Quantifiable Metrics (10%) + Action Verbs (10%)
      4. Formatting & Structure (10%): Contact Info (3%) + Section Headers (4%) + Length check (3%)

    Args:
        raw_jd: Raw job description text.
        raw_resume: Raw resume text.

    Returns:
        dict: {
            "match_percentage": float (0.0 to 100.0),
            "breakdown": { "core": float, "experience": float, "quality": float, "format": float },
            "matched_skills": list[str],
            "missing_skills": list[str],
            "coaching_tips": list[str],
            "warnings": list[str]
        }
    """
    # 0. Handle empty inputs
    if not raw_jd or not raw_resume or not raw_jd.strip() or not raw_resume.strip():
        return {
            "match_percentage": 0.0,
            "breakdown": {"core": 0.0, "experience": 0.0, "quality": 0.0, "format": 0.0},
            "matched_skills": [],
            "missing_skills": [],
            "coaching_tips": ["Ensure you paste a valid job description and upload a text-readable resume."],
            "warnings": ["Empty job description or resume text detected."]
        }

    coaching_tips = []
    warnings = []

    # Cleaned texts for NLP TF-IDF
    cleaned_jd = clean_text(raw_jd)
    cleaned_resume = clean_text(raw_resume)

    # 1. CORE MATCH (Max: 40 points)
    core_score = 0.0
    matched_skills = []
    missing_skills = []

    # 1.1 TF-IDF Cosine Similarity (Max: 30 points)
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([cleaned_jd, cleaned_resume])
        
        feature_names = vectorizer.get_feature_names_out()
        jd_vector = tfidf_matrix[0].toarray()[0]
        resume_vector = tfidf_matrix[1].toarray()[0]

        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        similarity_score = min(float(similarity) * 30.0, 30.0)
        core_score += similarity_score

        # Extract matched skills (words present in both JD and Resume)
        matched_indices = np.where((jd_vector > 0) & (resume_vector > 0))[0]
        matched_skills = sorted([feature_names[i] for i in matched_indices])

        # Extract missing skills (words present in JD with significant weight but missing in Resume)
        # Filter down to words that are present in the JD vector but NOT in the resume vector
        missing_indices = np.where((jd_vector > 0.05) & (resume_vector == 0))[0]
        missing_skills = sorted([feature_names[i] for i in missing_indices])[:12] # cap display at 12

        if len(missing_skills) > 0:
            coaching_tips.append(
                f"Missing Keywords: Your resume lacks several key terms from the job description: {', '.join(missing_skills[:5])}. Consider adding these if you have this experience."
            )
    except Exception:
        # Fallback if TF-IDF fails due to lack of vocabulary
        matched_skills = []
        missing_skills = []
        core_score += 0.0

    # 1.2 Job Title Alignment (Max: 10 points)
    # Extract title indicators from the first few words of the JD (e.g. "backend developer", "engineer")
    title_keywords = ["developer", "engineer", "designer", "analyst", "manager", "specialist", "architect", "consultant", "scientist"]
    jd_titles_found = [word for word in title_keywords if word in cleaned_jd]
    
    if jd_titles_found:
        resume_has_title = any(word in cleaned_resume for word in jd_titles_found)
        if resume_has_title:
            core_score += 10.0
        else:
            core_score += 5.0
            coaching_tips.append(
                "Synonym Warning: The target job title or role keywords (e.g., " + ", ".join(jd_titles_found[:2]) + ") were not found in your resume history. Verify you describe past roles using standard industry titles."
            )
    else:
        # If JD has no generic title keywords, default to full marks
        core_score += 10.0

    # 2. EXPERIENCE & TENURE (Max: 30 points)
    exp_score = 0.0

    # 2.1 Years of Experience (YoE) (Max: 20 points)
    # Search JD for expected YoE (e.g., "5+ years", "3 years of experience", "experience: 2 years")
    jd_yoe_match = re.search(r"(\d+)\+?\s*years?", raw_jd.lower())
    expected_yoe = int(jd_yoe_match.group(1)) if jd_yoe_match else 0

    # Calculate actual YoE from resume date ranges (e.g. 2018-2022, 2021 - Present)
    date_ranges = re.findall(r"\b((?:19|20)\d{2})\b\s*(?:-|to|until)\s*\b((?:19|20)\d{2}|present|current|now)\b", raw_resume.lower())
    
    tenure_years = 0.0
    current_year = 2026 # Context baseline year
    
    for start, end in date_ranges:
        start_yr = float(start)
        end_yr = current_year if end in ["present", "current", "now"] else float(end)
        diff = end_yr - start_yr
        if 0 < diff < 20: # Sanity check for realistic dates
            tenure_years += diff

    # Also search resume for declared years (e.g., "5+ years experience")
    resume_yoe_match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", raw_resume.lower())
    declared_yoe = float(resume_yoe_match.group(1)) if resume_yoe_match else 0.0

    actual_yoe = max(tenure_years, declared_yoe)

    if expected_yoe > 0:
        if actual_yoe >= expected_yoe:
            exp_score += 20.0
        else:
            exp_score += min((actual_yoe / expected_yoe) * 20.0, 20.0)
            coaching_tips.append(
                f"Experience Gap: The job description requires roughly {expected_yoe} years of experience, but our parser detected around {round(actual_yoe, 1)} years on your resume."
            )
    else:
        # Default full score if JD doesn't declare a specific YoE requirement
        exp_score += 20.0

    # 2.2 Seniority Indicators (Max: 10 points)
    seniority_keywords = ["senior", "sr", "lead", "principal", "manager", "director", "head", "architect"]
    junior_keywords = ["junior", "jr", "intern", "associate", "entry"]

    jd_is_senior = any(word in raw_jd.lower() for word in seniority_keywords)
    resume_is_senior = any(word in raw_resume.lower() for word in seniority_keywords)
    jd_is_junior = any(word in raw_jd.lower() for word in junior_keywords)
    resume_is_junior = any(word in raw_resume.lower() for word in junior_keywords)

    if jd_is_senior:
        if resume_is_senior:
            exp_score += 10.0
        else:
            exp_score += 3.0
            coaching_tips.append("Seniority Alignment: The job description looks for senior experience. Try to highlight leadership, mentoring, or architecture roles in your experience.")
    elif jd_is_junior:
        if resume_is_junior or not resume_is_senior:
            exp_score += 10.0
        else:
            exp_score += 7.0 # Slight mismatch for overqualification
            coaching_tips.append("Role Level: This appears to be an entry/junior role, but your resume contains senior indicators.")
    else:
        # No specific seniority match requested
        exp_score += 10.0

    # 3. IMPACT & QUALITY HEURISTICS (Max: 20 points)
    quality_score = 0.0

    # 3.1 Quantifiable Metrics (Max: 10 points)
    # Count numbers, %, $ symbols in the resume
    metric_count = len(re.findall(r"\b\d+\b|%|\$|₹", raw_resume))
    if metric_count >= 6:
        quality_score += 10.0
    elif metric_count >= 3:
        quality_score += 6.0
        coaching_tips.append("Quantifiable Impact: Add more metrics (percentages %, dollar signs $, numbers) to show the tangible results of your work (e.g., 'Optimized query speed by 25%').")
    else:
        quality_score += 2.0
        coaching_tips.append("Quantifiable Impact: Your resume lacks numbers or percentages. Recruiters prefer results-oriented descriptions rather than just listing responsibilities.")

    # 3.2 Action Verbs (Max: 10 points)
    action_verbs = [
        "designed", "implemented", "optimized", "spearheaded", "developed", 
        "architected", "integrated", "managed", "built", "created", 
        "led", "enhanced", "automated", "deployed", "scaled", "reduced", "increased"
    ]
    resume_words = cleaned_resume.split()
    action_verb_count = sum(1 for word in resume_words if word in action_verbs)

    if action_verb_count >= 8:
        quality_score += 10.0
    elif action_verb_count >= 3:
        quality_score += 6.0
        coaching_tips.append("Action Verbs: Try using more high-impact action verbs (e.g., 'Spearheaded', 'Architected', 'Automated') to describe your contributions.")
    else:
        quality_score += 3.0
        coaching_tips.append("Action Verbs: Your work descriptions are passive. Replace phrases like 'responsible for' or 'helped with' with active verbs like 'Implemented' or 'Optimized'.")

    # 4. FORMATTING & STRUCTURE (Max: 10 points)
    format_score = 0.0

    # 4.1 Contact Information (Max: 3 points)
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_resume))
    has_phone = bool(re.search(r"\b\+?\d[\d\s\-]{8,}\d\b", raw_resume))

    if has_email:
        format_score += 1.5
    else:
        warnings.append("Format Warning: No valid email address detected on your resume.")

    if has_phone:
        format_score += 1.5
    else:
        warnings.append("Format Warning: No phone number detected on your resume.")

    # 4.2 Section Headers (Max: 4 points)
    # Check for standard sections
    has_experience = any(h in cleaned_resume for h in ["experience", "work history", "employment", "professional background"])
    has_education = any(h in cleaned_resume for h in ["education", "academic", "college", "university", "qualification"])
    has_skills = any(h in cleaned_resume for h in ["skills", "technologies", "technical proficiency", "competencies"])

    sections_found = sum([has_experience, has_education, has_skills])
    format_score += (sections_found / 3.0) * 4.0

    missing_sections = []
    if not has_experience: missing_sections.append("Experience")
    if not has_education: missing_sections.append("Education")
    if not has_skills: missing_sections.append("Skills")

    if missing_sections:
        warnings.append(f"Structure Warning: Missing standard section header(s): {', '.join(missing_sections)}.")

    # 4.3 Resume Length (Max: 3 points)
    word_count = len(raw_resume.split())
    if 250 <= word_count <= 1000:
        format_score += 3.0
    elif 150 <= word_count <= 1500:
        format_score += 1.5
        coaching_tips.append("Resume Length: Your resume length is slightly sub-optimal. Aim for between 300 and 800 words for a standard 1-2 page layout.")
    else:
        format_score += 0.0
        warnings.append(f"Length Alert: Your resume word count is {word_count}. Highly sub-optimal. (Keep it between 200 and 1200 words).")

    # Final calculations
    final_score = round(core_score + exp_score + quality_score + format_score, 1)
    final_score = min(max(final_score, 1.0), 100.0) # range bound to 1% - 100%

    return {
        "match_percentage": final_score,
        "breakdown": {
            "core": round(core_score, 1),
            "experience": round(exp_score, 1),
            "quality": round(quality_score, 1),
            "format": round(format_score, 1)
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "coaching_tips": coaching_tips,
        "warnings": warnings
    }
