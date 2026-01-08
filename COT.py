import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# ========================== GOOGLE AUTH ==========================
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
sheet = cliente.open("COT_AGUAYTIA").sheet1

# Google Drive
gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

AST_FOLDER_ID = "1PhQg9p6NL4C6WYVSPIKB4P_vmLZbUYHn"


# ========================== CONFIG STREAMLIT ==========================
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")


# ========================== BASE TEMPORAL ==========================
if "registros" not in st.session_state:
    st.session_state.registros = pd.DataFrame(columns=[
        "Fecha Registro",
        "Área",
        "Supervisor Área",
        "Descripción Actividad",
        "Supervisor de Trabajo",
        "Dueño de Área",
        "Archivo ATS"
    ])

if "archivos" not in st.session_state:
    st.session_state.archivos = []


# ========================== AREAS ==========================
areas = {
    "PRODUCCION": ["BREYSON TALLEDO", "MIGUEL CRUZ"],
    "MANTENIMIENTO": ["NILTON HINOSTROZA", "GUSTAVO VASQUEZ"],
    "E&IC": ["OMAR CAYLLAHUA", "MAURO BENAVENTE", "DAWI TORRES"],
    "ADMINISTRACION": ["ENRIQUE ESPINOZA", "LUCIO ZEVALLOS"],
    "EHS": ["JOSE BENDEZU", "JACKER RUIZ", "MARCO ALVARADO"]
}

menu = st.tabs(["📋 Registrar Actividad", "📊 Dashboard / KPIs"])


# ====================================================================================
#                               TAB REGISTRO
# ====================================================================================
with menu[0]:

    st.subheader("DATOS GENERALES")

    area = st.selectbox("ÁREA", list(areas.keys()))
    supervisor = st.selectbox("SUPERVISOR", areas[area])

    with st.form("formulario_cot", clear_on_submit=True):

        st.subheader("DATOS DE LA ACTIVIDAD")

        descripcion = st.text_area("DESCRIPCIÓN DE LA ACTIVIDAD * (Obligatorio)")

        col3, col4 = st.columns(2)
        with col3:
            supervisor_trabajo = st.text_input("SUPERVISOR DE TRABAJO * (Obligatorio)")
        with col4:
            dueno_area = st.text_input("DUEÑO DE ÁREA * (Obligatorio)")

        archivo = st.file_uploader(
            "Adjuntar ATS / Evidencia (Opcional)",
            type=["xlsx", "xls", "pdf", "docx"]
        )

        enviar = st.form_submit_button("GUARDAR REGISTRO")

    if enviar:

        if descripcion.strip() == "" or supervisor_trabajo.strip() == "" or dueno_area.strip() == "":
            st.error("⚠️ No puedes registrar. Hay campos obligatorios vacíos.")
        else:
            fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ========================== SUBIR AST A DRIVE ==========================
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

            # ========================== GUARDAR EN GOOGLE SHEETS ==========================
            sheet.append_row([
                fecha_registro,
                area,
                supervisor,
                descripcion,
                supervisor_trabajo,
                dueno_area,
                ast_link
            ])

            st.success("Registro almacenado correctamente.")
            st.write("LINK AST:", ast_link)


# ====================================================================================
#                               TAB DASHBOARD
# ====================================================================================
with menu[1]:

    st.subheader("📊 KPIs y Gráficas del COT")

    data = sheet.get_all_records()

    if len(data) == 0:
        st.info("Aún no hay registros para mostrar KPIs.")
    else:
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        df["Fecha"] = pd.to_datetime(
            df["Fecha de Registro"],
            errors="coerce"
        ).dt.date

        # ------------------- KPI PRINCIPALES -------------------
        colk1, colk2, colk3 = st.columns(3)
        colk1.metric("Total de Registros", len(df))
        colk2.metric("Áreas Reportando", df["Área"].nunique())
        colk3.metric("Supervisores Participando", df["Supervisor Área"].nunique())

        st.markdown("---")

        # ------------------- Tendencia -------------------
        st.subheader("📈 Tendencia de registros en el tiempo")
        trend = df.groupby("Fecha").size().reset_index(name="Cantidad")
        st.plotly_chart(
            px.line(trend, x="Fecha", y="Cantidad", markers=True),
            use_container_width=True
        )

        st.markdown("---")

        # ------------------- Participación por Área -------------------
        st.subheader("🏆 Participación por Área")
        area_count = df["Área"].value_counts().reset_index()
        area_count.columns = ["Área", "Cantidad"]

        st.plotly_chart(
            px.bar(area_count, x="Área", y="Cantidad", text="Cantidad", color="Cantidad"),
            use_container_width=True
        )

        st.markdown("---")

        # ------------------- Ranking Supervisores -------------------
        st.subheader("👤 Ranking de Supervisores")
        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]

        st.plotly_chart(
            px.bar(sup_count, x="Supervisor", y="Cantidad", text="Cantidad", color="Cantidad"),
            use_container_width=True
        )

        st.markdown("---")

        # ------------------- Heatmap -------------------
        st.subheader("🔥 Mapa de Participación por Día y Área")
        heat = df.groupby(["Fecha", "Área"]).size().reset_index(name="Cantidad")
        st.plotly_chart(
            px.density_heatmap(
                heat,
                x="Fecha",
                y="Área",
                z="Cantidad",
                color_continuous_scale="Blues"
            ),
            use_container_width=True
        )

        st.markdown("---")

        # ------------------- Cumplimiento -------------------
        st.subheader("🎯 % Cumplimiento de Meta")
        meta = st.slider("Meta mínima diaria de registros:", 1, 50, 5)

        cumplimiento = []
        for _, total in trend.values:
            cumplimiento.append(min(100, int((total / meta) * 100)))

        avg_cumplimiento = int(sum(cumplimiento) / len(cumplimiento))

        if avg_cumplimiento >= 90:
            st.success(f"Cumplimiento promedio: {avg_cumplimiento}%")
        elif avg_cumplimiento >= 60:
            st.warning(f"Cumplimiento promedio: {avg_cumplimiento}%")
        else:
            st.error(f"Cumplimiento promedio: {avg_cumplimiento}%")
