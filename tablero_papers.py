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

# Garantizar que las columnas existan para evitar bloqueos si la hoja está en blanco
columnas_base = ['Paper', 'Actividad', 'Responsable', 'Correo Responsable', 'Estado', 'Fecha Inicio', 'Fecha Fin', 'Comentarios/Acciones']
for col in columnas_base:
    if col not in df.columns:
        df[col] = ""

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

# ==========================================
# MODULO 1: REGISTRO
# ==========================================
if opcion_menu == "Registrar / Actualizar Avance":
    st.sidebar.markdown("### 📝 Formulario de Registro")
    with st.sidebar.form("formulario_avance"):
        papers_existentes = list(df['Paper'].dropna().unique()) if not df.empty else []
        opciones_paper = ["+ Crear Nuevo Paper..."] + [p for p in papers_existentes if p != ""]
        paper_seleccion = st.selectbox("Nombre del Paper", opciones_paper)
        paper_nuevo = st.text_input("Si elegiste '+ Crear Nuevo Paper...', escribe el nombre aquí:")
        
        responsable_seleccion = st.selectbox("Responsable de la Actividad", ["+ Agregar Nuevo Coautor..."] + [r for r in RESPONSABLES if r != ""])
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
                
                # PREVENCIÓN DE ERRORES DE FORMATO
                columnas_texto = ['Responsable', 'Correo Responsable', 'Estado', 'Comentarios/Acciones', 'Paper', 'Actividad']
                for col in columnas_texto:
                    if col not in df_limpio.columns:
                        df_limpio[col] = ""
                    df_limpio[col] = df_limpio[col].astype(str)
                
                if not df_limpio.empty:
                    mascara = (df_limpio['Paper'] == paper_final.strip()) & (df_limpio['Actividad'] == actividad)
                else:
                    mascara = pd.Series([False])
                    
                if mascara.any():
                    indice = df_limpio[mascara].index[0]
                    df_limpio.loc[indice, 'Responsable'] = responsable_final.strip()
                    df_limpio.loc[indice, 'Correo Responsable'] = correo_responsable.strip()
                    df_limpio.loc[indice, 'Estado'] = estado
                    df_limpio.loc[indice, 'Fecha Inicio'] = fecha_inicio.strftime('%Y-%m-%d')
                    df_limpio.loc[indice, 'Fecha Fin'] = fecha_fin.strftime('%Y-%m-%d')
                    df_limpio.loc[indice, 'Comentarios/Acciones'] = accion_texto
                    df_actualizado = df_limpio
                else:
                    nuevo_registro = pd.DataFrame([{
                        "Paper": paper_final.strip(),
                        "Actividad": actividad,
                        "Responsable": responsable_final.strip(),
                        "Correo Responsable": correo_responsable.strip(),
                        "Estado": estado,
                        "Fecha Inicio": fecha_inicio.strftime('%Y-%m-%d'),
                        "Fecha Fin": fecha_fin.strftime('%Y-%m-%d'),
                        "Comentarios/Acciones": accion_texto
                    }])
                    df_actualizado = pd.concat([df_limpio, nuevo_registro], ignore_index=True)
                    
                conn.update(data=df_actualizado)
                st.success(f"✅ Sincronización exitosa.")
                st.rerun()

# ==========================================
# MODULO 2: ELIMINACIÓN DIRECTA
# ==========================================
elif opcion_menu == "Eliminar Datos Directamente":
    st.sidebar.markdown("### 🗑️ Opciones de Borrado Frecuente")
    tipo_borrado = st.sidebar.selectbox("¿Qué deseas eliminar de la base de datos?", [
        "Una Actividad específica dentro de un Proyecto",
        "Un Proyecto (Paper) completo",
        "Un Autor (Borrar sus registros)"
    ])
    
    if not df.empty and df.dropna(subset=['Paper', 'Actividad']).shape[0] > 0:
        df_valido = df.dropna(subset=['Paper', 'Actividad'])
        df_valido = df_valido[(df_valido['Paper'].astype(str).str.strip() != "") & (df_valido['Actividad'].astype(str).str.strip() != "")]
        
        if tipo_borrado == "Una Actividad específica dentro de un Proyecto":
            paper_a_borrar = st.sidebar.selectbox("1. Selecciona el Proyecto:", df_valido['Paper'].unique())
            actividades_del_paper = df_valido[df_valido['Paper'] == paper_a_borrar]['Actividad'].unique()
            actividad_a_borrar = st.sidebar.selectbox("2. Selecciona la Actividad a remover:", actividades_del_paper)
            
            if st.sidebar.button("❌ Eliminar Actividad Seleccionada"):
                df_actualizado = df[~((df['Paper'] == paper_a_borrar) & (df['Actividad'] == actividad_a_borrar))]
                conn.update(data=df_actualizado)
                st.success(f"🗑️ Actividad '{actividad_a_borrar}' eliminada correctamente de '{paper_a_borrar}'.")
                st.rerun()
                
        elif tipo_borrado == "Un Proyecto (Paper) completo":
            paper_completo_borrar = st.sidebar.selectbox("Selecciona el Paper que deseas borrar por completo:", df_valido['Paper'].unique())
            if st.sidebar.button("❌ Eliminar Todo el Proyecto"):
                df_actualizado = df[df['Paper'] != paper_completo_borrar]
                conn.update(data=df_actualizado)
                st.success(f"🗑️ El proyecto '{paper_completo_borrar}' ha sido borrado de la nube por completo.")
                st.rerun()
                
        elif tipo_borrado == "Un Autor (Borrar sus registros)":
            autor_a_borrar = st.sidebar.selectbox("Selecciona el Autor que deseas remover de las asignaciones:", df_valido['Responsable'].unique())
            if st.sidebar.button("❌ Eliminar Asignaciones del Autor"):
                df_actualizado = df[df['Responsable'] != autor_a_borrar]
                conn.update(data=df_actualizado)
                st.success(f"🗑️ Todos los registros bajo la responsabilidad de '{autor_a_borrar}' han sido eliminados.")
                st.rerun()
    else:
        st.sidebar.info("No hay datos cargados para eliminar en este momento.")


# ==========================================
# MODULO 3: VISUALIZACIÓN GENERAL
# ==========================================
if not df.empty and df.dropna(subset=['Paper', 'Actividad']).shape[0] > 0:
    df_visualizacion = df.dropna(subset=['Paper', 'Actividad']).copy()
    df_visualizacion = df_visualizacion[(df_visualizacion['Paper'].astype(str).str.strip() != "") & (df_visualizacion['Actividad'].astype(str).str.strip() != "")]
    
    if df_visualizacion.shape[0] > 0:
        df_visualizacion['Fecha Inicio'] = pd.to_datetime(df_visualizacion['Fecha Inicio'], errors='coerce')
        df_visualizacion['Fecha Fin'] = pd.to_datetime(df_visualizacion['Fecha Fin'], errors='coerce')

        tab_general, tab_individual = st.tabs(["🌐 Visión General de Proyectos", "📄 Seguimiento Individual por Paper"])
        
        with tab_general:
            st.subheader("Rendimiento Global del Equipo")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Tareas Registradas", len(df_visualizacion))
            with col2:
                st.metric("Papers Activos", df_visualizacion['Paper'].nunique())
            with col3:
                completadas_mask = df_visualizacion['Estado'].isin(['Completado', 'Completo'])
                st.metric("Fases Completadas (Global)", len(df_visualizacion[completadas_mask]))
            
            st.markdown("---")
            st.subheader("📅 Cronograma Integrado (Todos los Papers)")
            
            num_papers = df_visualizacion['Paper'].nunique()
            altura_dinamica = 300 + (120 * num_papers)
            
            fig_global = px.timeline(
                df_visualizacion, x_start="Fecha Inicio", x_end="Fecha Fin", y="Actividad", 
                color="Responsable", facet_row="Paper", hover_data=["Estado", "Comentarios/Acciones"],
                color_discrete_sequence=px.colors.qualitative.Safe, height=altura_dinamica
            )
            
            fig_global.for_each_annotation(
                lambda a: a.update(text="<br>".join(textwrap.wrap(a.text.split("=")[-1], width=50)))
            )
            
            fig_global.update_yaxes(title_text="", autorange="reversed", matches=None)
            fig_global.update_layout(margin=dict(l=20, r=20, t=40, b=20), legend_title_text="Investigador")
            st.plotly_chart(fig_global, use_container_width=True)

        with tab_individual:
            st.subheader("🔍 Análisis Detallado de Progreso")
            lista_papers = df_visualizacion['Paper'].unique()
            paper_seleccionado = st.selectbox("Selecciona el paper que deseas auditar:", lista_papers)
            
            df_paper = df_visualizacion[df_visualizacion['Paper'] == paper_seleccionado]
            
            completadas_mask_ind = df_paper['Estado'].isin(['Completado', 'Completo'])
            actividades_completadas_total = df_paper[completadas_mask_ind]['Actividad'].tolist()
            
            fases_meta_completadas = [act for act in actividades_completadas_total if act in FASES_META_100]
            porcentaje_avance = len(fases_meta_completadas) / len(FASES_META_100)
            
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
else:
    st.info("💡 La hoja de cálculo está lista. Utiliza el panel izquierdo para registrar avances.")
