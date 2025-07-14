import streamlit as st
import pandas as pd
import requests
from PIL import Image
import re
import base64
import io

# Configuración de la app
st.set_page_config(page_title="Inventario BRP", layout="centered")
st.title("Inventario BRP 🚗")
st.markdown("Sube o toma una foto de una patente y la IA te mostrará los datos del vehículo desde el inventario.")

# Cargar Excel y normalizar patentes
@st.cache_data
def cargar_datos():
    df = pd.read_excel("Inventario_Matias_117.xlsx")
    df['PPU_normalizado'] = df['PPU'].astype(str).str.replace(r"[^A-Z0-9]", "", regex=True).str.upper()
    return df

inventario = cargar_datos()

# Función para usar Google Cloud Vision OCR
def extraer_patente_con_google(imagen):
    buffered = io.BytesIO()
    imagen.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    api_key = "AIzaSyAc_KWGN1xPCS0PGTNZEi-LoAFEbdyXREI"
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

    body = {
        "requests": [
            {
                "image": {
                    "content": img_base64
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    }

    response = requests.post(url, json=body)
    result = response.json()

    try:
        st.write("🧠 **Texto detectado por Google Cloud Vision:**")
        st.json(result)  # Muestra el OCR completo para debug

        text = result['responses'][0]['textAnnotations'][0]['description']
        text = text.upper().replace(" ", "").replace("-", "").replace("·", "")
        text = re.sub(r"[^A-Z0-9]", "", text)

        posibles_patentes = re.findall(r"[A-Z]{2,4}[0-9]{2,4}", text)
        if posibles_patentes:
            return posibles_patentes[0]
        return text
    except Exception as e:
        st.error("❌ Error procesando la imagen. Intenta con otra o revisa la API Key.")
        print("Error al extraer texto:", e)
        return ""

# Interfaz principal
imagen = st.file_uploader("📷 Foto de la patente", type=["jpg", "jpeg", "png"])
if imagen:
    st.image(imagen, use_container_width=True)
    img = Image.open(imagen)
    patente = extraer_patente_con_google(img)
    st.markdown(f"**Patente detectada por IA:** `{patente}`")

    if patente:
        res = inventario[inventario['PPU_normalizado'] == patente]
        if not res.empty:
            st.success("✅ Vehículo encontrado:")
            st.dataframe(res)
        else:
            st.error("🚫 Patente no encontrada en el inventario.")
    else:
        st.warning("⚠️ No se detectó una patente válida. Intenta otra imagen.")
