import streamlit as st
import pandas as pd
import requests
from PIL import Image
import re
import base64
import io
from fpdf import FPDF
import os

st.set_page_config(page_title="Inventario BRP", layout="centered")
st.title("Inventario BRP 🚗")
st.markdown("Sube o toma una foto de una patente o ingrésala manualmente. La IA te mostrará los datos del vehículo desde el inventario y generará una ficha PDF.")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("Inventario_Matias_117.xlsx", sheet_name="INVENTARIO")
    df['PPU_normalizado'] = df['PPU'].astype(str).str.replace(r"[^A-Z0-9]", "", regex=True).str.upper()
    return df

inventario = cargar_datos()

columnas_mostrar = [
    "PPU", "N°OP", "Bodega", "Ciudad", "Region", "Ubicación Específica", "Observación Unidad", "Marca", "Modelo", "Año", "Tipo Vehículo", "Giro", "Estado", "Venta", "Canal de Venta", "Estado Mecánico", "Costo Reparación", "Gasto Reparación", "Precio mercado", "Kms", "Transmisión", "Combustible", "Chasis", "Motor", "Color", "Versión", "Fecha Dación", "Fecha Ingreso BRP", "Fecha Inicio Venta", "Dias Stock liberado", "Valor Economico", "Precio Publicación Actual", "Valor Excelente Condición", "Valor Buena Condición", "Valor Regular Condición", "Valor Mala Condición", "Valor Autored", "Proyección Macal", "Categoría Vehiculo", "Origen", "MUNI PERMISO", "VALOR PERMISO", "FECHA VENC PERMISO", "FECHA VENC RT", "FECHA VENC SOAP", "NUMERO MULTAS", "TOTAL REGULARIZACIÓN", "Dias Liberación", "Fecha Liberación", "Avance RC"
]

# OCR con Google Cloud Vision
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

# Crear ficha PDF
class FichaVehiculoPDF(FPDF):
    def header(self):
        if os.path.exists("Tanner Original.png"):
            self.image("Tanner Original.png", 10, 8, 50)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Ficha del Vehículo", ln=True, align="C")
        self.ln(10)

    def add_info(self, data):
        self.set_font("Arial", size=10)
        for campo, valor in data.items():
            self.cell(60, 8, str(campo), border=1)
            self.cell(0, 8, str(valor), border=1, ln=True)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

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
        st.dataframe(res[columnas_mostrar], use_container_width=True)

        # Generar PDF
        datos_dict = res[columnas_mostrar].iloc[0].to_dict()
        pdf = FichaVehiculoPDF()
        pdf.add_page()
        pdf.add_info(datos_dict)

        output = io.BytesIO()
        pdf.output(output)
        pdf_bytes = output.getvalue()

        st.download_button(
            label="📄 Descargar ficha PDF",
            data=pdf_bytes,
            file_name=f"Ficha_{patente}.pdf",
            mime="application/pdf"
        )

        st.markdown("---")
        st.markdown("### 📄 Vista previa del PDF:")
        st.download_button("⬇️ Descargar PDF", data=pdf_bytes, file_name=f"Ficha_{patente}.pdf", mime="application/pdf")
        st.pdf(pdf_bytes)

    else:
        st.error("🚫 Patente no encontrada en el inventario.")
