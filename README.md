# AI Risk Radar – Rail Projects MVP

## Purpose
AI Risk Radar identifies intuitive and counterintuitive risks in rail infrastructure projects. This MVP is a **portfolio project** to demonstrate AI + engineering synergy, not a production tool.

## How It Works
- **Input**: Project document (PDF or text) + optional context.
- **Output**: 10 risks (5 intuitive, 5 counterintuitive) + justification + creative countermeasure.
- Displays in a **simple table** (future: risk matrix).

## Tech Stack
- Backend: FastAPI
- AI Core: GPT-4
- UI: Streamlit
- Deployment: Hugging Face Spaces

## Ethical Safeguards
- Outputs = suggestions, not truths.
- Confidence scores planned.
- No personal data.

## Install & Run
```bash
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
