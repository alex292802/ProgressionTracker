import streamlit as st
from datetime import datetime
from collections import defaultdict

def add_series(cursor, conn, training_id):
    cursor.execute("SELECT id, name FROM exercice ORDER BY name")
    exercises = cursor.fetchall()
    st.subheader("Ajouter une série")
    exercise = st.selectbox(
        "Exercice:",
        exercises,
        format_func=lambda e: e[1],
        key="exercise_select"
    )

    weight = st.number_input("Poids:", min_value=0.0, value=0.0, key="weight_input")
    reps = st.number_input("Reps:", min_value=0, value=0, key="reps_input")
    rir = st.number_input("RIR:", min_value=0, value=0, key="rir_input")

    if st.button("Ajouter la série"):
        curr_date = datetime.now()
        cursor.execute(
            """
            INSERT INTO series (training_id, exercice_id, weight, reps, rir, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (training_id, exercise[0], weight, reps, rir, curr_date)
        )
        conn.commit()
        st.success("Série ajoutée avec succès !")

    cursor.execute(
        """
        SELECT t.start_time, s.weight, s.reps, s.rir
        FROM series s
        JOIN training t ON t.id = s.training_id
        WHERE s.exercice_id = %s
          AND t.id <> %s
        ORDER BY t.start_time DESC, s.created_at ASC
        LIMIT 15
        """,
        (exercise[0], training_id)
    )
    history = cursor.fetchall()

    if history:
        grouped = defaultdict(list)
        for end_time, w, r, rr in history:
            grouped[end_time.date()].append((w, r, rr))

        with st.expander("📈 Historique de l'exercice", expanded=False):
            for day in sorted(grouped.keys(), reverse=True):
                st.markdown(f"**{day:%d/%m/%Y}**")
                for w, r, rr in grouped[day]:
                    st.write(f"- {w} kg | {r} reps | RIR {rr}")
    else:
        st.caption("Aucun historique pour cet exercice.")
