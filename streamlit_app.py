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

cursor.execute("SELECT name FROM app_user")
users = [row[0] for row in cursor.fetchall()]
st.title("Select who you are")
current_user = st.selectbox("I am ", users)

training_started = False
if not training_started:
    cursor.execute("SELECT name FROM training_type")
    training_types = [row[0] for row in cursor.fetchall()]
    st.selectbox("Type d'entrainement :", training_types)
    current_user = st.selectbox("I am ", users)
    if st.button("Start Training"):
        # TODO: add training to databse
        training_started = True


cursor.execute("SELECT name FROM exercice")
exercises_list = [row[0] for row in cursor.fetchall()]
st.write("Track down a series:")
exercise = st.selectbox("Exercise:", exercises_list)
weight = st.number_input("Weight: ", min_value=0)
reps = st.number_input("Reps: ", min_value=0)
rir = st.number_input("RIR: ", min_value=0)

cursor.close()
conn.close()