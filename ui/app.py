#streamlit App productive
import os
import streamlit as st
import requests
import pandas as pd
from translations import translations as t

# 🌐 Config idioma
LANGUAGES = {"Español": "es", "English": "en", "Deutsch": "de"}
lang = st.sidebar.selectbox("🌐 Idioma / Language / Sprache", list(LANGUAGES.keys()))
lang_code = LANGUAGES[lang]

# 🔗 Configuración de API (usa variable de entorno en Render o local por defecto)
BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
API_URL = f"{BASE_URL}/analyze"


# ⚙️ Config app
st.set_page_config(page_title="AI Risk Radar", layout="centered")
st.title(t["app_title"][lang_code])
st.markdown(t["file_instruction"][lang_code])

# 📂 Carga de archivos y contexto
uploaded_file = st.file_uploader(t["file_label"][lang_code], type=["txt", "pdf", "docx"])
context = st.text_input(t["context_label"][lang_code], placeholder=t["context_placeholder"][lang_code])

# ▶️ Botón de análisis
if st.button(t["analyze_button"][lang_code]):
    if not uploaded_file:
        st.warning(t["no_file_warning"][lang_code])
    else:
        with st.spinner(t["analyzing"][lang_code]):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"context": context, "lang": lang_code}
            try:
                r = requests.post(API_URL, files=files, data=data, timeout=120)

                if r.status_code != 200:
                    try:
                        payload = r.json()
                    except Exception:
                        payload = {"message": r.text}
                    status = r.status_code
                    err_code = payload.get("error_code", "")
                    err_msg = payload.get("message") or payload.get("error") or str(payload)
                    st.error(f"HTTP {status}"
                             + (f" · {err_code}" if err_code else "")
                             + f": {err_msg}")
                    st.stop()

                result = r.json()
                st.success(t["analysis_done"][lang_code])

                # 🟠 Riesgos intuitivos
                df1 = pd.DataFrame(result.get("intuitive_risks", []))
                if not df1.empty:
                    st.subheader("⚠️ " + t["intuitive_risks"][lang_code])
                for i, row in df1.iterrows():
                    with st.expander(f"🔸 {row['risk']}"):
                        if "page" in row or "evidence" in row:
                            st.markdown("**📄 Fuente del riesgo:**")
                        if "page" in row:
                            st.markdown(f"• **Página:** {row['page']}")
                        if "evidence" in row:
                            st.markdown(f"• **Fragmento del texto:**\n\n> {row['evidence'][:500]}{'...' if len(row['evidence']) > 500 else ''}")
                        st.markdown(f"**{t['columns']['justification'][lang_code]}**")
                        st.write(row['justification'])
                        st.markdown(f"**{t['columns']['countermeasure'][lang_code]}**")
                        st.write(row['countermeasure'])

                # 🔵 Riesgos contraintuitivos
                df2 = pd.DataFrame(result.get("counterintuitive_risks", []))
                if not df2.empty:
                    st.subheader("💡 " + t["counterintuitive_risks"][lang_code])
                for i, row in df2.iterrows():
                    with st.expander(f"🔹 {row['risk']}"):
                        if "page" in row or "evidence" in row:
                            st.markdown("**📄 Fuente del riesgo:**")
                        if "page" in row:
                            st.markdown(f"• **Página:** {row['page']}")
                        if "evidence" in row:
                            st.markdown(f"• **Fragmento del texto:**\n\n> {row['evidence'][:500]}{'...' if len(row['evidence']) > 500 else ''}")
                        st.markdown(f"**{t['columns']['justification'][lang_code]}**")
                        st.write(row['justification'])
                        st.markdown(f"**{t['columns']['countermeasure'][lang_code]}**")
                        st.write(row['countermeasure'])

                # 🔍 Info debug
                dbg = result.get("_debug")
                if dbg:
                    st.caption(f"DEBUG · chars={dbg.get('chars')} · file={dbg.get('filename')}")

                if result.get("source") == "modo simulado (mock)":
                    st.info(t["mock_notice"][lang_code])

            except Exception as e:
                st.error(f"{t['error']['default'][lang_code]}: {e}")
