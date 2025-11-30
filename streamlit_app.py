import streamlit as st
import psycopg2

cfg = st.secrets["neon"]
conn = psycopg2.connect(
    host=cfg["host"],
    dbname=cfg["dbname"],
    user=cfg["user"],
    password=cfg["password"],
    sslmode="require"
)
cursor = conn.cursor()

cursor.execute("SELECT name FROM app_user")
users = [row[0] for row in cursor.fetchall()]
st.title("Select who you are")
current_user = st.selectbox(users)

if "training_started" not in st.session_state:
    st.session_state["training_started"] = False

if not st.session_state["training_started"]:
    if st.button("Start Training"):
        st.session_state["training_started"] = True
    else:
        st.stop()

cursor.execute("SELECT name FROM exercice")
exercises_list = [row[0] for row in cursor.fetchall()]
# --- UI ---
st.write("Track down a series:")
exercise = st.selectbox("Exercise:", exercises_list)
weight = st.number_input("Weight: ", min_value=0)
reps = st.number_input("Reps: ", min_value=0)
rir = st.number_input("RIR: ", min_value=0)

cursor.close()
conn.close()