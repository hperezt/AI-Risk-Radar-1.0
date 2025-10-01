# app/main.py
import logging
import traceback
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse

from app.parsers import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
)
from app.risk_engine import generate_risks

logger = logging.getLogger("uvicorn.error")
app = FastAPI(debug=True)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "AI Risk Radar API is running"}

@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    context: str = Form(""),
    lang: str = Form("es"),
):
    try:
        filename = (file.filename or "").lower()
        file_bytes = await file.read()

        # Detectar tipo por extensión y procesar
        if filename.endswith(".pdf"):
            text_per_page = extract_text_from_pdf(file_bytes)
            joined_text = "\n---\n".join([f"[Página {p['page']}]\n{p['text']}" for p in text_per_page])
        elif filename.endswith(".docx"):
            joined_text = extract_text_from_docx(file_bytes)
        elif filename.endswith(".txt"):
            joined_text = extract_text_from_txt(file_bytes)
        else:
            return JSONResponse(
                content={
                    "error_code": "unsupported_format",
                    "message": "Formato no soportado (usa .txt, .pdf o .docx)",
                },
                status_code=400,
            )

        # Validación mínima para detectar parser vacío
        if not joined_text or len(joined_text) < 100:
            return JSONResponse(
                content={
                    "error_code": "empty_or_too_short",
                    "message": "El archivo se leyó vacío o muy corto. Revisa el parser o prueba otro archivo.",
                },
                status_code=422,
            )

        # Generar riesgos con GPT
        result = generate_risks(joined_text, context=context, lang=lang)

        # Añadir metadatos internos para debugging
        result["_debug"] = {
            "filename": filename,
            "chars": len(joined_text),
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error en /analyze: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "error_code": "internal_error",
                "message": str(e),
            },
            status_code=500,
        )
