from datetime import datetime
from bson import ObjectId


def upsert_user(db, user_info):
    """
    Create a new user or update their last login timestamp.

    Args:
        db: PyMongo database instance.
        user_info: Dict with keys: sub, name, email, picture.
    """
    db.users.update_one(
        {"google_id": user_info["sub"]},
        {
            "$set": {
                "name": user_info.get("name", ""),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
                "last_login": datetime.utcnow(),
            },
            "$setOnInsert": {
                "google_id": user_info["sub"],
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )


def save_analysis(db, user_id, jd_snippet, results):
    """
    Save a complete analysis report to MongoDB.

    Args:
        db: PyMongo database instance.
        user_id: Google sub (from session).
        jd_snippet: First 100 chars of job description.
        results: List of dicts: [{ filename, match_percentage, matched_skills }]

    Returns:
        str: Inserted document ID as string.
    """
    document = {
        "user_id": user_id,
        "job_description_snippet": jd_snippet,
        "total_resumes": len(results),
        "created_at": datetime.utcnow(),
        "results": results,
    }
    inserted = db.analyses.insert_one(document)
    return str(inserted.inserted_id)


def get_history(db, user_id, limit=20, page=1):
    """
    Get paginated analysis history for a user.

    Args:
        db: PyMongo database instance.
        user_id: Google sub (from session).
        limit: Number of records per page.
        page: Page number (1-indexed).

    Returns:
        dict: { total, page, history: [...] }
    """
    skip_count = (page - 1) * limit
    total = db.analyses.count_documents({"user_id": user_id})

    cursor = (
        db.analyses.find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip_count)
        .limit(limit)
    )

    records = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["analysis_id"] = doc.pop("_id")
        # Format created_at for JSON
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat() + "Z"
        # Remove user_id from response (already known)
        doc.pop("user_id", None)
        # Add top candidate summary
        if doc.get("results"):
            top = max(doc["results"], key=lambda r: r["match_percentage"])
            doc["top_candidate"] = {
                "filename": top["candidate_filename"],
                "match_percentage": top["match_percentage"],
            }
        records.append(doc)

    return {"total": total, "page": page, "history": records}


def get_analysis_by_id(db, analysis_id, user_id):
    """
    Get full details of a specific analysis.

    Args:
        db: PyMongo database instance.
        analysis_id: MongoDB ObjectId string.
        user_id: Google sub for ownership verification.

    Returns:
        tuple: (document or None, status_string)
    """
    try:
        obj_id = ObjectId(analysis_id)
    except Exception:
        return None, "invalid_id"

    doc = db.analyses.find_one({"_id": obj_id})

    if doc is None:
        return None, "not_found"

    if doc.get("user_id") != user_id:
        return None, "forbidden"

    doc["_id"] = str(doc["_id"])
    doc["analysis_id"] = doc.pop("_id")
    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat() + "Z"
    doc.pop("user_id", None)

    return doc, "ok"


def delete_analysis(db, analysis_id, user_id):
    """
    Delete a specific analysis record after verifying ownership.

    Args:
        db: PyMongo database instance.
        analysis_id: MongoDB ObjectId string.
        user_id: Google sub for ownership verification.

    Returns:
        tuple: (success: bool, status_string)
    """
    try:
        obj_id = ObjectId(analysis_id)
    except Exception:
        return False, "invalid_id"

    doc = db.analyses.find_one({"_id": obj_id})

    if doc is None:
        return False, "not_found"

    if doc.get("user_id") != user_id:
        return False, "forbidden"

    db.analyses.delete_one({"_id": obj_id})
    return True, "ok"
