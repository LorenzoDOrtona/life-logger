import streamlit as st
import yaml
import time
import bcrypt
from github import Github
from modules.crypto_utils import verify_password

def check_password():
    """Gestisce Login e Registrazione. Ritorna username se loggato."""
    
    if st.session_state.get("authenticated", False):
        return st.session_state["username"]

    st.title("🔐 Life Logger")

    # Creiamo due tab: uno per entrare, uno per creare account
    tab_login, tab_register = st.tabs(["Accedi", "Crea Account"])

    # --- TAB 1: LOGIN CLASSICO ---
    with tab_login:
        with st.form("login_form"):
            user_input = st.text_input("Username").strip().lower()
            pass_input = st.text_input("Password", type="password")
            submitted_login = st.form_submit_button("Entra")

        if submitted_login:
            authenticate_user(user_input, pass_input)

    # --- TAB 2: REGISTRAZIONE NUOVO UTENTE ---
    with tab_register:
        st.caption("Serve un codice invito per registrarsi.")
        with st.form("register_form"):
            new_user = st.text_input("Nuovo Username").strip().lower()
            new_pass = st.text_input("Nuova Password", type="password")
            confirm_pass = st.text_input("Conferma Password", type="password")
            invite_code = st.text_input("Codice Invito")
            submitted_reg = st.form_submit_button("Registrati")

        if submitted_reg:
            register_user(new_user, new_pass, confirm_pass, invite_code)

    return None

# --- LOGICA DI AUTHENTICAZIONE ---
def authenticate_user(username, password):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        
        # Scarica users.yaml
        content = repo.get_contents("users.yaml")
        users_db = yaml.safe_load(content.decoded_content.decode()) or {}
        
        if username in users_db:
            stored_hash = users_db[username]
            if verify_password(password, stored_hash):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["encryption_key"] = password
                st.success("Login effettuato! 🔓")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Password errata.")
        else:
            st.error("Utente non trovato.")
            
    except Exception as e:
        st.error(f"Errore di connessione: {e}")

# --- LOGICA DI REGISTRAZIONE ---
def register_user(username, password, confirm, code):
    # 1. Validazione Input
    if not username or not password:
        st.warning("Compila tutti i campi.")
        return
    if password != confirm:
        st.error("Le password non coincidono.")
        return
    if code != st.secrets.get("INVITE_CODE", ""):
        st.error("Codice invito non valido! Chiedi all'admin.")
        return

    try:
        with st.spinner("Creazione utente su GitHub..."):
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["REPO_NAME"])
            
            # 2. Scarica DB attuale (per evitare sovrascritture accidentali)
            contents = repo.get_contents("users.yaml")
            users_db = yaml.safe_load(contents.decoded_content.decode()) or {}
            
            # 3. Controllo duplicati
            if username in users_db:
                st.error("Username già in uso. Scegline un altro.")
                return

            # 4. Genera Hash sicuro
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # 5. Aggiorna DB locale
            users_db[username] = hashed
            
            # 6. Push su GitHub
            new_yaml = yaml.dump(users_db, default_flow_style=False)
            repo.update_file(
                contents.path, 
                f"New User: {username}", 
                new_yaml, 
                contents.sha
            )
            
            st.success(f"Benvenuto {username}! Account creato. Ora puoi accedere.")
            
    except Exception as e:
        st.error(f"Errore durante la registrazione: {e}")