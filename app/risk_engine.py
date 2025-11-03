# app/risk_engine.py
import os
import json
from dotenv import load_dotenv
import openai

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = False

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en Render > Environment")

openai.api_key = API_KEY  # SDK v1: asignación directa

def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    if USE_MOCK:
        raise RuntimeError("USE_MOCK=True pero el modo estricto está activo.")

    # 🔹 Normaliza/valida lang
    lang = (lang or "es").strip().lower()
    if lang not in {"es", "en", "de"}:
        raise ValueError(f"Unsupported lang='{lang}'. Use one of: es,en,de")
    print(f"[risk_engine] lang received: {lang}")

    # 🔹 System prompt monolingüe por idioma
    SYSTEM_BY_LANG = {
        "de": (
            "Du bist ein interdisziplinäres Fachgremium für Schieneninfrastruktur. "
            "Antworte ausschließlich auf Deutsch. "
            "JSON-Schlüssel bleiben Englisch (risk, justification, countermeasure, page, evidence). "
            "Zitate im Feld 'evidence' nicht übersetzen."
        ),
        "en": (
            "You are an interdisciplinary expert panel for rail infrastructure. "
            "Respond exclusively in English. "
            "JSON keys must remain in English (risk, justification, countermeasure, page, evidence). "
            "Do not translate quotes in 'evidence'."
        ),
        "es": (
            "Eres un panel interdisciplinar de infraestructura ferroviaria. "
            "Responde exclusivamente en español. "
            "Las claves JSON deben quedar en inglés (risk, justification, countermeasure, page, evidence). "
            "No traduzcas las citas en 'evidence'."
        ),
    }
    system_prompt = SYSTEM_BY_LANG[lang]

    # 🔹 Guardrail + tarea monolingüe
    GUARD = {
        "de": "Benutze ausschließlich Deutsch (außer JSON-Schlüsseln und 'evidence').",
        "en": "Use only English (except JSON keys and 'evidence').",
        "es": "Usa solo español (salvo claves JSON y 'evidence').",
    }[lang]

    TASK = {
        "de": "Analysiere das Dokument und liefere genau 5 'intuitive_risks' und 5 'counterintuitive_risks'.",
        "en": "Analyze the document and deliver exactly 5 'intuitive_risks' and 5 'counterintuitive_risks'.",
        "es": "Analiza el documento y entrega exactamente 5 'intuitive_risks' y 5 'counterintuitive_risks'.",
    }[lang]

    STRUCT = {
        "de": 'Jeder Eintrag: "risk", "justification", "countermeasure", "page", "evidence".',
        "en": 'Each entry: "risk", "justification", "countermeasure", "page", "evidence".',
        "es": 'Cada entrada: "risk", "justification", "countermeasure", "page", "evidence".',
    }[lang]

    user_prompt = f"""{GUARD}

{TASK}
{STRUCT}

Kontext / Contexto / Context:
{context}

Dokument (gekürzt / truncado a 18000 Zeichen):
{text[:18000]}

Return ONLY a valid JSON object with exactly:
- "intuitive_risks": 5 objects
- "counterintuitive_risks": 5 objects
""".strip()

    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=3000,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear la respuesta como JSON. Raw: {content[:400]}... Error: {e}")

    # Validación de estructura
    if not isinstance(data.get("intuitive_risks"), list) or not isinstance(data.get("counterintuitive_risks"), list):
        raise ValueError("El modelo no devolvió el JSON esperado.")

    for block in data["intuitive_risks"] + data["counterintuitive_risks"]:
        if not all(k in block for k in ["risk", "justification", "countermeasure", "page", "evidence"]):
            raise ValueError("Falta una de las claves requeridas en un riesgo.")

    data["source"] = "openai"
    return data
