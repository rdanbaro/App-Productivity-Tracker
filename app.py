# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

from modulos.database import init_db, save_data_to_db, load_data_from_db, clear_database
from modulos.processing import process_uploaded_file, get_new_entries

# --- NUEVA FUNCIÓN DE AYUDA ---
def format_hours_minutes(hours_decimal):
    """Convierte un número decimal de horas a un formato de string 'Xh Ymin'."""
    if pd.isna(hours_decimal):
        return "0h 0min"
    
    # Separar la parte entera (horas)
    hours = int(hours_decimal)
    # Calcular los minutos a partir de la parte decimal y redondear
    minutes = round((hours_decimal - hours) * 60)
    
    return f"{hours}h {minutes}min"

# --- INICIALIZACIÓN DE LA APP ---
init_db()
st.set_page_config(layout="wide", page_title="Analizador de Productividad Avanzado")

# --- BARRA LATERAL ---
st.sidebar.title("Gestión de Datos")
uploaded_file = st.sidebar.file_uploader("1. Sube tu archivo CSV", type="csv")

if uploaded_file is not None:
    file_id = uploaded_file.file_id
    if 'last_processed_file_id' not in st.session_state or st.session_state.last_processed_file_id != file_id:
        with st.spinner('Procesando y guardando datos...'):
            df_raw = pd.read_csv(uploaded_file)
            if 'Total' in df_raw.get('Dia', pd.Series(dtype=str)).values:
                df_raw = df_raw.iloc[:-1]

            df_processed = process_uploaded_file(df_raw)
            if df_processed is not None:
                df_existing = load_data_from_db()
                if not df_existing.empty:
                    df_existing['Dia'] = pd.to_datetime(df_existing['Dia']).dt.strftime('%Y-%m-%d')
                
                df_new_entries = get_new_entries(df_processed, df_existing)
                save_data_to_db(df_new_entries)
                st.session_state.last_processed_file_id = file_id
                st.rerun()

if 'upload_success_message' in st.session_state:
    st.sidebar.success(st.session_state.upload_success_message)
    del st.session_state.upload_success_message

st.sidebar.markdown("---")
st.sidebar.write("2. Opciones")
if st.sidebar.button("Limpiar Base de Datos y Empezar de Nuevo"):
    clear_database()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.sidebar.success("¡Base de datos limpiada!")
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title('🚀 Dashboard de Productividad Avanzado')
df_total = load_data_from_db()

if df_total.empty:
    st.info("Aún no hay datos. Sube un archivo CSV para empezar.")
else:
    st.header("Filtros Globales")
    min_date = df_total['Dia'].min().date()
    max_date = df_total['Dia'].max().date()
    
    date_range = st.date_input("Selecciona un rango de fechas", (min_date, max_date), min_value=min_date, max_value=max_date)
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df_total[(df_total['Dia'].dt.date >= start_date) & (df_total['Dia'].dt.date <= end_date)]
        
        tab_mensual, tab_semanal, tab_diario = st.tabs(["Análisis Mensual", "Análisis Semanal", "Análisis Diario"])

        with tab_mensual:
            st.subheader("Rendimiento Mensual")
            df_mensual = df_filtered.copy()
            df_mensual['Mes'] = df_mensual['Dia'].dt.strftime('%Y-%m')
            
            selected_months = st.multiselect("Compara meses", sorted(df_mensual['Mes'].unique()), key="meses")
            if selected_months:
                df_comparison = df_mensual[df_mensual['Mes'].isin(selected_months)]
                st.subheader("Horas Totales por Mes")
                monthly_totals = df_comparison.groupby('Mes')['Horas'].sum()
                cols = st.columns(len(monthly_totals))
                for i, (month, total_hours) in enumerate(monthly_totals.items()):
                    # --- CAMBIO AQUÍ ---
                    formatted_time = format_hours_minutes(total_hours)
                    cols[i].metric(f"Total Horas en {month}", formatted_time)
                
                with st.expander("Ver datos detallados para la selección mensual"):
                    st.dataframe(df_comparison)
                
                st.markdown("---")
                monthly_summary = df_comparison.groupby(['Mes', 'Categoria'])['Horas'].sum().reset_index()
                fig = px.bar(monthly_summary, x='Mes', y='Horas', color='Categoria', title='Horas por Categoría entre Meses', barmode='group')
                st.plotly_chart(fig, use_container_width=True)

        with tab_semanal:
            st.subheader("Rendimiento Semanal")
            df_semanal = df_filtered.copy()
            df_semanal['Semana'] = df_semanal['Dia'].dt.strftime('%Y-W%U')
            
            selected_weeks = st.multiselect("Compara semanas", sorted(df_semanal['Semana'].unique()), key="semanas")
            if selected_weeks:
                df_comparison = df_semanal[df_semanal['Semana'].isin(selected_weeks)]
                st.subheader("Horas Totales por Semana")
                weekly_totals = df_comparison.groupby('Semana')['Horas'].sum()
                cols = st.columns(len(weekly_totals))
                for i, (week, total_hours) in enumerate(weekly_totals.items()):
                    # --- CAMBIO AQUÍ ---
                    formatted_time = format_hours_minutes(total_hours)
                    cols[i].metric(f"Total Horas en {week}", formatted_time)
                
                with st.expander("Ver datos detallados para la selección semanal"):
                    st.dataframe(df_comparison)

                st.markdown("---")
                weekly_summary = df_comparison.groupby(['Semana', 'Categoria'])['Horas'].sum().reset_index()
                fig = px.bar(weekly_summary, x='Semana', y='Horas', color='Categoria', title='Horas por Categoría entre Semanas', barmode='group')
                st.plotly_chart(fig, use_container_width=True)

        with tab_diario:
            st.subheader("Análisis Diario")
            selected_day = st.date_input("Elige un día", max_date)
            df_day = df_filtered[df_filtered['Dia'].dt.date == selected_day]
            if not df_day.empty:
                # --- CAMBIO AQUÍ ---
                total_hours_day = df_day['Horas'].sum()
                formatted_time = format_hours_minutes(total_hours_day)
                st.metric("Total Horas en este día", formatted_time)
                
                fig = px.pie(df_day, names='Tarea', values='Horas', title=f"Distribución de Tareas del {selected_day.strftime('%d/%m/%Y')}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos para el día seleccionado.")