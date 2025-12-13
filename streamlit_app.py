import streamlit as st
import psycopg2
from datetime import datetime

from training import render_training_recap, get_ongoing_training_id, start_new_training, select_past_training
from user import select_user

cfg = st.secrets["neon"]
conn = psycopg2.connect(
    host=cfg["host"],
    dbname=cfg["dbname"],
    user=cfg["user"],
    password=cfg["password"],
    sslmode="require"
)
cursor = conn.cursor()

st.title("Progression Tracker")

if "user_id" not in st.session_state:
    user_id = select_user(cursor)
    if user_id:
        st.session_state.user_id = user_id
        st.rerun()
else:
    cursor.execute(
        "SELECT id, end_time FROM training WHERE user_id = %s",
        (st.session_state.user_id,)
    )
    users_trainings = cursor.fetchall()
    st.session_state.training_id = get_ongoing_training_id(users_trainings)
    if st.session_state.training_id is None:
        if getattr(st.session_state, "shown_training_id", None) is None:
            st.session_state.training_id = start_new_training(cursor, conn, st.session_state.user_id)
            st.session_state.shown_training_id = select_past_training(users_trainings)
        else:
            render_training_recap(cursor, st.session_state.shown_training_id)
    else:
        cursor.execute("SELECT id, name FROM exercice")
        exercises_list = cursor.fetchall()
        st.write("Ajouter une série:")
        exercise = st.selectbox("Exercice:", options=exercises_list, format_func=lambda e: e[1])
        weight = st.number_input("Poids: ", min_value=0)
        reps = st.number_input("Reps: ", min_value=0)
        rir = st.number_input("RIR: ", min_value=0)

        if st.button("Ajouter la série"):
            exercise_id = exercise[0]
            cursor.execute(
                """
                INSERT INTO series (training_id, exercice_id, weight, reps, rir, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (st.session_state.training_id, exercise_id, weight, reps, rir, datetime.now())
            )
            conn.commit()
            st.success("Série ajoutée avec succès !")

        if st.button("Terminer le training"):
            cursor.execute(
                "UPDATE training SET end_time = %s WHERE id = %s",
                (datetime.now(), st.session_state.training_id)
            )
            conn.commit()
            st.session_state.shown_training_id = st.session_state.training_id
            st.session_state.training_id = None
            st.success("Training terminé !")
            st.rerun()

cursor.close()
conn.close()
