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
        st.session_state.shown_training_id = selected[0]
        st.rerun()


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
        st.session_state.training_id = cursor.fetchone()[0]
        st.rerun()


def get_ongoing_training_id(trainings):
    for training_id, end_time in trainings:
        if end_time is None:
            return training_id
    return None


def fetch_training_series(cursor, training_id):
    cursor.execute(
        """
        SELECT
            s.id,
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
    return cursor.fetchall()


def build_muscle_map(rows):
    muscle_map = defaultdict(lambda: defaultdict(list))
    for series_id, muscle, exercice, weight, reps, rir, created_at in rows:
        muscle_map[muscle][exercice].append({
            "id": series_id,
            "weight": float(weight),
            "reps": reps,
            "rir": rir,
            "created_at": created_at,
        })
    return muscle_map


def render_series_readonly(index, series):
    st.write(
        f"- Série {index} : "
        f"**{series['weight']} kg** | "
        f"**{series['reps']} reps** | "
        f"**RIR {series['rir']}**"
    )
    
    
def render_series_edit(cursor, conn, series, muscle):
    # integers define relative width
    cols = st.columns([2, 2, 2, 1, 1])
    key = f"{series['id']}_{muscle}"
    weight = cols[0].number_input(
        "Poids",
        value=series["weight"],
        step=1.0,
        min_value=0.0,
        key=f"w_{key}"
    )
    reps = cols[1].number_input(
        "Répétitions",
        value=series["reps"],
        step=1,
        min_value=0,
        key=f"r_{key}"
    )
    rir = cols[2].number_input(
        "RIR",
        value=series["rir"],
        step=1,
        min_value=0,
        key=f"rir_{key}"
    )
    if cols[3].button("💾", key=f"save_{key}", use_container_width=True):
        cursor.execute(
            """
            UPDATE series
            SET weight = %s, reps = %s, rir = %s
            WHERE id = %s
            """,
            (weight, reps, rir, series["id"])
        )
        conn.commit()
        st.success("Série modifiée")
        st.rerun()
    if cols[4].button("🗑", key=f"del_{key}", use_container_width=True):
        cursor.execute(
            "DELETE FROM series WHERE id = %s",
            (series["id"],)
        )
        conn.commit()
        st.success("Série supprimée")
        st.rerun()


def render_muscle_block(cursor, conn, muscle, exercices, edit_mode):
    total_series = sum(len(series) for series in exercices.values())
    st.markdown(f"## {muscle} — {total_series} séries")
    for exercice, series in exercices.items():
        with st.expander(f"{exercice} ({len(series)} séries)", expanded=False):
            for i, s in enumerate(series, 1):
                if edit_mode:
                    render_series_edit(cursor, conn, s, muscle)
                else:
                    render_series_readonly(i, s)
                    

def render_training_actions(cursor, conn, training_id):
    if st.button("Retour"):
        st.session_state.shown_training_id = None
        st.session_state.edit_mode = False
        st.rerun()
        
    if st.button("Modifier mon entrainement"):
        st.session_state.edit_mode = True
        st.rerun()

    if st.button("Supprimer mon entrainement"):
        cursor.execute(
            "DELETE FROM training WHERE id = %s",
            (training_id,)
        )
        conn.commit()
        st.session_state.shown_training_id = None
        st.session_state.training_id = None
        st.session_state.edit_mode = False
        st.success("Entrainement supprimé")
        st.rerun()

    if getattr(st.session_state, "training_id", None) is not None:
        if st.button("Terminer"):
            cursor.execute(
                "UPDATE training SET end_time = %s WHERE id = %s",
                (datetime.now(), training_id)
            )
            conn.commit()
            st.session_state.training_id = None
            st.session_state.shown_training_id = None
            st.session_state.edit_mode = False
            st.success("Training terminé !")
            st.rerun()


def render_training_recap(cursor, conn, training_id):
    rows = fetch_training_series(cursor, training_id)

    if not rows:
        st.info("Aucune série enregistrée pour ce training.")
    else:
        muscle_map = build_muscle_map(rows)
        st.subheader("📊 Récapitulatif du training")
        for muscle, exercices in muscle_map.items():
            render_muscle_block(
                cursor,
                conn,
                muscle,
                exercices,
                edit_mode=st.session_state.get("edit_mode", False)
            )

    render_training_actions(cursor, conn, training_id)