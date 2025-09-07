# app/services/pdf_utils.py
from typing import Optional
import io

def read_pdf_text(path: Optional[str]) -> str:
    """
    Lightweight PDF text extractor using PyPDF2.
    If path is None or unreadable, returns empty string (fail-soft).
    """
    if not path:
        return ""
    try:
        import PyPDF2
        text = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text() or ""
                text.append(t)
        return "\n".join(text)
    except Exception:
        return ""
