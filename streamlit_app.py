import streamlit as st
import psycopg2

from training import render_training_recap, get_ongoing_training_id, start_new_training, select_past_training, finish_training
from login import login
from series import add_series

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
    user_id = login(cursor)
    if user_id:
        st.session_state.user_id = user_id
        st.rerun()
else:
    cursor.execute(
        "SELECT id, end_time FROM training WHERE user_id = %s ORDER BY end_time DESC",
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
        add_series(cursor, conn, st.session_state.training_id)
        if st.button("Terminer le training"):
            finish_training(cursor, conn, st.session_state.training_id)

cursor.close()
conn.close()
