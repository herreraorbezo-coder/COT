import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

from PIL import Image
import numpy as np
import cv2


# ========================== GOOGLE AUTH ==========================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["GOOGLE_SHEETS_CREDENTIALS"],
    scopes=scope
)

cliente = gspread.authorize(creds)
sheet = cliente.open("COT_AGUAYTIA").sheet1


# ========================== CATÁLOGO EQUIPOS ==========================
equipos = {
    "CO-11-0602A": "COMPRESOR #1",
    "CO-11-0602B": "COMPRESOR #2",
    "CO-11-0601A": "COMPRESOR #3",
    "CO-11-0601B": "COMPRESOR #4",
    "GE-28-9601A": "GENERADOR WAUKESHA #1",
    "GE-28-9601B": "GENERADOR WAUKESHA #2",
    "CR-01": "COOLER REGEN #1",
    "CR-02": "COOLER REGEN #2",
    "PU-17-0801": "PRODUCT INJECT PUMP",
    "TESAXS-12-601": "TURBOEXPANDER",
    "HESAAS-19-0601-A": "COOLER DE PRODUCTO A",
    "HESAAS-19-0601-B": "COOLER DE PRODUCTO B",
    "BH-OIL-A": "BOMBA HOT OIL A",
    "BH-OIL-B": "BOMBA HOT OIL B",
    "PU-17-0501A": "BOMBA BOOSTER A",
    "PU-17-0501B": "BOMBA BOOSTER B",
    "PU-17-0601A": "BOMBA DE FONDO A",
    "PU-17-0601B": "BOMBA DE FONDO B",
    "CO-22-6101A": "COMPRESOR AIR A",
    "CO-22-6101B": "COMPRESOR AIR B",
    "PU-17-3047A": "MOTOBOMBA CLARKE SCI A",
    "PU-17-3047B": "MOTOBOMBA CLARKE SCI B",
    "PU-17-3048": "JOCKEY CLARKE SCI PUMP",
    "PU-17-8202": "ELECTROBOMBA ACEITOSA",
    "PU-17-3802A": "BOMBA CAT A",
    "PU-17-3802B": "BOMBA CAT B",
    "PU-17-3802C": "BOMBA CAT C",
    "PU-17-3801": "BOMBA CAT 2511",
    "PU-17-3801A": "BOMBA IMBIL INI A",
    "PU-17-3801B": "BOMBA IMBIL INI B",
    "PU-17-3801C": "BOMBA INBIL C"
}


# ========================== INTERFAZ ==========================
st.set_page_config(page_title="Registro de Horas", layout="centered")
st.title("📋 Registro de Horas de Operación")

st.subheader("📷 Escanear QR del equipo")

imagen = st.camera_input("Toma una foto clara del QR del equipo")

tag = None

# ========================== DETECTOR QR CON OPENCV ==========================
if imagen is not None:
    img = Image.open(imagen)
    img_np = np.array(img)

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img_np)

    if data:
        st.success(f"QR detectado: {data}")

        # Si contiene solo TAG
        if data in equipos:
            tag = data

        # Si contiene URL con ?tag=
        elif "tag=" in data:
            tag = data.split("tag=")[-1]

    else:
        st.error("❌ No se pudo detectar ningún QR. Intenta con mejor iluminación.")


# ========================== VALIDACIÓN ==========================
if not tag:
    st.info("Escanee un QR válido para continuar")
    st.stop()

if tag not in equipos:
    st.error("TAG no reconocido en el sistema")
    st.stop()


# ========================== MOSTRAR EQUIPO ==========================
equipo = equipos[tag]

st.subheader(f"Equipo: {equipo}")
st.write(f"TAG: {tag}")


# ========================== BUSCAR ACUMULADO ==========================
registros = sheet.get_all_records()

acumulado_actual = 0
for fila in reversed(registros):
    if fila["TAG"] == tag:
        acumulado_actual = float(fila["Horas_Acumuladas"])
        break

st.info(f"⏱️ Horas acumuladas actuales: {acumulado_actual}")


# ========================== INGRESO HORAS ==========================
horas_dia = st.number_input("Horas trabajadas hoy", min_value=0.0, step=0.1)

nuevo_acumulado = acumulado_actual + horas_dia
st.write(f"➡️ Nuevo acumulado será: {nuevo_acumulado}")


# ========================== GUARDAR ==========================
if st.button("💾 Guardar registro"):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        fecha,
        tag,
        equipo,
        horas_dia,
        nuevo_acumulado
    ])

    st.success("✅ Registro guardado correctamente")

