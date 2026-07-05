def validate_word_count(text, limit=500):
    """
    Validate that text does not exceed the word limit.

    Args:
        text: The input string to validate.
        limit: Maximum number of words allowed (default 500).

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not text or not text.strip():
        return False, "Job description cannot be empty."
    words = text.strip().split()
    if len(words) > limit:
        return False, f"Job description exceeds {limit} word limit ({len(words)} words)."
    return True, "OK"


def validate_files(files, max_count=10):
    """
    Validate uploaded files: check count and PDF extension.

    Args:
        files: List of uploaded file objects from request.files.
        max_count: Maximum number of files allowed (default 10).

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not files or len(files) == 0:
        return False, "Please upload at least one PDF resume."

    if len(files) > max_count:
        return False, f"Maximum {max_count} resume files allowed. You uploaded {len(files)}."

    for file in files:
        if not file.filename:
            return False, "One of the uploaded files has no filename."
        if not file.filename.lower().endswith(".pdf"):
            return False, f"Invalid file: {file.filename}. Only PDF files are accepted."

    return True, "OK"
