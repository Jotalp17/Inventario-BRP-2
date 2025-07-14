import streamlit as st
import pandas as pd
import requests
from PIL import Image
import re
import base64
import io

st.set_page_config(page_title="Inventario BRP", layout="centered")
st.title("Inventario BRP 🚗")
st.markdown("Sube o toma una foto de una patente y la IA te mostrará los datos del vehículo desde el inventario.")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("Inventario_Matias_117.xlsx")
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
        text = result['responses'][0]['textAnnotations'][0]['description']
        st.markdown(f"🧠 Texto detectado por Google Cloud Vision:\n\n```\n{text}\n```")

        # Normaliza el texto
        text = text.upper().replace("CHILE", "")
        text = re.sub(r"[^A-Z0-9]", "", text)  # Elimina símbolos y espacios

        match = re.search(r"[A-Z]{2,4}[0-9]{2,4}", text)
        if match:
            return match.group(0)
        return text
    except Exception as e:
        st.error("❌ Error procesando la imagen. Intenta con otra o revisa la API Key.")
        print("Error:", e)
        return ""

# Interfaz principal
imagen = st.file_uploader("📷 Foto de la patente", type=["jpg", "jpeg", "png"])
if imagen:
    st.image(imagen, use_container_width=True)
    img = Image.open(imagen)
    patente = extraer_patente_con_google(img)
    st.markdown(f"**🔍 Patente detectada por IA:** `{patente}`")

    if patente:
        res = inventario[inventario['PPU_normalizado'] == patente]
        if not res.empty:
            st.success("✅ Vehículo encontrado:")
            st.dataframe(res)
        else:
            st.error("🚫 Patente no encontrada en el inventario.")
    else:
        st.warning("⚠️ No se detectó una patente válida. Intenta otra imagen.")
