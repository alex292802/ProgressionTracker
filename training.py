import streamlit as st
from datetime import datetime


def select_past_training(users_trainings):
    st.subheader("Mes entrainements précédents")

    selected = st.selectbox(
        "Entrainement du :",
        options=users_trainings,
        format_func=lambda t: t[1].strftime("%d/%m/%Y à %H:%M")
    )

    if st.button("Afficher le détail"):
        return selected[0]

    return None

def start_new_training(cursor, conn, user_id):
    cursor.execute("SELECT id, name FROM training_type")
    training_types = cursor.fetchall()
    st.subheader("Commencer un nouvel entrainement")
    selected = st.selectbox(
        "Type d'entrainement :",
        options=training_types,
        format_func=lambda t: t[1]
    )

    if st.button("Lancer mon entrainement"):
        cursor.execute(
            """
            INSERT INTO training (start_time, user_id, training_type_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (datetime.now(), user_id, selected[0])
        )
        conn.commit()
        return cursor.fetchone()[0]

    return None

def finish_training(cursor, conn, training_id):
    cursor.execute(
        "UPDATE training SET end_time = %s WHERE id = %s",
        (datetime.now(), training_id)
    )
    conn.commit()

    st.session_state.shown_training_id = training_id
    st.session_state.training_id = None

    st.success("Training terminé !")
    st.rerun()

def get_ongoing_training_id(trainings):
    for training_id, end_time in trainings:
        if end_time is None:
            return training_id
    return None

def render_training_recap(cursor, training_id):
    cursor.execute(
        """
        SELECT 
            e.name AS exercice,
            s.weight,
            s.reps,
            s.rir,
            s.created_at
        FROM series s
        JOIN exercice e ON e.id = s.exercice_id
        WHERE s.training_id = %s
        ORDER BY e.name, s.created_at
        """,
        (training_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        st.info("Aucune série enregistrée pour ce training.")
        return

    st.subheader("📊 Récapitulatif du training")

    current_exercice = None
    for exercice, weight, reps, rir, created_at in rows:
        if exercice != current_exercice:
            st.markdown(f"### 🏋️ {exercice}")
            current_exercice = exercice

        st.write(
            f"- **{weight} kg** × **{reps} reps** | RIR: {rir} "
            f"_(⏱ {created_at.strftime('%H:%M')})_"
        )
    
    if st.button("Terminer"):
        st.session_state.shown_training_id = None
        st.rerun()