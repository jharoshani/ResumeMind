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


def calculate_match(jd_text, resume_text):
    """
    Calculate the match percentage and extract matched skills between
    a job description and a resume using TF-IDF and cosine similarity.

    Args:
        jd_text: Cleaned job description text.
        resume_text: Cleaned resume text.

    Returns:
        dict: {
            "match_percentage": float (0.0 to 100.0),
            "matched_skills": list of lowercase strings
        }
    """
    # Handle edge case: empty inputs
    if not jd_text or not resume_text:
        return {"match_percentage": 0.0, "matched_skills": []}

    try:
        # Step 1: Create TF-IDF vectors, ignoring common English stop words
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([jd_text, resume_text])

        # Step 2: Get the list of meaningful words discovered across both texts
        feature_names = vectorizer.get_feature_names_out()

        # Step 3: Convert sparse matrix rows to dense arrays
        jd_vector = tfidf_matrix[0].toarray()[0]
        resume_vector = tfidf_matrix[1].toarray()[0]

        # Step 4: Calculate cosine similarity and convert to percentage
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        match_percentage = round(float(similarity[0][0]) * 100, 1)

        # Step 5: Find matched skills — words with non-zero weight in BOTH documents
        matched_indices = np.where((jd_vector > 0) & (resume_vector > 0))[0]
        matched_skills = sorted([feature_names[i] for i in matched_indices])

        return {
            "match_percentage": match_percentage,
            "matched_skills": matched_skills,
        }

    except Exception:
        return {"match_percentage": 0.0, "matched_skills": []}
