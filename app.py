import streamlit as st
import pandas as pd
import requests
from PIL import Image
import re
import base64
import io
from fpdf import FPDF

st.set_page_config(page_title="Inventario BRP", layout="centered")
st.title("Inventario BRP 🚗")
st.markdown("Sube o toma una foto de una patente o ingrésala manualmente. La IA te mostrará los datos del vehículo desde el inventario y podrás generar su ficha PDF.")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("Inventario_Matias_117.xlsx", sheet_name="INVENTARIO")
    df['PPU_normalizado'] = df['PPU'].astype(str).str.replace(r"[^A-Z0-9]", "", regex=True).str.upper()
    return df

inventario = cargar_datos()

columnas_deseadas = [
    "PPU", "N°OP", "Bodega", "Ciudad", "Region", "Ubicación Específica", "Observación Unidad",
    "Marca", "Modelo", "Año", "Tipo Vehículo", "Giro", "Estado", "Venta", "Canal de Venta",
    "Estado Mecánico", "Costo Reparación", "Gasto Reparación", "Precio mercado", "Kms", "Transmisión",
    "Combustible", "Chasis", "Motor", "Color", "Versión", "Fecha Dación", "Fecha Ingreso BRP",
    "Fecha Inicio Venta", "Dias Stock liberado", "Valor Economico", "Precio Publicación Actual",
    "Valor Excelente Condición", "Valor Buena Condición", "Valor Regular Condición", "Valor Mala Condición",
    "Valor Autored", "Proyección Macal", "Categoría Vehiculo", "Origen", "MUNI PERMISO", "VALOR PERMISO",
    "FECHA VENC PERMISO", "FECHA VENC RT", "FECHA VENC SOAP", "NUMERO MULTAS", "TOTAL REGULARIZACIÓN",
    "Dias Liberación", "Fecha Liberación", "Avance RC"
]

# Función OCR con Google Vision
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
        if match:
            return match.group(0)
        return texto_normalizado
    except Exception as e:
        st.error(f"❌ Error procesando la imagen. Intenta con otra o revisa la API Key.\n\n{e}")
        return ""

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

# Búsqueda
if patente:
    st.markdown(f"### 🔍 Patente detectada por IA: `{patente}`")
    res = inventario[inventario['PPU_normalizado'] == patente]
    if not res.empty:
        st.success("✅ Vehículo encontrado:")
        st.dataframe(res[columnas_deseadas], use_container_width=True)

        # Crear PDF
        vehiculo = res[columnas_deseadas]
        output = io.BytesIO()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Logo
        try:
            pdf.image("Tanner Original.png", x=10, y=8, w=50)
        except:
            pass

        pdf.ln(30)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Ficha Vehículo: {patente}", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=11)
        for col in columnas_deseadas:
            valor = str(vehiculo.iloc[0][col])
            pdf.cell(60, 10, f"{col}:", border=0)
            pdf.multi_cell(0, 10, valor)

        pdf_bytes = pdf.output(dest='S').encode('latin1')
        output.write(pdf_bytes)
        output.seek(0)

        # Mostrar botones
        st.download_button("📥 Descargar ficha PDF", data=output, file_name=f"{patente}_ficha.pdf", mime="application/pdf")
        st.markdown("### 📄 Vista previa de la ficha:")
        st.download_button("📥 Descargar nuevamente", data=output, file_name=f"{patente}_ficha.pdf", mime="application/pdf", key="dl2")
    else:
        st.error("🚫 Patente no encontrada en el inventario.")
