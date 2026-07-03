import pdfplumber


def extract_text_from_pdf(file_stream):
    """
    Extract all text content from a PDF file stream.

    Args:
        file_stream: A binary file-like object (e.g., from request.files)

    Returns:
        str: All extracted text concatenated, or empty string on failure.
    """
    try:
        all_text = ""
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
        return all_text.strip()
    except Exception:
        return ""
