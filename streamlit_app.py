import streamlit as st
import psycopg2
from datetime import datetime

cfg = st.secrets["neon"]
conn = psycopg2.connect(
    host=cfg["host"],
    dbname=cfg["dbname"],
    user=cfg["user"],
    password=cfg["password"],
    sslmode="require"
)
cursor = conn.cursor()

# TODO: better structure for user (for the moment, it supposes that user names are unique)
cursor.execute("SELECT id, name FROM app_user")
users = cursor.fetchall()
st.title("Select who you are")
current_user = st.selectbox("I am ", [t[1] for t in users])
user_id = next(u[0] for u in users if u[1] == current_user)

cursor.execute(
    "SELECT id FROM training WHERE end_time IS NULL AND user_id = %s",
    (user_id,)
)
on_going_trainings_ids = [row[0] for row in cursor.fetchall()]

if len(on_going_trainings_ids) == 0:
    training_id = None
else:
    training_id = on_going_trainings_ids[0]

if training_id is None:
    cursor.execute("SELECT id, name FROM training_type")
    training_types = cursor.fetchall()
    selected_training = st.selectbox(
        "Type d'entrainement :",
        [t[1] for t in training_types]
    )
    if st.button("Start Training"):
        training_type_id = next(t[0] for t in training_types if t[1] == selected_training)
        cursor.execute(
            """
            INSERT INTO training (start_time, user_id, training_type_id)
            VALUES (%s, %s, %s, %s)
            """,
            (datetime.now(), user_id, training_type_id)
        )
        training_id = cursor.fetchone()[0]
        conn.commit()
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
