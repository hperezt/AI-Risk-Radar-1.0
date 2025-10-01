# app/risk_engine.py
import os
import json
from dotenv import load_dotenv
import openai

# Cargar variables de entorno (.env o Render Environment)
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = False

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en Render > Environment")

# Configurar API Key para cliente viejo (openai<=0.28.0)
openai.api_key = API_KEY


def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    """
    Genera riesgos a partir del texto de un documento usando GPT.
    Devuelve un JSON con riesgos intuitivos y contraintuitivos.
    """
    if USE_MOCK:
        return {
            "intuitive_risks": [
                {"risk": "Retraso por clima", "justification": "Condiciones adversas", "countermeasure": "Plan de contingencia", "page": 1, "evidence": "Clima en zona de obra"},
            ],
            "counterintuitive_risks": [
                {"risk": "Exceso de presupuesto por ahorro mal planificado", "justification": "Decisiones apresuradas", "countermeasure": "Revisión independiente", "page": 2, "evidence": "Reportes financieros"},
            ],
        }

    prompt = f"""
Idioma de salida: {lang}

Analiza el siguiente documento de proyecto de infraestructura y genera:
- 5 riesgos intuitivos
- 5 riesgos contraintuitivos

Documento (truncado a 18000 caracteres):
{text[:18000]}

Contexto adicional:
{context}

Devuelve solo un JSON válido con:
- "intuitive_risks": lista de 5 objetos
- "counterintuitive_risks": lista de 5 objetos
Cada objeto debe incluir:
- "risk"
- "justification"
- "countermeasure"
- "page"
- "evidence"
"""

    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Eres un analista de riesgos experto en proyectos de infraestructura.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    try:
        data = json.loads(response["choices"][0]["message"]["content"])
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear JSON: {e}")

    return data

