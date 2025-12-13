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