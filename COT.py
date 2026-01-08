import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# -------------------------------- CONFIG --------------------------------
st.set_page_config(
    page_title="SISTEMA COT - AGUAYTÍA ENERGY S.R.L.",
    layout="wide",
    page_icon="🛠️"
)

st.title("SISTEMA COT - AGUAYTÍA ENERGY S.R.L.")
st.write("Plataforma para registro de actividades destinadas al COT")

# --------------------------- BASE DE DATOS TEMPORAL ---------------------------
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

# -------------------------------- AREAS Y SUPERVISORES --------------------------------
areas = {
    "PRODUCCION": ["BREYSON TALLEDO", "MIGUEL CRUZ"],
    "MANTENIMIENTO": ["NILTON HINOSTROZA", "GUSTAVO VASQUEZ"],
    "E&IC": ["OMAR CAYLLAHUA", "MAURO BENAVENTE", "DAWI TORRES"],
    "ADMINISTRACION": ["ENRIQUE ESPINOZA", "LUCIO ZEVALLOS"],
    "EHS": ["JOSE BENDEZU", "JACKER RUIZ", "MARCO ALVARADO"]
}

# -------------------- MENU SUPERIOR --------------------
menu = st.tabs(["📋 Registrar Actividad", "📊 Dashboard / KPIs"])

# ====================================================================================
#                                TAB REGISTRO
# ====================================================================================
with menu[0]:

    st.subheader("DATOS DEL SUPERVISOR")

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

            st.success("Registro almacenado correctamente.")
            st.write("### Resumen del Registro")
            st.write(nuevo_registro)

    st.subheader("HISTÓRICO DE REGISTROS EN SESIÓN")
    st.dataframe(st.session_state.registros, use_container_width=True)

    st.subheader("Descargar ATS Guardados")
    for file in st.session_state.archivos:
        if file:
            st.download_button(f"Descargar {file.name}", file, file.name)

# ====================================================================================
#                                TAB DASHBOARD
# ====================================================================================
with menu[1]:

    st.subheader("📊 KPIs y Gráficas del COT")

    if len(st.session_state.registros) == 0:
        st.info("Aún no hay registros para mostrar KPIs.")
    else:
        df = st.session_state.registros.copy()
        df["Fecha"] = pd.to_datetime(df["Fecha Registro"]).dt.date

        # ------------------- KPI PRINCIPALES -------------------
        colk1, colk2, colk3 = st.columns(3)
        colk1.metric("Total de Registros", len(df))
        colk2.metric("Áreas Reportando", df["Área"].nunique())
        colk3.metric("Supervisores Participando", df["Supervisor Área"].nunique())

        st.markdown("---")

        # ------------------- KPI 1 Tendencia en el tiempo -------------------
        st.subheader("📈 Tendencia de registros en el tiempo")
        trend = df.groupby("Fecha").size().reset_index(name="Cantidad")
        fig_trend = px.line(trend, x="Fecha", y="Cantidad", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("---")

        # ------------------- KPI 2 Participación por área mejorada -------------------
        st.subheader("🏆 Participación por Área")
        area_count = df["Área"].value_counts().reset_index()
        area_count.columns = ["Área", "Cantidad"]

        top_area = area_count.iloc[0]
        st.success(f"Área con mayor aporte: {top_area['Área']} ({top_area['Cantidad']} registros)")

        if len(area_count) > 1:
            bottom_area = area_count.iloc[-1]
            st.warning(f"Área con menor aporte: {bottom_area['Área']} ({bottom_area['Cantidad']} registros)")

        fig_area = px.bar(area_count, x="Área", y="Cantidad", text="Cantidad", color="Cantidad")
        st.plotly_chart(fig_area, use_container_width=True)

        st.markdown("---")

        # ------------------- KPI 3 Ranking de Supervisores -------------------
        st.subheader("👤 Ranking de Supervisores")
        sup_count = df["Supervisor Área"].value_counts().reset_index()
        sup_count.columns = ["Supervisor", "Cantidad"]

        st.info(f"Supervisor Top: {sup_count.iloc[0]['Supervisor']} con {sup_count.iloc[0]['Cantidad']} registros")

        fig_sup = px.bar(sup_count, x="Supervisor", y="Cantidad", text="Cantidad", color="Cantidad")
        st.plotly_chart(fig_sup, use_container_width=True)

        st.markdown("---")

        # ------------------- KPI 6 Heatmap participación -------------------
        st.subheader("🔥 Mapa de Participación por Día y Área")
        heat = df.groupby(["Fecha", "Área"]).size().reset_index(name="Cantidad")
        fig_heat = px.density_heatmap(
            heat,
            x="Fecha",
            y="Área",
            z="Cantidad",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("---")

        # ------------------- KPI 7 % Cumplimiento meta -------------------
        st.subheader("🎯 % Cumplimiento de Meta")
        meta = st.slider("Meta mínima diaria de registros:", 1, 50, 5)

        cumplimiento = []
        for day, total in trend.values:
            cumplimiento.append(min(100, int((total / meta) * 100)))

        avg_cumplimiento = int(sum(cumplimiento) / len(cumplimiento))

        if avg_cumplimiento >= 90:
            st.success(f"Cumplimiento promedio: {avg_cumplimiento}%")
        elif avg_cumplimiento >= 60:
            st.warning(f"Cumplimiento promedio: {avg_cumplimiento}%")
        else:
            st.error(f"Cumplimiento promedio: {avg_cumplimiento}%")
