import streamlit as st
import psycopg2
from datetime import datetime

from training_overview import render_training_recap

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
    cursor.execute("SELECT id, name FROM app_user")
    users = cursor.fetchall()
    current_user = st.selectbox("Je suis:", options=users, format_func=lambda u: u[1])
    if st.button(f"Confirmer"):
        st.session_state.user_id = current_user[0]
        st.rerun()
else:
    cursor.execute(
        "SELECT id, end_time FROM training WHERE user_id = %s",
        (st.session_state.user_id,)
    )
    users_trainings = cursor.fetchall()
    on_going_trainings_ids = [row[0] for row in users_trainings if row[1] is None]

    if len(on_going_trainings_ids) == 0:
        st.session_state.training_id = None
    else:
        st.session_state.training_id = on_going_trainings_ids[0]

    if st.session_state.training_id is None:
        if getattr(st.session_state, "shown_training_id", None) is None:
            cursor.execute("SELECT id, name FROM training_type")
            training_types = cursor.fetchall()
            st.subheader("Commencer un nouvel entrainement")
            selected_training = st.selectbox(
                "Type d'entrainement :",
                options=training_types,
                format_func=lambda t: t[1]
            )
            if st.button("Lancer mon entrainement"):
                training_type_id = selected_training[0]
                cursor.execute(
                    """
                    INSERT INTO training (start_time, user_id, training_type_id)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (datetime.now(), st.session_state.user_id, training_type_id)
                )
                st.session_state.training_id = cursor.fetchone()[0]
                conn.commit()
                st.rerun()
            st.subheader("Mes entrainements précédents")
            past_training = st.selectbox(
                "Entrainement du :",
                options=users_trainings,
                format_func=lambda t: t[1].strftime("%d/%m/%Y à %H:%M")
            )
            past_training_id = past_training[0]
            if st.button("Afficher le détail"):
                st.session_state.shown_training_id = past_training_id
                st.rerun()
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
