import streamlit as st
from argon2 import PasswordHasher

ph = PasswordHasher()

def login(cursor):
    st.subheader("Login")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if not username or not password:
            st.warning("Veuillez remplir tous les champs")
            return None

        cursor.execute(
            "SELECT id, hashed_password FROM app_user WHERE user_name=%s",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            st.error("Nom d'utilisateur inconnu")
            return None

        user_id, hashed_password = row

        try:
            if ph.verify(hashed_password, password):
                st.success("Login réussi !")
                return user_id
        except Exception:
            st.error("Mot de passe incorrect")
            return None
