import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io


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
drive_service = build("drive", "v3", credentials=creds)

AST_FOLDER_ID = "1PhQg9p6NL4C6WYVSPIKB4P_vmLZbUYHn"


# ========================== CONFIG STREAMLIT ==========================
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")


# ========================== BASE TEMPORAL PARA DASHBOARD ==========================
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

    if "area" not in st.session_state:
        st.session_state.area = "PRODUCCION"

    st.session_state.area = st.selectbox("ÁREA", list(areas.keys()))

    with st.form("formulario_cot", clear_on_submit=True):

        supervisor = st.selectbox("SUPERVISOR", areas[st.session_state.area])

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

            nuevo_registro = {
                "Fecha Registro": fecha_registro,
                "Área": st.session_state.area,
                "Supervisor Área": supervisor,
                "Descripción Actividad": descripcion,
                "Supervisor de Trabajo": supervisor_trabajo,
                "Dueño de Área": dueno_area,
                "Archivo ATS": archivo.name if archivo else "No adjuntado"
            }

            st.session_state.registros = pd.concat(
                [st.session_state.registros, pd.DataFrame([nuevo_registro])],
                ignore_index=True
            )

            st.session_state.archivos.append(archivo)

            ast_link = "No adjuntado"

            if archivo is not None:
                media = MediaIoBaseUpload(
                    io.BytesIO(archivo.getbuffer()),
                    mimetype=archivo.type,
                    resumable=False
                )

                file_metadata = {
                    "name": archivo.name,
                    "parents": [AST_FOLDER_ID]
                }

                uploaded = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=False
                ).execute()

                drive_service.permissions().create(
                    fileId=uploaded["id"],
                    body={
                        "type": "anyone",
                        "role": "reader"
                    },
                    supportsAllDrives=False
                ).execute()

                ast_link = f"https://drive.google.com/file/d/{uploaded['id']}/view"

            sheet.append_row([
                fecha_registro,
                st.session_state.area,
                supervisor,
                descripcion,
                supervisor_trabajo,
                dueno_area,
                ast_link
            ])

            st.success("Registro almacenado correctamente.")
            st.write("### Resumen del Registro")
            st.write(nuevo_registro)

    st.subheader("HISTÓRICO DE REGISTROS EN SESIÓN")
    st.dataframe(st.session_state.registros, use_container_width=True)


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
        df["Fecha"] = pd.to_datetime(df["Fecha Registro"]).dt.date

        colk1, colk2, colk3 = st.columns(3)
        colk1.metric("Total de Registros", len(df))
        colk2.metric("Áreas Reportando", df["Área"].nunique())
        colk3.metric("Supervisores Participando", df["Supervisor Área"].nunique())

        st.markdown("---")

        trend = df.groupby("Fecha").size().reset_index(name="Cantidad")
        st.plotly_chart(
            px.line(trend, x="Fecha", y="Cantidad", markers=True),
            use_container_width=True
        )

        st.markdown("---")

        area_count = df["Área"].value_counts().reset_index()
        area_count.columns = ["Área", "Cantidad"]

        st.plotly_chart(
            px.bar(area_count, x="Área", y="Cantidad", text="Cantidad", color="Cantidad"),
            use_container_width=True
        )

        st.markdown("---")

        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]

        st.plotly_chart(
            px.bar(sup_count, x="Supervisor", y="Cantidad", text="Cantidad", color="Cantidad"),
            use_container_width=True
        )

        st.markdown("---")

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
