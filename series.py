import streamlit as st
from datetime import datetime

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

    cursor.execute(
        """
        SELECT
            t.end_time,
            s.weight,
            s.reps,
            s.rir
        FROM series s
        JOIN training t ON t.id = s.training_id
        WHERE s.exercice_id = %s
          AND t.id <> %s
          AND t.end_time IS NOT NULL
        ORDER BY t.end_time DESC, s.created_at ASC
        LIMIT 15
        """,
        (exercise[0], training_id)
    )

    history = cursor.fetchall()

    if history:
        with st.expander("📈 Historique de l'exercice", expanded=False):
            for end_time, weight, reps, rir in history:
                st.write(
                    f"{end_time:%d/%m} → "
                    f"{weight} kg | "
                    f"{reps} reps | "
                    f"RIR {rir}"
                )
    else:
        st.caption("Aucun historique pour cet exercice.")

    if history:
        _, last_weight, last_reps, last_rir = history[0]
    else:
        last_weight, last_reps, last_rir = 0, 0, 0
    
    weight = st.number_input("Poids:", min_value=0.0, value=float(last_weight))
    reps = st.number_input("Reps:", min_value=0, value=int(last_reps))
    rir = st.number_input("RIR:", min_value=0, value=int(last_rir))

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
        st.rerun()
