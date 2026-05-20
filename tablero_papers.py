import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import textwrap

st.set_page_config(page_title="Control de Papers - Camilo & Alejandro", layout="wide")
st.title("📊 Tablero de Avance en Línea: Papers de Investigación")
st.markdown("Gestión compartida de actividades, tiempos y responsabilidades.")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0) 
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica la configuración de tus Secrets.")
    st.stop()

ACTIVIDADES = [
    "Análisis estadístico y elección del modelo",
    "Escritura de la introducción",
    "Marco teórico",
    "Escritura de la metodología y resultados",
    "Discusión y conclusiones",
    "Revisión completa del documento",
    "Decisión de sometimiento del paper a la revista",
    "Someter el paper",
    "Decisión por parte de la revista",
    "Acciones según decisión (Ej. Nueva revista / Re-sometimiento)"
]

FASES_META_100 = [
    "Análisis estadístico y elección del modelo",
    "Escritura de la introducción",
    "Marco teórico",
    "Escritura de la metodología y resultados",
    "Discusión y conclusiones",
    "Revisión completa del documento",
    "Decisión de sometimiento del paper a la revista",
    "Someter el paper"
]

AUTORES_BASE = [
    "Camilo Alarcón", 
    "Alejandro Díaz", 
    "Jose Antonio Clemente", 
    "Esther Aranda", 
    "Alejandra Fiayo", 
    "Jorge Restrepo", 
    "Ambos"
]

if not df.empty and 'Responsable' in df.columns:
    autores_existentes = list(df['Responsable'].dropna().unique())
    RESPONSABLES = list(set(AUTORES_BASE + autores_existentes))
else:
    RESPONSABLES = AUTORES_BASE

ESTADOS = ["Pendiente", "En Progreso", "Completado"]

st.sidebar.header("⚙️ Panel de Control")
opcion_menu = st.sidebar.radio("Selecciona una acción:", ["Registrar / Actualizar Avance", "Eliminar Datos Directamente"])

if opcion_menu == "Registrar / Actualizar Avance":
    st.sidebar.markdown("### 📝 Formulario de Registro")
    with st.sidebar.form("formulario_avance"):
        papers_existentes = list(df['Paper'].dropna().unique()) if not df.empty else []
        paper_seleccion = st.selectbox("Nombre del Paper", ["+ Crear Nuevo Paper..."] + papers_existentes)
        paper_nuevo = st.text_input("Si elegiste '+ Crear Nuevo Paper...', escribe el nombre aquí:")
        
        responsable_seleccion = st.selectbox("Responsable de la Actividad", ["+ Agregar Nuevo Coautor..."] + RESPONSABLES)
        responsable_nuevo = st.text_input("Si elegiste '+ Agregar Nuevo Coautor...', escribe su nombre aquí:")
        
        actividad = st.selectbox("Fase de la Investigación", ACTIVIDADES)
        correo_responsable = st.text_input("Correo electrónico del responsable (Para notificaciones)")
        estado = st.selectbox("Estado Actual", ESTADOS)
        
        fecha_inicio = st.date_input("Fecha de Inicio")
        fecha_fin = st.date_input("Fecha de Finalización (o Estimada)")
        comentarios = st.text_area("Notas / Comentarios adicionales")
        
        st.markdown("---")
        decision_revista = st.radio("Resultado del Dictamen (Revista):", ["No aplica", "Aceptado", "Comentarios Mayores", "Rechazado"])
        
        submit_btn = st.form_submit_button("Sincronizar con la Nube")

        if submit_btn:
            paper_final = paper_nuevo if paper_seleccion == "+ Crear Nuevo Paper..." else paper_seleccion
            responsable_final = responsable_nuevo if responsable_seleccion == "+ Agregar Nuevo Coautor..." else responsable_seleccion
            
            if not paper_final or paper_final.strip() == "":
                st.error("Por favor, introduce el nombre del paper.")
            elif not responsable_final or responsable_final.strip() == "":
                st.error("Por favor, especifica el responsable de la actividad.")
            elif fecha_inicio > fecha_fin:
                st.error("La fecha de inicio no puede ser posterior a la finalización.")
            else:
                accion_texto = comentarios
                if actividad == "Decisión por parte de la revista" or decision_revista != "No aplica":
                    if decision_revista == "Rechazado":
                        accion_texto = "🚨 RECHAZADO -> Buscar de inmediato nueva revista. | " + comentarios
                    elif decision_revista == "Comentarios Mayores":
                        accion_texto = "⚠️ REVISIÓN -> Realizar cambios estructurales y volver a someter. | " + comentarios
                
                df_limpio = df.dropna(how='all').copy()
                
                columnas_texto = ['Responsable', 'Correo Responsable', 'Estado', 'Comentarios/Acciones']
                for col in columnas_texto:
                    if col not in df_limpio.columns:
                        df
