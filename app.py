import streamlit as st
import yaml
import pandas as pd
from datetime import datetime
from github import Github
import json

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Git Life Logger", page_icon="📓")
st.title("📓 Git Life Logger")

# Recupera i segreti (configurati su Streamlit Cloud)
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"] # Es: "tuonome/life-logger"
FILE_PATH = "data.yaml"

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
