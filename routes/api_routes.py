from flask import Blueprint, request, session, jsonify, current_app
from utils.validators import validate_word_count, validate_files
from utils.pdf_parser import extract_text_from_pdf
from utils.ai_engine import clean_text, calculate_match
from utils.db_service import save_analysis, get_history, get_analysis_by_id, delete_analysis

api_bp = Blueprint("api", __name__, url_prefix="/api")


def require_login(f):
    """Decorator to protect API routes — returns 401 JSON if not logged in."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({
                "status": "error",
                "error": "unauthorized",
                "message": "You must be logged in to access this resource.",
            }), 401
        return f(*args, **kwargs)

    return decorated


@api_bp.route("/analyze", methods=["POST"])
@require_login
def analyze():
    """Core endpoint: accepts JD + PDFs, runs AI matching, returns ranked results."""
    db = current_app.config["DB"]

    # --- Step 1: Get and validate job description ---
    job_description = request.form.get("job_description", "").strip()

    is_valid, msg = validate_word_count(job_description, current_app.config.get("MAX_JD_WORDS", 200))
    if not is_valid:
        error_code = "empty_job_description" if "empty" in msg.lower() else "job_description_too_long"
        return jsonify({"status": "error", "error": error_code, "message": msg}), 400

    # --- Step 2: Get and validate uploaded files ---
    files = request.files.getlist("resumes")

    is_valid, msg = validate_files(files, current_app.config.get("MAX_RESUMES", 10))
    if not is_valid:
        if "no" in msg.lower() or "at least" in msg.lower():
            error_code = "no_resumes_provided"
        elif "maximum" in msg.lower():
            error_code = "too_many_files"
        else:
            error_code = "invalid_file_type"
        return jsonify({"status": "error", "error": error_code, "message": msg}), 400

    # --- Step 3: Extract text from each PDF ---
    cleaned_jd = clean_text(job_description)
    results = []

    for file in files:
        try:
            raw_text = extract_text_from_pdf(file.stream)
            if not raw_text:
                # Skip files that couldn't be parsed
                results.append({
                    "candidate_filename": file.filename,
                    "match_percentage": 0.0,
                    "matched_skills": [],
                })
                continue

            # --- Step 4: Run AI matching ---
            cleaned_resume = clean_text(raw_text)
            match_result = calculate_match(cleaned_jd, cleaned_resume)

            results.append({
                "candidate_filename": file.filename,
                "match_percentage": match_result["match_percentage"],
                "matched_skills": match_result["matched_skills"],
            })

        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            results.append({
                "candidate_filename": file.filename,
                "match_percentage": 0.0,
                "matched_skills": [],
            })

    # --- Step 5: Sort by match percentage (highest first) and assign rank ---
    results.sort(key=lambda r: r["match_percentage"], reverse=True)
    for i, result in enumerate(results):
        result["rank"] = i + 1

    # --- Step 6: Save to MongoDB ---
    jd_snippet = job_description[:100] + ("..." if len(job_description) > 100 else "")
    try:
        analysis_id = save_analysis(db, session["user_id"], jd_snippet, results)
    except Exception as e:
        print(f"Database save error: {e}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": "Failed to save analysis results.",
        }), 500

    return jsonify({
        "status": "success",
        "analysis_id": analysis_id,
        "total_processed": len(results),
        "results": results,
    }), 200


@api_bp.route("/history", methods=["GET"])
@require_login
def history():
    """Return paginated list of past analyses for the logged-in user."""
    db = current_app.config["DB"]

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({
            "status": "error",
            "error": "invalid_page",
            "message": "Page and limit must be positive integers.",
        }), 400

    if page < 1:
        return jsonify({
            "status": "error",
            "error": "invalid_page",
            "message": "Page number must be a positive integer.",
        }), 400

    if limit < 1 or limit > 50:
        return jsonify({
            "status": "error",
            "error": "invalid_limit",
            "message": "Limit must be between 1 and 50.",
        }), 400

    result = get_history(db, session["user_id"], limit, page)
    return jsonify({"status": "success", **result}), 200


@api_bp.route("/history/<analysis_id>", methods=["GET"])
@require_login
def history_detail(analysis_id):
    """Return full details of a specific past analysis."""
    db = current_app.config["DB"]

    doc, status = get_analysis_by_id(db, analysis_id, session["user_id"])

    if status == "invalid_id":
        return jsonify({
            "status": "error", "error": "invalid_id",
            "message": "Invalid analysis ID format.",
        }), 400
    elif status == "not_found":
        return jsonify({
            "status": "error", "error": "not_found",
            "message": "Analysis not found.",
        }), 404
    elif status == "forbidden":
        return jsonify({
            "status": "error", "error": "forbidden",
            "message": "You do not have permission to view this analysis.",
        }), 403

    return jsonify({"status": "success", **doc}), 200


@api_bp.route("/history/<analysis_id>", methods=["DELETE"])
@require_login
def history_delete(analysis_id):
    """Delete a specific analysis record owned by the logged-in user."""
    db = current_app.config["DB"]

    success, status = delete_analysis(db, analysis_id, session["user_id"])

    if status == "invalid_id":
        return jsonify({
            "status": "error", "error": "invalid_id",
            "message": "Invalid analysis ID format.",
        }), 400
    elif status == "not_found":
        return jsonify({
            "status": "error", "error": "not_found",
            "message": "Analysis not found.",
        }), 404
    elif status == "forbidden":
        return jsonify({
            "status": "error", "error": "forbidden",
            "message": "You do not have permission to delete this analysis.",
        }), 403

    return jsonify({
        "status": "success",
        "message": "Analysis deleted successfully.",
    }), 200


@api_bp.route("/me", methods=["GET"])
@require_login
def me():
    """Return profile info of the currently logged-in user."""
    return jsonify({
        "status": "success",
        "user": {
            "user_id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "picture": session.get("user_pic"),
        },
    }), 200
