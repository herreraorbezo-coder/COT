import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials


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

# ⚠️ USA SIEMPRE EL ID (NO EL NOMBRE)
SHEET_ID = "PEGA_EL_ID_AQUI"
sheet = cliente.open_by_key(SHEET_ID).sheet1


# ========================== CONFIG STREAMLIT ==========================
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")


# ========================== SESSION STATE ==========================
if "registros" not in st.session_state:
    st.session_state.registros = pd.DataFrame(columns=[
        "Fecha Registro",
        "Área",
        "Supervisor Área",
        "Descripción Actividad",
        "Supervisor de Trabajo",
        "Dueño de Área",
        "PSM"
    ])


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

        psm = st.radio("¿Actividad asociada a PSM?", ["NO", "SÍ"], horizontal=True)

        enviar = st.form_submit_button("GUARDAR REGISTRO")

    if enviar:
        if descripcion.strip() == "" or supervisor_trabajo.strip() == "" or dueno_area.strip() == "":
            st.error("⚠️ Campos obligatorios vacíos.")
        else:
            nuevo_registro = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                st.session_state.area,
                supervisor,
                descripcion,
                supervisor_trabajo,
                dueno_area,
                psm
            ]

            sheet.append_row(nuevo_registro)
            st.success("Registro almacenado correctamente.")

    st.subheader("HISTÓRICO DE REGISTROS EN SESIÓN")
    st.dataframe(st.session_state.registros, use_container_width=True)


# ====================================================================================
#                               TAB DASHBOARD
# ====================================================================================
with menu[1]:

    st.subheader("📊 KPIs y Gráficas del COT")

    data = sheet.get_all_records()

    if data:
        df = pd.DataFrame(data)
        df["Fecha"] = pd.to_datetime(df["Fecha Registro"]).dt.date

        colk1, colk2, colk3 = st.columns(3)
        colk1.metric("Total Registros", len(df))
        colk2.metric("Áreas Reportando", df["Área"].nunique())
        colk3.metric("Supervisores Participando", df["Supervisor Área"].nunique())

        trend = df.groupby("Fecha").size().reset_index(name="Cantidad")
        st.plotly_chart(px.line(trend, x="Fecha", y="Cantidad", markers=True), True)

        area_count = df["Área"].value_counts().reset_index()
        area_count.columns = ["Área", "Cantidad"]
        st.plotly_chart(px.bar(area_count, x="Área", y="Cantidad"), True)

        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]
        st.plotly_chart(px.bar(sup_count, x="Supervisor", y="Cantidad"), True)

        heat = df.groupby(["Fecha", "Área"]).size().reset_index(name="Cantidad")
        st.plotly_chart(px.density_heatmap(heat, x="Fecha", y="Área", z="Cantidad"), True)

        psm_count = df["PSM"].value_counts().reset_index()
        psm_count.columns = ["PSM", "Cantidad"]
        st.plotly_chart(px.pie(psm_count, names="PSM", values="Cantidad", hole=0.4), True)

