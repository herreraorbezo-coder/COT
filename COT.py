import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# =============================================================================
#                               GOOGLE AUTH
# =============================================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["GOOGLE_SHEETS_CREDENTIALS"],
    scopes=scope
)

# Google Sheets
cliente = gspread.authorize(creds)
sheet = cliente.open("COT_AGUAYTIA").sheet1  # Nombre EXACTO del Sheet

# Google Drive
gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

# ID de la carpeta de Drive donde se guardan los AST
AST_FOLDER_ID = "1PhQg9p6NL4C6WYVSPIKB4P_vmLZbUYHn"


# =============================================================================
#                               STREAMLIT CONFIG
# =============================================================================
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")


# =============================================================================
#                               DATA TEMPORAL
# =============================================================================
if "registros" not in st.session_state:
    st.session_state.registros = pd.DataFrame()

# =============================================================================
#                               AREAS
# =============================================================================
areas = {
    "PRODUCCION": ["BREYSON TALLEDO", "MIGUEL CRUZ"],
    "MANTENIMIENTO": ["NILTON HINOSTROZA", "GUSTAVO VASQUEZ"],
    "E&IC": ["OMAR CAYLLAHUA", "MAURO BENAVENTE", "DAWI TORRES"],
    "ADMINISTRACION": ["ENRIQUE ESPINOZA", "LUCIO ZEVALLOS"],
    "EHS": ["JOSE BENDEZU", "JACKER RUIZ", "MARCO ALVARADO"]
}

menu = st.tabs(["📋 Registrar Actividad", "📊 Dashboard / KPIs"])


# =============================================================================
#                               TAB REGISTRO
# =============================================================================
with menu[0]:

    st.subheader("DATOS GENERALES")

    area = st.selectbox("ÁREA", list(areas.keys()))
    supervisor = st.selectbox("SUPERVISOR", areas[area])

    with st.form("formulario_cot", clear_on_submit=True):

        descripcion = st.text_area("DESCRIPCIÓN DE LA ACTIVIDAD *")
        col1, col2 = st.columns(2)

        with col1:
            supervisor_trabajo = st.text_input("SUPERVISOR DE TRABAJO *")
        with col2:
            dueno_area = st.text_input("DUEÑO DE ÁREA *")

        archivo = st.file_uploader(
            "Adjuntar AST / Evidencia",
            type=["pdf", "xlsx", "xls", "docx"]
        )

        enviar = st.form_submit_button("GUARDAR REGISTRO")

    if enviar:
        if descripcion.strip() == "" or supervisor_trabajo.strip() == "" or dueno_area.strip() == "":
            st.error("⚠️ Complete todos los campos obligatorios.")
        else:
            fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ---------------- SUBIR AST A DRIVE ----------------
            ast_link = "No adjuntado"

            if archivo is not None:
                gfile = drive.CreateFile({
                    "title": archivo.name,
                    "parents": [{"id": AST_FOLDER_ID}]
                })
                gfile.SetContentBinary(archivo.getvalue())
                gfile.Upload()

                gfile.InsertPermission({
                    "type": "anyone",
                    "role": "reader"
                })

                ast_link = f"https://drive.google.com/file/d/{gfile['id']}/view"

            # ---------------- GUARDAR EN GOOGLE SHEETS ----------------
            sheet.append_row([
                fecha_registro,
                area,
                supervisor,
                descripcion,
                supervisor_trabajo,
                dueno_area,
                ast_link
            ])

            st.success("Registro guardado correctamente.")
            st.write("🔗 Link AST:", ast_link)


# =============================================================================
#                               TAB DASHBOARD
# =============================================================================
with menu[1]:

    st.subheader("📊 KPIs y Gráficas del COT")

    data = sheet.get_all_records()

    if len(data) == 0:
        st.info("Aún no hay registros.")
    else:
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        df["Fecha"] = pd.to_datetime(
            df["Fecha de Registro"],
            errors="coerce"
        ).dt.date

        # KPIs
        colk1, colk2, colk3 = st.columns(3)
        colk1.metric("Total Registros", len(df))
        colk2.metric("Áreas", df["Área"].nunique())
        colk3.metric("Supervisores", df["Supervisor Área"].nunique())

        st.markdown("---")

        # Tendencia
        trend = df.groupby("Fecha").size().reset_index(name="Cantidad")
        st.plotly_chart(
            px.line(trend, x="Fecha", y="Cantidad", markers=True),
            use_container_width=True
        )

        st.markdown("---")

        # Por área
        area_count = df["Área"].value_counts().reset_index()
        area_count.columns = ["Área", "Cantidad"]
        st.plotly_chart(
            px.bar(area_count, x="Área", y="Cantidad", text="Cantidad"),
            use_container_width=True
        )

        st.markdown("---")

        # Ranking supervisores
        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]
        st.plotly_chart(
            px.bar(sup_count, x="Supervisor", y="Cantidad", text="Cantidad"),
            use_container_width=True
        )





