import streamlit as st
from datetime import datetime
from collections import defaultdict


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

def get_ongoing_training_id(trainings):
    for training_id, end_time in trainings:
        if end_time is None:
            return training_id
    return None

def render_training_recap(cursor, conn, training_id):
    cursor.execute(
        """
        SELECT
            m.name AS muscle,
            e.name AS exercice,
            s.weight,
            s.reps,
            s.rir,
            s.created_at
        FROM series s
        JOIN exercice e ON e.id = s.exercice_id
        JOIN exercice_muscle em ON em.exercice_id = e.id
        JOIN muscle m ON m.id = em.muscle_id
        WHERE s.training_id = %s
        ORDER BY m.name, e.name, s.created_at;
        """,
        (training_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        st.info("Aucune série enregistrée pour ce training.")
    else:
        muscle_map = defaultdict(lambda: defaultdict(list))
        for muscle, exercice, weight, reps, rir, created_at in rows:
            muscle_map[muscle][exercice].append({
                "weight": weight,
                "reps": reps,
                "rir": rir,
            })

        st.subheader("📊 Récapitulatif du training")
        
        for muscle, exercices in muscle_map.items():
            total_series = sum(len(series) for series in exercices.values())
            st.markdown(f"## {muscle} — {total_series} séries")
            for exercice, series in exercices.items():
                with st.expander(f"{exercice} ({len(series)} séries)", expanded=False):
                    for i, s in enumerate(series, 1):
                        st.write(
                            f"- Série {i} : "
                            f"**{s['weight']} kg** | "
                            f"**{s['reps']} reps** | "
                            f"**RIR {s['rir']}**"
                        )
    if st.button("Retour"):
        st.session_state.shown_training_id = None
        st.rerun()
    if getattr(st.session_state, "training_id", None) is not None:
        if st.button("Terminer"):
            st.session_state.shown_training_id = None
            st.session_state.training_id = None
            cursor.execute(
                "UPDATE training SET end_time = %s WHERE id = %s",
                (datetime.now(), training_id)
            )
            conn.commit()
            st.success("Training terminé !")
            st.rerun()