import streamlit as st

def select_user(cursor):
    cursor.execute("SELECT id, name FROM app_user")
    users = cursor.fetchall()

    selected_user = st.selectbox(
        "Je suis:",
        options=users,
        format_func=lambda u: u[1]
    )

    if st.button("Confirmer"):
        return selected_user[0]

    return None
