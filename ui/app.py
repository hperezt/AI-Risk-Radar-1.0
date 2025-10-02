# ================================================
# 🌐 AI Risk Radar – Streamlit App (Optimized)
# ================================================

import os
import re
import random
import json
import streamlit as st
import requests
import pandas as pd
import gspread
from google.oauth2 import service_account
from translations import translations as t

# ⚙️ Configuración de página (debe ir al principio)
st.set_page_config(page_title="AI Risk Radar", layout="centered")

# ==========================
# 🌐 Config idioma
# ==========================
LANGUAGES = {"Español": "es", "English": "en", "Deutsch": "de"}
lang = st.sidebar.selectbox("🌐 Idioma / Language / Sprache", list(LANGUAGES.keys()))
lang_code = LANGUAGES[lang]

# ==========================
# 🔗 Configuración de API
# ==========================
BASE_URL = os.environ.get("API_URL", "https://ai-risk-radar-1-0-bwdu.onrender.com/")
API_URL = f"{BASE_URL}/analyze"

# ==========================
# 📂 Configuración de Google Sheets
# ==========================
SHEET_ID = os.environ.get("SHEET_ID")
GCP_CREDS = os.environ.get("GCP_CREDS")

if GCP_CREDS and SHEET_ID:
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        data = json.loads(GCP_CREDS)
        data["private_key"] = data["private_key"].replace("\\n", "\n")  # asegurar saltos de línea
        creds = service_account.Credentials.from_service_account_info(data, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        sheet = None
else:
    sheet = None

# ==========================
# 🔐 Control de acceso
# ==========================
if "authorized" not in st.session_state:
    st.session_state["authorized"] = False

if "captcha_num1" not in st.session_state:
    st.session_state["captcha_num1"] = random.randint(1, 9)
    st.session_state["captcha_num2"] = random.randint(1, 9)

if not st.session_state["authorized"]:
    st.header("🔐 Acceso a la Demo")
    email = st.text_input("📧 Ingresa tu email")
    reason = st.text_area("📝 ¿Por qué quieres probar AI Risk Radar?")
    captcha_answer = st.number_input(
        f"🔢 Resuelve: {st.session_state['captcha_num1']} + {st.session_state['captcha_num2']} = ?",
        min_value=0, step=1
    )

    if st.button("Enviar"):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("❌ Ingresa un email válido.")
        elif captcha_answer != (st.session_state["captcha_num1"] + st.session_state["captcha_num2"]):
            st.error("❌ Captcha incorrecto.")
        elif not reason.strip():
            st.error("❌ Por favor indica una razón de uso.")
        else:
            try:
                if sheet:
                    sheet.append_row([email, reason])
                st.session_state["authorized"] = True
                st.success("✅ Acceso concedido. Ahora puedes usar la demo.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"⚠️ Error al guardar en Google Sheets: {e}")

# ==========================
# 🔄 Función para mostrar riesgos
# ==========================
def render_risks(df, title, icon, lang_code):
    """Renderiza lista de riesgos con expansores y validaciones seguras"""
    if not df.empty:
        st.subheader(f"{icon} {title}")
    for _, row in df.iterrows():
        with st.expander(f"{icon} {row.get('risk', 'Riesgo sin título')}"):
            if row.get("page") or row.get("evidence"):
                st.markdown("**📄 Fuente del riesgo:**")
            if row.get("page"):
                st.markdown(f"• **Página:** {row['page']}")
            if row.get("evidence"):
                snippet = row["evidence"][:500]
                st.markdown(f"• **Fragmento del texto:**\n\n> {snippet}{'...' if len(row['evidence']) > 500 else ''}")
            st.markdown(f"**{t['columns']['justification'][lang_code]}**")
            st.write(row.get("justification", ""))
            st.markdown(f"**{t['columns']['countermeasure'][lang_code]}**")
            st.write(row.get("countermeasure", ""))

# ==========================
# 🚀 Aplicación principal
# ==========================
if st.session_state["authorized"]:
    st.title(t["app_title"][lang_code])
    st.markdown(t["file_instruction"][lang_code])

    uploaded_file = st.file_uploader(t["file_label"][lang_code], type=["txt", "pdf", "docx"])
    context = st.text_input(t["context_label"][lang_code], placeholder=t["context_placeholder"][lang_code])

    if st.button(t["analyze_button"][lang_code]):
        if not uploaded_file:
            st.warning(t["no_file_warning"][lang_code])
        else:
            with st.spinner(t["analyzing"][lang_code]):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"context": context, "lang": lang_code}
                try:
                    r = requests.post(API_URL, files=files, data=data, timeout=120)
                    r.raise_for_status()  # lanza error si no es 200

                    result = r.json()
                    st.success(t["analysis_done"][lang_code])

                    # 🟠 Riesgos intuitivos
                    df1 = pd.DataFrame(result.get("intuitive_risks", []))
                    render_risks(df1, t["intuitive_risks"][lang_code], "🔸", lang_code)

                    # 🔵 Riesgos contraintuitivos
                    df2 = pd.DataFrame(result.get("counterintuitive_risks", []))
                    render_risks(df2, t["counterintuitive_risks"][lang_code], "🔹", lang_code)

                    # 🔍 Info debug
                    dbg = result.get("_debug")
                    if dbg:
                        st.caption(f"DEBUG · chars={dbg.get('chars')} · file={dbg.get('filename')}")

                    if result.get("source") == "modo simulado (mock)":
                        st.info(t["mock_notice"][lang_code])

                except requests.exceptions.RequestException as e:
                    st.error(t["error"]["network"][lang_code] + f": {e}")
                except Exception as e:
                    st.error(f"{t['error']['default'][lang_code]}: {e}")
