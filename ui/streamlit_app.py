#streamlit demo
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="AI Risk Radar", layout="centered")

# Título y descripción
st.title("📊 AI Risk Radar")
st.write("Upload your project document to analyze potential infrastructure risks. (Feature coming soon)")

# Carga de archivos
uploaded_file = st.file_uploader("📄 Choose a file", type=["pdf", "docx", "txt"])

if uploaded_file:
    st.success(f"✅ File `{uploaded_file.name}` uploaded successfully!")
    st.info("⏳ Analyzing risks... (This feature is under development)")
