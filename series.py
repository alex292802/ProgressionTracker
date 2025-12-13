import streamlit as st
from datetime import datetime

def add_series(cursor, conn, training_id):
    cursor.execute("SELECT id, name FROM exercice")
    exercises = cursor.fetchall()
    st.subheader("Ajouter une série")
    exercise = st.selectbox("Exercice:", exercises, format_func=lambda e: e[1])
    weight = st.number_input("Poids:", min_value=0)
    reps = st.number_input("Reps:", min_value=0)
    rir = st.number_input("RIR:", min_value=0)

    if st.button("Ajouter la série"):
        cursor.execute(
            """
            INSERT INTO series (training_id, exercice_id, weight, reps, rir, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (training_id, exercise[0], weight, reps, rir, datetime.now())
        )
        conn.commit()
        st.success("Série ajoutée avec succès !")
