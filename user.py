import streamlit as st
import secrets
from argon2 import PasswordHasher
from datetime import datetime, timedelta

ph = PasswordHasher()

def generate_invitation_token():
    token = secrets.token_urlsafe(16)
    return token

def render_form(form_key, submit_label):
    with st.form(form_key):
        user_name = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button(submit_label)
        return submitted, user_name, password


def are_fields_filled(username, password):
    if not username or not password:
        st.warning("Veuillez remplir tous les champs")
        return False
    return True

def fetch_user(cursor, username, with_password=False):
    base_request = "SELECT id"
    if with_password:
        base_request += ", hashed_password"
    cursor.execute(
        base_request + " FROM app_user WHERE user_name=%s",
        (username,)
    )
    return cursor.fetchone()


def login(cursor):
    submitted, user_name, password = render_form("login_form", "Se connecter")
    if submitted:
        if not are_fields_filled(user_name, password):
            return
        user = fetch_user(cursor, user_name, True)
        if not user:
            st.error("Nom d'utilisateur inconnu")
            return
        user_id, hashed_password = user
        try:
            if ph.verify(hashed_password, password):
                st.success("Login réussi !")
                return user_id
        except Exception:
            st.error("Mot de passe incorrect")
            return


def is_valid_token(cursor, token):
    cursor.execute(
        "SELECT expires_at FROM invitations WHERE token=%s", 
        (token,)
    )
    row = cursor.fetchone()
    if row is None:
        return False
    expires_at = row[0]
    if datetime.utcnow() > expires_at:
        return False
    return True


def add_user(cursor, token=None):
    submitted, user_name, password = render_form("signup_form", "Créer mon compte")
    if submitted:
        if not are_fields_filled(user_name, password):
            return
        user = fetch_user(cursor, user_name)
        if user:
            st.error("Nom d'utilisateur déjà utilisé")
            return   
        hashed = ph.hash(password)
        try:
            cursor.execute(
                """
                INSERT INTO app_user (user_name, hashed_password, invitation)
                VALUES (%s, %s, %s)
                """,
                (user_name, hashed, token)
            )
            if token:
                cursor.execute(
                    "UPDATE invitations SET is_expired = TRUE WHERE token=%s",
                    (token,)
                )
            st.success("Compte créé avec succès !")
        except Exception as e:
            st.error(f"Erreur lors de la création du compte")
            
def invite_friend(cursor, current_user_id, base_url):
    cursor.execute(
        """
        SELECT created_at FROM invitations
        WHERE created_by = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (current_user_id,)
    )
    last_invitation_date = cursor.fetchone()
    
    if last_invitation_date:
        if datetime.utcnow() - last_invitation_date < timedelta(hours=24):
            st.error("Vous avez déjà créé une invitation dans les dernières 24 heures.")
            return

    token = generate_invitation_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    cursor.execute(
        """
        INSERT INTO invitations (token, created_by, created_at, expires_at, is_expired)
        VALUES (%s, %s, %s, %s, FALSE)
        """,
        (token, current_user_id, datetime.utcnow(), expires_at)
    )
    
    cursor.connection.commit()
    
    invitation_link = f"{base_url}?token={token}"
    st.success("Invitation créée avec succès !")
    st.code(invitation_link, language="text")