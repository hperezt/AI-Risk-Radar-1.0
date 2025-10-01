# app/parsers.py
from io import BytesIO
from typing import Union, List, Dict
import re

# 1) PDF: usa pdfplumber
def extract_text_from_pdf(file_bytes: Union[bytes, BytesIO]) -> List[Dict]:
    """
    Devuelve una lista de dicts: { "page": n, "text": "..." }
    Útil para trazabilidad de riesgos por página.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Falta pdfplumber. Instala con: pip install pdfplumber")

    bio = BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    pages = []

    with pdfplumber.open(bio) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text(x_tolerance=1.5, y_tolerance=1.5) or ""
            page_text = re.sub(r"[ \t]+", " ", page_text)
            page_text = re.sub(r"\n{3,}", "\n\n", page_text).strip()
            pages.append({"page": i + 1, "text": page_text})

    return pages


# 2) DOCX
def extract_text_from_docx(file_bytes: Union[bytes, BytesIO]) -> str:
    """
    Extrae texto plano de documentos .docx (Word).
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("Falta python-docx. Instala con: pip install python-docx")

    bio = BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes
    doc = Document(bio)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


# 3) TXT
def extract_text_from_txt(file_bytes: Union[bytes, BytesIO]) -> str:
    """
    Extrae texto de archivos planos .txt codificados como UTF-8.
    """
    if not isinstance(file_bytes, bytes):
        file_bytes = file_bytes.read()

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="ignore")

    # Debug en logs de Render
    print(f"DEBUG · TXT length={len(text)} preview={text[:200]!r}")

    return text

