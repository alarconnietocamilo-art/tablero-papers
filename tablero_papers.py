import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

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
    "Discusión y conclusiones",
    "Revisión completa del documento",
    "Decisión de sometimiento del paper a la revista",
    "Someter el paper",
    "Decisión por parte de la revista",
    "Acciones según decisión (Ej. Nueva revista / Re-sometimiento)"
]

# Definimos cuáles son las fases requeridas para llegar al 100% del objetivo principal
FASES_META_100 = [
    "Análisis estadístico y elección del modelo",
    "Escritura de la introducción",
    "Marco teórico",
    "Discusión y conclusiones",
    "Revisión completa del documento",
    "Decisión de sometimiento del paper a la revista",
    "Someter el paper"
]

RESPONSABLES = [
    "Camilo Alarcón", 
    "Alejandro Díaz", 
    "Jose Antonio Clemente", 
    "Esther Aranda", 
    "Alejandra Fiayo", 
    "Jorge Restrepo", 
    "Ambos"
]

ESTADOS = ["Pendiente", "En Progreso", "Completado"]

st.sidebar.header("📝 Registrar / Actualizar Avance")
with st.sidebar.form("formulario_avance"):
    papers_existentes = list(df['Paper'].dropna().unique()) if not df.empty else []
    opciones_paper = ["+ Crear Nuevo Paper..."] + papers_existentes
    paper_seleccion = st.selectbox("Nombre del Paper", opciones_paper)
    
    paper_nuevo = st.text_input("Si elegiste '+ Crear Nuevo Paper...', escribe el nombre aquí:")
    
    actividad = st.selectbox("Fase de la Investigación", ACTIVIDADES)
    responsable = st.selectbox("Responsable de la Actividad", RESPONSABLES)
    correo_responsable = st.text_input("Correo electrónico del responsable (Para notificaciones)")
    estado = st.selectbox("Estado Actual", ESTADOS)
    
    fecha_inicio = st.date_input("Fecha de Inicio")
    fecha_fin = st.date_input("Fecha de Finalización (o Estimada)")
    comentarios = st.text_area("Notas / Comentarios adicionales")
    
    st.markdown("---")
    st.markdown("⚠️ **Flujo de decisión de la revista (Solo si aplica):**")
    decision_revista = st.radio("Resultado del Dictamen:", ["No aplica", "Aceptado", "Comentarios Mayores", "Rechazado"])
    
    submit_btn = st.form_submit_button("Sincronizar con la Nube")

    if submit_btn:
        paper_final = paper_nuevo if paper_seleccion == "+ Crear Nuevo Paper..." else paper_seleccion
        
        if not paper_final or paper_final.strip() == "":
            st.error("Por favor, introduce el nombre del paper.")
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
            
            # LÓGICA DE ACTUALIZACIÓN: Buscar si la actividad ya existe para este paper
            if not df_limpio.empty:
                mascara = (df_limpio['Paper'] == paper_final.strip()) & (df_limpio['Actividad'] == actividad)
            else:
                mascara = pd.Series([False])
                
            if mascara.any():
                # Si existe, actualizamos la fila existente para no duplicar
                indice = df_limpio[mascara].index[0]
                df_limpio.loc[indice, 'Responsable'] = responsable
                df_limpio.loc[indice, 'Correo Responsable'] = correo_responsable.strip()
                df_limpio.loc[indice, 'Estado'] = estado
                df_limpio.loc[indice, 'Fecha Inicio'] = fecha_inicio.strftime('%Y-%m-%d')
                df_limpio.loc[indice, 'Fecha Fin'] = fecha_fin.strftime('%Y-%m-%d')
                df_limpio.loc[indice, 'Comentarios/Acciones'] = accion_texto
                df_actualizado = df_limpio
            else:
                # Si no existe, creamos una nueva fila
                nuevo_registro = pd.DataFrame([{
                    "Paper": paper_final.strip(),
                    "Actividad": actividad,
                    "Responsable": responsable,
                    "Correo Responsable": correo_responsable.strip(),
                    "Estado": estado,
                    "Fecha Inicio": fecha_inicio.strftime('%Y-%m-%d'),
                    "Fecha Fin": fecha_fin.strftime('%Y-%m-%d'),
                    "Comentarios/Acciones": accion_texto
                }])
                df_actualizado = pd.concat([df_limpio, nuevo_registro], ignore_index=True)
                
            conn.update(data=df_actualizado)
            st.success(f"✅ Estado de '{actividad}' actualizado a '{estado}'.")
            st.rerun()

if not df.empty and df.dropna(subset=['Paper', 'Actividad']).shape[0] > 0:
    df_visualizacion = df.dropna(subset=['Paper', 'Actividad']).copy()
    df_visualizacion['Fecha Inicio'] = pd.to_datetime(df_visualizacion['Fecha Inicio'])
    df_visualizacion['Fecha Fin'] = pd.to_datetime(df_visualizacion['Fecha Fin'])

    tab_general, tab_individual = st.tabs(["🌐 Visión General de Proyectos", "📄 Seguimiento Individual por Paper"])
    
    with tab_general:
        st.subheader("Rendimiento Global del Equipo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Tareas Registradas", len(df_visualizacion))
        with col2:
            st.metric("Papers Activos", df_visualizacion['Paper'].nunique())
        with col3:
            # Compatibilidad con "Completo" o "Completado"
            completadas_mask = df_visualizacion['Estado'].isin(['Completado', 'Completo'])
            st.metric("Fases Completadas (Global)", len(df_visualizacion[completadas_mask]))
        
        st.markdown("---")
        st.subheader("📅 Cronograma Integrado (Todos los Papers)")
        fig_global = px.timeline(
            df_visualizacion, x_start="Fecha Inicio", x_end="Fecha Fin", y="Actividad", 
            color="Responsable", facet_col="Paper", hover_data=["Estado", "Comentarios/Acciones"],
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_global.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_global, use_container_width=True)

    with tab_individual:
        st.subheader("🔍 Análisis Detallado de Progreso")
        lista_papers = df_visualizacion['Paper'].unique()
        paper_seleccionado = st.selectbox("Selecciona el paper que deseas auditar:", lista_papers)
        
        df_paper = df_visualizacion[df_visualizacion['Paper'] == paper_seleccionado]
        
        # Filtramos las completadas (Aceptando "Completado" o "Completo")
        completadas_mask_ind = df_paper['Estado'].isin(['Completado', 'Completo'])
        actividades_completadas_total = df_paper[completadas_mask_ind]['Actividad'].tolist()
        
        # Calculamos el progreso SOLO con las 7 fases principales
        fases_meta_completadas = [act for act in actividades_completadas_total if act in FASES_META_100]
        porcentaje_avance = len(fases_meta_completadas) / len(FASES_META_100)
        
        # Evitamos que pase del 100% visualmente
        if porcentaje_avance > 1.0:
            porcentaje_avance = 1.0
        
        st.markdown(f"### Nivel de Avance para Sometimiento: **{int(porcentaje_avance * 100)}%**")
        st.progress(porcentaje_avance)
        
        col_grafico, col_lista = st.columns([2, 1])
        
        with col_grafico:
            st.markdown("#### Cronograma de este Paper")
            fig_ind = px.timeline(
                df_paper, x_start="Fecha Inicio", x_end="Fecha Fin", y="Actividad", 
                color="Responsable", hover_data=["Estado", "Comentarios/Acciones"],
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_ind.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_ind, use_container_width=True)
            
        with col_lista:
            st.markdown("#### Checklist de Actividades")
            for act in ACTIVIDADES:
                if act in actividades_completadas_total:
                    st.markdown(f"✅ ~~{act}~~")
                elif act in df_paper['Actividad'].tolist():
                    # Mostrar el estado en el que se encuentra actualmente
                    estado_actual = df_paper[df_paper['Actividad'] == act]['Estado'].values[0]
                    st.markdown(f"🔄 **{act}** *({estado_actual})*")
                else:
                    st.markdown(f"⚪ {act} *(No iniciada)*")
                    
        st.markdown("---")
        st.markdown(f"#### Historial de registros: {paper_seleccionado}")
        st.dataframe(
            df_paper.sort_values(by="Fecha Inicio", ascending=False),
            column_config={
                "Fecha Inicio": st.column_config.DatetimeColumn("Inicio", format="YYYY-MM-DD"),
                "Fecha Fin": st.column_config.DatetimeColumn("Fin", format="YYYY-MM-DD"),
            },
            use_container_width=True, hide_index=True
        )

else:
    st.info("💡 La hoja de cálculo está lista. Utiliza el panel izquierdo para registrar avances.")
