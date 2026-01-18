import streamlit as st
from datetime import datetime
import pandas as pd

# Importa i moduli
from modules.auth import check_password
from modules.backend import GitHubBackend
from modules.activities import get_all_activities
from modules.intelligence import SuggestionEngine
from modules.analytics import AnalyticsEngine

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Life Logger", page_icon="📓", layout="centered")

# 1. Sicurezza
# MODIFICA FONDAMENTALE 1: Catturiamo l'utente che ha fatto login
current_user = check_password()

if not current_user:
    st.stop()

# 2. Inizializzazione Backend
# MODIFICA FONDAMENTALE 2: Passiamo l'utente al backend per aprire il file giusto
backend = GitHubBackend(username=current_user)

# Cache dei dati per velocità (si ricarica solo se svuoti la cache o ricarichi pagina)
if 'data_snapshot' not in st.session_state:
    with st.spinner(f"Decriptazione dati di {current_user}..."):
        st.session_state['data_snapshot'] = backend.load_data()

df = st.session_state['data_snapshot']

st.title(f"📓 Life Logger ({current_user})")

# --- UI TABS ---
tab_log, tab_stats, tab_raw = st.tabs(["⚡ Diario", "📈 Statistiche", "💾 Dati"])

# TAB 1: LOGGING
with tab_log:
    # A. Suggerimenti Intelligenti
    if not df.empty:
        engine = SuggestionEngine(df)
        prompts = engine.get_prompts()
        
        if prompts:
            st.caption("✨ Suggerimenti Rapidi")
            cols = st.columns(len(prompts))
            for idx, p in enumerate(prompts):
                with cols[idx]:
                    if st.button(p['msg'], key=p['id']):
                        # Pre-imposta session state per il form
                        st.session_state['prefill_activity'] = p['activity']
                        st.session_state['prefill_detail'] = p['dettaglio']
                        st.rerun()
            st.divider()

    # B. Form Principale
    st.subheader("Nuova Attività")
    
    # Recupera attività selezionata dai suggerimenti o default
    activities_list = get_all_activities()
    act_names = [a.name for a in activities_list]
    
    default_idx = 0
    if 'prefill_activity' in st.session_state:
        try:
            default_idx = act_names.index(st.session_state['prefill_activity'])
        except: pass
        
    selected_name = st.selectbox("Cosa stai facendo?", act_names, index=default_idx)
    
    # Trova la classe corrispondente
    selected_activity = next(a for a in activities_list if a.name == selected_name)
    
    with st.form("main_log_form", clear_on_submit=True):
        # Renderizza UI specifica
        data_collected = selected_activity.render_ui(df)
        
        # Sovrascrivi dettaglio se suggerito (hack rapido per prefill)
        if 'prefill_detail' in st.session_state and st.session_state.get('prefill_activity') == selected_name:
            st.info(f"Dettaglio pre-impostato: {st.session_state['prefill_detail']}")
            data_collected['dettaglio'] = st.session_state['prefill_detail']
            # Pulisci suggerimento per il prossimo giro
            del st.session_state['prefill_detail']
            del st.session_state['prefill_activity']

        notes = st.text_area("Note", height=80)
        # ... dentro app.py ...
        
        submitted = st.form_submit_button("Salva su GitHub 🚀", type="primary")
        
        if submitted:
            # 1. Recupera la data personalizzata se esiste, altrimenti usa oggi
            if "custom_date" in data_collected:
                # Combina la data scelta con l'ora attuale (per mantenere l'ordine cronologico preciso)
                chosen_date = data_collected["custom_date"]
                current_time = datetime.now().time()
                final_timestamp = datetime.combine(chosen_date, current_time).strftime("%Y-%m-%d %H:%M:%S")
                
                # Rimuovi la chiave temporanea 'custom_date' per non salvarla sporca nel DB
                del data_collected["custom_date"]
            else:
                final_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Costruisci l'entry
            entry = {
                "timestamp": final_timestamp,
                "activity_type": selected_name,
                "note": notes,
                **data_collected # Qui dentro ora c'è anche 'pagine_totali'
            }
            
            with st.spinner("Salvataggio in corso..."):
                # ... resto del codice di salvataggio uguale a prima ...
                if backend.save_entry(entry):
                    st.success("Salvato!")
                    del st.session_state['data_snapshot'] # Invalida cache locale
                    st.rerun() # Ricarica pagina per vedere dati aggiornati

# TAB 2: ANALYTICS
with tab_stats:
    analytics = AnalyticsEngine(df)
    analytics.render_summary()

# TAB 3: RAW DATA
with tab_raw:
    st.dataframe(df.sort_values(by="timestamp", ascending=False) if not df.empty else pd.DataFrame())
    if st.button("Forza Ricaricamento Dati"):
        del st.session_state['data_snapshot']
        st.rerun()