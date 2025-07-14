import streamlit as st
import pandas as pd
import requests
from PIL import Image
import re
import base64
import io
from fpdf import FPDF
from datetime import datetime
import os

st.set_page_config(page_title="Inventario BRP", layout="centered")
st.title("Inventario BRP 🚗")
st.markdown("Sube o toma una foto de una patente o ingrésala manualmente. La IA te mostrará los datos del vehículo desde el inventario y te permitirá generar una ficha PDF.")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("Inventario_Matias_117.xlsx", sheet_name="INVENTARIO")
    df['PPU_normalizado'] = df['PPU'].astype(str).str.replace(r"[^A-Z0-9]", "", regex=True).str.upper()
    return df

inventario = cargar_datos()

def extraer_patente_con_google(imagen):
    buffered = io.BytesIO()
    imagen.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    api_key = "AIzaSyAiZrflsHlZuXg9nt_uIEwKGz6qeAwWw78"
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

    body = {
        "requests": [
            {
                "image": {"content": img_base64},
                "features": [{"type": "TEXT_DETECTION"}]
            }
        ]
    }

    response = requests.post(url, json=body)
    result = response.json()

    try:
        texto_detectado = result['responses'][0]['textAnnotations'][0]['description']
        st.markdown("### 🧠 Texto detectado por Google Cloud Vision:")
        st.code(texto_detectado)
        texto_normalizado = texto_detectado.upper().replace(" ", "").replace("-", "").replace("·", "").replace("°", "")
        match = re.search(r"[A-Z]{2,4}[0-9]{2,4}", texto_normalizado)
        return match.group(0) if match else texto_normalizado
    except Exception as e:
        st.error(f"❌ Error procesando la imagen. Intenta con otra o revisa la API Key.\n\n{e}")
        return ""

def generar_pdf(data):
    fila = data.iloc[0]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Logo
    logo_path = "Tanner Original.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=35)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 70, 140)
    pdf.cell(0, 10, "Ficha Vehículo BRP", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)

    for campo in fila.index:
        if campo == 'PPU_normalizado':
            continue
        valor = str(fila[campo])
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 8, f"{campo}:", border=0)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, valor)

    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="R")

    output = f"Ficha_{fila['PPU']}.pdf"
    pdf.output(output)
    return output

# Interfaz principal
opcion = st.radio("Selecciona cómo deseas ingresar la patente:", ["Subir imagen", "Ingresar manualmente"])
patente = ""
if opcion == "Subir imagen":
    imagen = st.file_uploader("📷 Foto de la patente", type=["jpg", "jpeg", "png"])
    if imagen:
        st.image(imagen, use_container_width=True)
        img = Image.open(imagen)
        patente = extraer_patente_con_google(img)
elif opcion == "Ingresar manualmente":
    entrada_manual = st.text_input("✍️ Ingresa la patente del vehículo")
    if entrada_manual:
        patente = re.sub(r"[^A-Z0-9]", "", entrada_manual.upper())

if patente:
    st.markdown(f"### 🔍 Patente detectada por IA: `{patente}`")
    res = inventario[inventario['PPU_normalizado'] == patente]
    if not res.empty:
        st.success("✅ Vehículo encontrado:")
        st.dataframe(res)
        if st.button("📄 Generar Ficha PDF"):
            ruta_pdf = generar_pdf(res)
            with open(ruta_pdf, "rb") as f:
                st.download_button("⬇️ Descargar Ficha PDF", f, file_name=ruta_pdf, mime="application/pdf")
            st.success("PDF generado correctamente.")
    else:
        st.error("🚫 Patente no encontrada en el inventario.")
