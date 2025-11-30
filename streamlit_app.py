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

cursor.execute("SELECT id FROM training WHERE end_time IS NULL")
on_going_trainings_ids = [row[0] for row in cursor.fetchall()]

if len(on_going_trainings_ids) == 0:
    training_id = None
else:
    training_id = on_going_trainings_ids[0]

if training_id is None:
    cursor.execute("SELECT name FROM training_type")
    training_types = [row[0] for row in cursor.fetchall()]
    st.selectbox("Type d'entrainement :", training_types)
    if st.button("Start Training"):
        # TODO: add training to databse
        training_started = True
else:
    cursor.execute("SELECT name FROM exercice")
    exercises_list = [row[0] for row in cursor.fetchall()]
    st.write("Track down a series:")
    exercise = st.selectbox("Exercise:", exercises_list)
    weight = st.number_input("Poids: ", min_value=0)
    reps = st.number_input("Reps: ", min_value=0)
    rir = st.number_input("RIR: ", min_value=0)

cursor.close()
conn.close()
