import streamlit as st
import psycopg2

cfg = st.secrets["neon"]
conn = psycopg2.connect(
    host=cfg["host"],
    dbname=cfg["dbname"],
    user=cfg["user"],
    password=cfg["password"],
    sslmode="require"
)
cursor = conn.cursor()

cursor.execute("SELECT name FROM exercice")
exercises_list = [row[0] for row in cursor.fetchall()]

# --- UI ---
st.write("Track down a series:")
exercise = st.selectbox("Exercise:", exercises_list)
weight = st.number_input("Weight: ", min_value=0)
reps = st.number_input("Reps: ", min_value=0)
rir = st.number_input("RIR: ", min_value=0)

cursor.close()
conn.close()