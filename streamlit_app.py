import streamlit as st
import psycopg2
from datetime import datetime


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
    current_user = st.selectbox("Je suis:", [t[1] for t in users])
    if st.button(f"Confirmer que je suis {current_user}"):
        st.session_state.user_id = next(u[0] for u in users if u[1] == current_user)
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
            selected_training = st.selectbox(
                "Type d'entrainement :",
                [t[1] for t in training_types]
            )
            st.subheader("Commencer un nouvel entrainement")
            if st.button("Lancer mon entrainement"):
                training_type_id = next(t[0] for t in training_types if t[1] == selected_training)
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
            past_training_id = st.selectbox("Entrainement du :", [t["id"] for t in users_trainings])
            if st.button("Afficher le détail"):
                st.session_state.shown_training_id = past_training_id
                st.rerun()
        else:
            render_training_recap(cursor, st.session_state.shown_training_id)
    else:
        cursor.execute("SELECT id, name FROM exercice")
        exercises_list = cursor.fetchall()
        st.write("Ajouter une série:")
        exercise = st.selectbox("Exercice:", [row[1] for row in exercises_list])
        weight = st.number_input("Poids: ", min_value=0)
        reps = st.number_input("Reps: ", min_value=0)
        rir = st.number_input("RIR: ", min_value=0)

        if st.button("Ajouter la série"):
            exercise_id = next(e[0] for e in exercises_list if e[1] == exercise)
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
