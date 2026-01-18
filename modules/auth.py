import streamlit as st
import yaml
import time
from github import Github
from modules.crypto_utils import verify_password

def check_password():
    if st.session_state.get("authenticated", False):
        return st.session_state["username"]

    st.title("🔒 Secure Login")
    
    with st.form("login"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi")

    if submitted:
        # 1. Connettiti a GitHub usando SOLO il token generico (nei secrets)
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        
        try:
            # 2. Scarica il file users.yaml (che contiene gli HASH, non le password)
            content = repo.get_contents("users.yaml")
            users_db = yaml.safe_load(content.decoded_content.decode())
            
            # 3. Verifica: Esiste l'utente? L'hash coincide?
            if user_input in users_db:
                stored_hash = users_db[user_input]
                if verify_password(pass_input, stored_hash):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    # SALVIAMO LA PASSWORD IN MEMORIA (TEMPORANEA):
                    # Serve per decriptare i dati dopo! Streamlit la dimentica al refresh.
                    st.session_state["encryption_key"] = pass_input 
                    
                    st.success("Accesso consentito. Decriptazione in corso...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Password errata.")
            else:
                st.error("Utente non trovato.")
                
        except Exception as e:
            st.error(f"Errore connessione DB Utenti: {e}")

    return None