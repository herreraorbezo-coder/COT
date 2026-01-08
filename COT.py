import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
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
sheet = cliente.open("COT_AGUAYTIA").sheet1


# ========================== CONFIG STREAMLIT ==========================
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")


# ========================== AREAS ==========================
areas = {
    "PRODUCCION": ["BREYSON TALLEDO", "MIGUEL CRUZ"],
    "MANTENIMIENTO": ["NILTON HINOSTROZA", "GUSTAVO VASQUEZ"],
    "E&IC": ["OMAR CAYLLAHUA", "MAURO BENAVENTE", "DAWI TORRES"],
    "ADMINISTRACION": ["ENRIQUE ESPINOZA", "LUCIO ZEVALLOS"],
    "EHS": ["JOSE BENDEZU", "JACKER RUIZ", "MARCO ALVARADO"],
    "GIA": ["GARI NAVARRO", "JULIAN RODRIGUEZ", "ADDERLY DE LA CRUZ"]
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

        supervisor = st.selectbox("SUPERVISOR / OPERADOR", areas[st.session_state.area])

        st.subheader("DATOS DE LA ACTIVIDAD")

        descripcion = st.text_area("DESCRIPCIÓN DE LA ACTIVIDAD * (Obligatorio)")

        col3, col4 = st.columns(2)

        with col3:
            supervisor_trabajo = st.text_input("SUPERVISOR DE TRABAJO * (Obligatorio)")

        with col4:
            dueno_area = st.text_input("DUEÑO DE ÁREA * (Obligatorio)")

        enviar = st.form_submit_button("GUARDAR REGISTRO")

    if enviar:
        if descripcion.strip() == "" or supervisor_trabajo.strip() == "" or dueno_area.strip() == "":
            st.error("⚠️ No puedes registrar. Hay campos obligatorios vacíos.")
        else:
            fecha_registro = datetime.now(
                ZoneInfo("America/Lima")
            ).strftime("%Y-%m-%d %H:%M:%S")

            archivo_ats = "No adjuntado"

            nuevo_registro = {
                "Fecha Registro": fecha_registro,
                "Área": st.session_state.area,
                "Supervisor Área": supervisor,
                "Descripción Actividad": descripcion,
                "Supervisor de Trabajo": supervisor_trabajo,
                "Dueño de Área": dueno_area,
                "Archivo ATS": archivo_ats
            }

            sheet.append_row([
                fecha_registro,
                st.session_state.area,
                supervisor,
                descripcion,
                supervisor_trabajo,
                dueno_area,
                archivo_ats
            ])

            st.success("Registro almacenado correctamente.")
            st.write("### Resumen del Registro")
            st.write(nuevo_registro)

    st.subheader("HISTÓRICO DE REGISTROS")

    data_historico = sheet.get_all_records()

    if len(data_historico) == 0:
        st.info("Aún no hay registros almacenados.")
    else:
        df_historico = pd.DataFrame(data_historico)
        st.dataframe(df_historico, use_container_width=True)


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
            px.bar(
                area_count,
                x="Área",
                y="Cantidad",
                color="Área",
                text="Cantidad"
            ),
            use_container_width=True
        )

        st.markdown("---")

        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]

        st.plotly_chart(
            px.bar(
                sup_count,
                x="Supervisor",
                y="Cantidad",
                color="Supervisor",
                text="Cantidad"
            ),
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

        pie_data = df["Área"].value_counts().reset_index()
        pie_data.columns = ["Área", "Cantidad"]

        st.plotly_chart(
            px.pie(
                pie_data,
                names="Área",
                values="Cantidad",
                hole=0.4,
                title="Distribución porcentual de registros por Área"
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

