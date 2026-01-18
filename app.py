import streamlit as st
import yaml
import pandas as pd
from datetime import datetime
from github import Github

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Git Life Logger", page_icon="🔒")

# --- SISTEMA DI AUTENTICAZIONE ---
def check_password():
    """Ritorna True se l'utente ha inserito la password corretta."""

    def password_entered():
        """Controlla se la password inserita corrisponde a quella nei segreti."""
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Pulisce la password dalla memoria per sicurezza
        else:
            st.session_state["password_correct"] = False

    # Se la password è già stata verificata in questa sessione
    if st.session_state.get("password_correct", False):
        return True

    # Interfaccia di Login
    st.title("🔒 Login Richiesto")
    st.text_input(
        "Inserisci la password per accedere al Logger:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password errata.")

    return False

# --- BLOCCO DI SICUREZZA ---
if not check_password():
    st.stop()  # FERMA TUTTO QUI se non sei loggato. Niente sotto viene eseguito.

# =========================================================
# DA QUI IN GIÙ INCOLLA IL RESTO DEL TUO VECCHIO CODICE
# =========================================================

st.title("📓 Git Life Logger")

# Recupera i segreti 
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data.yaml"

# ... (tutto il resto delle funzioni get_github_file, load_data, save_to_github, interfaccia, etc.)
# ...

# --- GESTIONE GITHUB ---
def get_github_file():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        return repo, contents
    except:
        # Se il file non esiste, ritorna solo il repo per crearlo
        return repo, None

def load_data():
    _, contents = get_github_file()
    if contents:
        # Decodifica il contenuto dal b64/bytes
        yaml_content = contents.decoded_content.decode("utf-8")
        # Se il file è vuoto o ha solo [], ritorna lista vuota
        data = yaml.safe_load(yaml_content)
        if data is None: return []
        return data
    return []

def save_to_github(new_entry):
    repo, contents = get_github_file()
    
    # 1. Carica dati attuali
    current_data = load_data()
    
    # 2. Aggiungi nuova entry
    current_data.append(new_entry)
    
    # 3. Converti in stringa YAML
    # allow_unicode=True per gestire accenti ed emoji
    new_yaml_content = yaml.dump(current_data, sort_keys=False, allow_unicode=True)
    
    # 4. Push (Commit) su GitHub
    if contents:
        repo.update_file(
            path=contents.path,
            message=f"Log: {new_entry['attivita']} - {datetime.now().strftime('%Y-%m-%d')}",
            content=new_yaml_content,
            sha=contents.sha
        )
    else:
        repo.create_file(
            path=FILE_PATH,
            message="Initial commit log",
            content=new_yaml_content
        )

# --- CARICAMENTO DATI ---
data_list = load_data()
df = pd.DataFrame(data_list)

# --- INTERFACCIA ---
with st.container():
    st.header("Nuovo Log")
    
    with st.form("log_form", clear_on_submit=True):
        activity = st.selectbox(
            "Attività",
            ["Lettura", "Film/Serie", "Studio", "Progetto Side", "Workout"]
        )
        
        # Logica condizionale per i dettagli
        detail = ""
        metric = 0.0
        
        # Sezione Lettura intelligente
        if activity == "Lettura":
            # Trova libri unici già loggati
            existing_books = []
            if not df.empty and 'dettaglio' in df.columns:
                existing_books = df[df['attivita'] == "Lettura"]['dettaglio'].unique().tolist()
            
            mode = st.radio("Libro", ["In Corso", "Nuovo"], horizontal=True)
            if mode == "In Corso" and existing_books:
                detail = st.selectbox("Seleziona Titolo", existing_books)
            else:
                detail = st.text_input("Titolo Nuovo Libro")
            
            metric = st.number_input("Pagine lette", step=1)
            
        elif activity == "Film/Serie":
            detail = st.text_input("Titolo")
            metric = st.slider("Rating", 1, 10)
            
        else:
            detail = st.text_input("Dettaglio (opzionale)")
            metric = st.number_input("Valore (opzionale)")

        notes = st.text_area("Note")
        
        submitted = st.form_submit_button("Push to GitHub 🚀")
        
        if submitted:
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "attivita": activity,
                "dettaglio": detail,
                "metrica": metric,
                "note": notes
            }
            
            with st.spinner('Commit in corso su GitHub...'):
                save_to_github(entry)
            
            st.success("Salvato! YAML aggiornato.")
            st.cache_data.clear() # Forza ricaricamento
            st.rerun()

# --- STATS DASHBOARD ---
st.divider()
if not df.empty:
    st.subheader("I tuoi dati (dal YAML)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Totale Logs", len(df))
    with col2:
        # Esempio somma pagine
        if 'metrica' in df.columns:
            pagine = df[df['attivita']=="Lettura"]['metrica'].sum()
            st.metric("Pagine Totali", int(pagine))

    # Tabella Raw Data
    with st.expander("Ispeziona YAML renderizzato"):
        st.dataframe(df.sort_values(by="timestamp", ascending=False))
else:
    st.info("Nessun dato nel file YAML ancora.")
