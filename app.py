import streamlit as st
from datetime import datetime
import pandas as pd

# --- IMPORT MODULI PERSONALIZZATI ---
from modules.auth import check_password
from modules.backend import GitHubBackend
from modules.activities import get_all_activities
from modules.intelligence import SuggestionEngine
from modules.analytics import AnalyticsEngine
# Nota: Importiamo l'admin panel solo se necessario, o qui per semplicità
from modules.admin import render_admin_panel 

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Life Logger", page_icon="🔐", layout="centered")

# --- 1. AUTENTICAZIONE & SICUREZZA ---
# check_password gestisce UI login e ritorna lo username se loggato
current_user = check_password()

if not current_user:
    st.stop() # Blocca l'esecuzione qui se non c'è login

# --- 2. SIDEBAR (LOGOUT & INFO) ---
with st.sidebar:
    st.write(f"Utente: **{current_user}**")
    if st.button("Logout", type="secondary"):
        # Pulisce tutto per sicurezza
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 3. INIZIALIZZAZIONE BACKEND ---
# CORREZIONE ERRORE PRECEDENTE: Passiamo lo username al backend!
# Il backend userà st.session_state['encryption_key'] per decriptare.
backend = GitHubBackend(username=current_user)

# Caricamento dati con Cache in Session State
# (Evita di scaricare e decriptare da GitHub a ogni interazione)
if 'data_snapshot' not in st.session_state:
    with st.spinner(f"🔓 Decriptazione diario di {current_user}..."):
        st.session_state['data_snapshot'] = backend.load_data()

df = st.session_state['data_snapshot']

st.title(f"📓 Diario di {current_user.capitalize()}")

# --- 4. GESTIONE TABS (CON ADMIN DINAMICO) ---
# Verifica se l'utente corrente è l'admin definito nei secrets
admin_user = st.secrets.get("ADMIN_USERNAME", "").lower()
is_admin = (current_user.lower() == admin_user)

tabs_labels = ["⚡ Diario", "📈 Statistiche", "💾 Dati"]
if is_admin:
    tabs_labels.append("🛠️ Admin")

# Crea i tabs
tabs = st.tabs(tabs_labels)

# --- TAB 1: DIARIO (LOGGING) ---
with tabs[0]:
    # A. Motore Suggerimenti (Intelligence)
    if not df.empty:
        engine = SuggestionEngine(df)
        prompts = engine.get_prompts()
        
        if prompts:
            st.info("✨ Suggerimenti Rapidi")
            cols = st.columns(len(prompts))
            for idx, p in enumerate(prompts):
                with cols[idx]:
                    if st.button(p['msg'], key=f"sugg_{idx}"):
                        st.session_state['prefill_activity'] = p['activity']
                        st.session_state['prefill_detail'] = p['dettaglio']
                        st.rerun()
            st.divider()

    # B. Form di Inserimento
    st.subheader("Nuova Attività")
    
    activities_list = get_all_activities()
    act_names = [a.name for a in activities_list]
    
    # Gestione pre-selezione da suggerimenti
    default_idx = 0
    if 'prefill_activity' in st.session_state:
        try:
            default_idx = act_names.index(st.session_state['prefill_activity'])
        except: pass
        
    selected_name = st.selectbox("Cosa stai facendo?", act_names, index=default_idx)
    
    # Recupera la classe dell'attività scelta
    selected_activity = next(a for a in activities_list if a.name == selected_name)
    
    with st.form("log_form", clear_on_submit=True):
        # Renderizza i campi specifici dell'attività
        data_collected = selected_activity.render_ui(df)
        
        # Override se c'era un suggerimento
        if 'prefill_detail' in st.session_state and st.session_state.get('prefill_activity') == selected_name:
            st.caption(f"Pre-impostato: {st.session_state['prefill_detail']}")
            data_collected['dettaglio'] = st.session_state['prefill_detail']
            # Pulizia post-render
            del st.session_state['prefill_detail']
            del st.session_state['prefill_activity']

        notes = st.text_area("Note", height=80)
        submitted = st.form_submit_button("Salva (Criptato) 🔒", type="primary")
        
        if submitted:
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "activity_type": selected_name,
                "note": notes,
                **data_collected
            }
            
            with st.spinner("Criptazione e Upload su GitHub..."):
                if backend.save_entry(entry):
                    st.success("Salvato al sicuro!")
                    # Invalida la cache per forzare il ricaricamento dei nuovi dati
                    del st.session_state['data_snapshot']
                    st.rerun()

# --- TAB 2: STATISTICHE ---
with tabs[1]:
    analytics = AnalyticsEngine(df)
    analytics.render_summary()

# --- TAB 3: DATI GREZZI ---
with tabs[2]:
    st.caption("Questi dati sono criptati su GitHub. Solo tu puoi vederli qui in chiaro.")
    st.dataframe(df.sort_values(by="timestamp", ascending=False) if not df.empty else pd.DataFrame())
    
    if st.button("🔄 Forza Ricaricamento da GitHub"):
        del st.session_state['data_snapshot']
        st.rerun()

# --- TAB 4: ADMIN (SOLO SE ABILITATO) ---
if is_admin:
    with tabs[3]:
        render_admin_panel()