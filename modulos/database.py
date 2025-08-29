# modulos/database.py

import sqlite3
import pandas as pd
import os
import streamlit as st

DB_FILE = "BBDD/productivity_data.db"

def init_db():
    os.makedirs("BBDD", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Dia TEXT NOT NULL,
            Categoria TEXT NOT NULL,
            Tarea TEXT NOT NULL,
            Horas REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_data_to_db(df):
    if df.empty:
        st.sidebar.info("No se encontraron nuevos registros para añadir.")
        return
    conn = sqlite3.connect(DB_FILE)
    try:
        df.to_sql('time_entries', conn, if_exists='append', index=False)
        st.session_state.upload_success_message = f"¡Éxito! Se han guardado {len(df)} nuevos registros."
    except Exception as e:
        st.sidebar.error(f"Error al guardar en la base de datos: {e}")
    finally:
        conn.close()

def load_data_from_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM time_entries", conn)
        if not df.empty:
            df['Dia'] = pd.to_datetime(df['Dia'])
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

def clear_database():
    """Elimina todos los registros de la tabla time_entries."""
    if not os.path.exists(DB_FILE):
        return True
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM time_entries")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False