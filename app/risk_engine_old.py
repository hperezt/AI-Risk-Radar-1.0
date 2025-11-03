# app/risk_engine.py
import os
import json
from dotenv import load_dotenv
import openai  

print("DEBUG · openai version:", openai.__version__)
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = False

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en Render > Environment")

openai.api_key = API_KEY  # 👈 cambio aquí


SYSTEM = """
Comentario: Este es un ejercicio de análisis asistido por inteligencia artificial. El objetivo es evaluar cómo un modelo LLM puede colaborar con expertos humanos para identificar riesgos relevantes en proyectos ferroviarios en Alemania, tanto obvios como sistémicos. El resultado será revisado por profesionales humanos, por lo tanto, la calidad, claridad y solidez del razonamiento es más importante que la cantidad de resultados.

Actúas como un comité interdisciplinario compuesto por:
- Ingenieros especializados en planificación y ejecución de proyectos de infraestructura ferroviaria en Europa.
- Abogados expertos en derecho de infraestructura y normativa aplicable en Alemania.
- Consultores y analistas con experiencia en evaluación de riesgos en el sector ferroviario alemán.

Piensa como si estos perfiles discutieran en conjunto cada riesgo y llegaran a un consenso argumentado.

Tu tarea es leer un documento técnico relacionado con un proyecto ferroviario y detectar *riesgos de planificación* que puedan generar retrasos, sobrecostos, conflictos contractuales o fallas operativas relevantes.

Devuelve un JSON con exactamente dos listas:
- "intuitive_risks": riesgos típicos, previsibles y esperables para equipos experimentados.
- "counterintuitive_risks": riesgos inusuales, sistémicos, interdisciplinares o difíciles de anticipar.

Cada entrada debe tener esta estructura:
{
  "risk": "...",
  "justification": "...",
  "countermeasure": "...",
  "page": 42,
  "evidence": "Extracto del texto que sirvió de base"
}
"""

def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    if USE_MOCK:
        raise RuntimeError("USE_MOCK=True pero el modo estricto está activo.")
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en .env")
    if not MODEL_NAME:
        raise RuntimeError("MODEL_NAME no está definida")

    # === Sprach-Mapping (Anzeigetext für das Modell) ===
    LANG_MAP = {"de": "Deutsch", "en": "Englisch", "es": "Spanisch"}
    lang_name = LANG_MAP.get(lang, "Deutsch")

    # === System-Prompt in Zielsprache ===
    SYSTEM_BY_LANG = {
        "de": (
            "Du bist ein interdisziplinäres Fachgremium (Bauingenieurwesen, Vergabe-/Infrastrukturrecht, "
            "Risikomanagement im deutschen Schienenverkehr). Antworte ausnahmslos in Deutsch. "
            "JSON-Schlüssel bleiben englisch (risk, justification, countermeasure, page, evidence). "
            "Zitate aus dem Dokument (evidence) nicht übersetzen."
        ),
        "en": (
            "You are an interdisciplinary expert panel (rail civil engineering, procurement/infrastructure law, "
            "risk management in German rail). Respond exclusively in English. "
            "JSON keys must remain in English (risk, justification, countermeasure, page, evidence). "
            "Do not translate document quotes (evidence)."
        ),
        "es": (
            "Eres un panel interdisciplinar (ingeniería ferroviaria, derecho de infraestructura, "
            "gestión de riesgos en ferrocarriles). Responde exclusivamente en Español. "
            "Las claves JSON deben quedar en inglés (risk, justification, countermeasure, page, evidence). "
            "No traduzcas citas del documento (evidence)."
        ),
    }
    system_prompt = SYSTEM_BY_LANG.get(lang, SYSTEM_BY_LANG["de"])

    # === User-Prompt mit harter Sprachvorgabe ===
    user_prompt = f"""
Instrucción crítica / Wichtige Vorgabe / Critical instruction:
Antworte ausschließlich in {lang_name}. Keine Mischsprache. 
JSON-Keys bleiben englisch. Inhalte in {lang_name}. Zitate (evidence) unverändert lassen.

Aufgabe:
Analysiere das folgende Projektdokument (Schieneninfrastruktur) und liefere:
- 5 intuitive Risiken
- 5 kontraintuitive Risiken

Struktur jedes Eintrags:
- "risk"
- "justification"
- "countermeasure"
- "page" (falls unbekannt: schätzen oder leer lassen)
- "evidence" (originales Textzitat aus dem Dokument)

Zusätzlicher Kontext (optional):
{context}

Dokument (abgeschnitten auf 18000 Zeichen):
{text[:18000]}

Gib ausschließlich einen gültigen JSON-Objekt-Output mit genau diesen beiden Listen zurück:
- "intuitive_risks": Liste mit 5 Objekten
- "counterintuitive_risks": Liste mit 5 Objekten
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

    try:
        data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear la respuesta como JSON: {e}")

    if not isinstance(data.get("intuitive_risks"), list) or not isinstance(data.get("counterintuitive_risks"), list):
        raise ValueError("El modelo no devolvió el JSON esperado.")

    for block in data["intuitive_risks"] + data["counterintuitive_risks"]:
        if not all(k in block for k in ["risk", "justification", "countermeasure", "page", "evidence"]):
            raise ValueError("Falta una de las claves requeridas en un riesgo")

    data["source"] = "openai"
    return data

