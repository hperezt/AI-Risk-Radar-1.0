def extract_text_from_pdf(file_bytes) -> list[dict]:
    import pdfplumber
    from io import BytesIO
    import re

    bio = BytesIO(file_bytes)
    page_texts = []

    with pdfplumber.open(bio) as pdf:
        MAX_PAGES = 100
        for i, page in enumerate(pdf.pages):
            if i >= MAX_PAGES:
                break
            text = page.extract_text(x_tolerance=1.5, y_tolerance=1.5) or ""
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            page_texts.append({"page": i + 1, "text": text})

    return page_texts
