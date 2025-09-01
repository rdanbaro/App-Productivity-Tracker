# modulos/processing.py

import pandas as pd
import streamlit as st

def parse_duration(duration_str):
    """
    Convierte una duración en formato 'HH:MM' o 'HH:MM:SS' a horas decimales.
    Es compatible con ambos formatos.
    """
    if pd.isna(duration_str): return 0.0
    try:
        parts = str(duration_str).split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        # --- CAMBIO AQUÍ ---
        # Si existe una tercera parte (segundos), la añadimos al cálculo.
        seconds = int(parts[2]) if len(parts) > 2 else 0
        
        return hours + (minutes / 60.0) + (seconds / 3600.0)
    except (ValueError, IndexError): 
        return 0.0

def process_uploaded_file(df):
    required_columns = ['Dia', 'Duracion', 'Tarea', 'Etiquetas']
    if not all(col in df.columns for col in required_columns):
        st.error(f"El archivo CSV debe contener las columnas: {', '.join(required_columns)}")
        return None
    
    processed_df = df[required_columns].copy()
    processed_df = processed_df.rename(columns={'Etiquetas': 'Categoria'})

    processed_df['Tarea'] = processed_df['Tarea'].fillna('Sin Tarea')
    processed_df['Categoria'] = processed_df['Categoria'].fillna('Sin Categoria')
    processed_df = processed_df.dropna(subset=['Dia'])

    try:
        processed_df['Dia'] = pd.to_datetime(processed_df['Dia'], format='%d/%m/%Y', errors='coerce')
        processed_df = processed_df.dropna(subset=['Dia'])
        processed_df['Horas'] = processed_df['Duracion'].apply(parse_duration)
        
        final_df = processed_df[['Dia', 'Categoria', 'Tarea', 'Horas']].copy()
        final_df['Dia'] = final_df['Dia'].dt.strftime('%Y-%m-%d')
        return final_df
        
    except Exception as e:
        st.error(f"Ocurrió un error en el procesamiento: {e}")
        return None

def get_new_entries(df_new, df_existing):
    if df_existing.empty:
        return df_new
    
    df_new['merge_key'] = df_new.astype(str).agg('-'.join, axis=1)
    df_existing['merge_key'] = df_existing.astype(str).agg('-'.join, axis=1)
    new_entries = df_new[~df_new['merge_key'].isin(df_existing['merge_key'])]
    return new_entries.drop(columns=['merge_key'])