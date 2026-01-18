import streamlit as st
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, date

class BaseActivity(ABC):
    @property
    @abstractmethod
    def name(self): pass
    @abstractmethod
    def render_ui(self, history_df: pd.DataFrame) -> dict: pass

# --- NUOVA VERSIONE LETTURA ---
class ReadingActivity(BaseActivity):
    name = "📚 Lettura"

    def render_ui(self, df: pd.DataFrame):
        # 1. SELEZIONE DATA
        # Default: Oggi
        log_date = st.date_input("Data Lettura", value=date.today())
        
        # 2. LOGICA LIBRI ESISTENTI
        existing_books = []
        book_metadata = {} # Dizionario per ricordare le pagine totali dei libri vecchi
        
        if not df.empty and 'dettaglio' in df.columns:
            # Filtra solo le righe di lettura
            reading_df = df[df['activity_type'] == self.name]
            existing_books = reading_df['dettaglio'].dropna().unique().tolist()
            
            # Cerca di recuperare le 'pagine_totali' dall'ultimo log di ogni libro
            if 'pagine_totali' in df.columns:
                for book in existing_books:
                    # Prendi il valore massimo inserito per quel libro (così se hai corretto, prende l'ultimo)
                    try:
                        max_p = reading_df[reading_df['dettaglio'] == book]['pagine_totali'].max()
                        if pd.notna(max_p):
                            book_metadata[book] = int(max_p)
                    except:
                        pass

        # 3. UI SELEZIONE
        col_mode, col_book = st.columns([1, 2])
        with col_mode:
            mode = st.radio("Modalità", ["In Corso", "Nuovo"], label_visibility="collapsed")
        
        selected_title = ""
        total_pages_val = 0

        if mode == "In Corso" and existing_books:
            with col_book:
                selected_title = st.selectbox("Seleziona Libro", existing_books)
                # Auto-recupera le pagine totali se esistono
                total_pages_val = book_metadata.get(selected_title, 0)
        else:
            with col_book:
                selected_title = st.text_input("Titolo Nuovo Libro")
                total_pages_val = 0 # Reset per nuovo libro

        # 4. INPUT DATI NUMERICI
        c1, c2 = st.columns(2)
        with c1:
            # Se conosciamo le pagine totali, le mostriamo, altrimenti l'utente le inserisce
            total_pages = st.number_input(
                "Pagine Totali del libro", 
                min_value=0, 
                value=total_pages_val,
                help="Serve per calcolare la % di completamento"
            )
        with c2:
            pages_read = st.number_input("Pagine lette in questa sessione", min_value=1, step=1)

        # 5. CALCOLO PERCENTUALE (Visuale)
        if total_pages > 0:
            # Cerchiamo quante pagine avevi letto PRIMA di oggi per questo libro
            already_read = 0
            if not df.empty and 'dettaglio' in df.columns and selected_title:
                # Somma tutte le metriche (pagine lette) per questo libro
                subset = df[(df['activity_type'] == self.name) & (df['dettaglio'] == selected_title)]
                already_read = subset['metrica'].sum()
            
            current_total = already_read + pages_read
            pct = (current_total / total_pages) * 100
            if pct > 100: pct = 100
            st.progress(pct / 100, text=f"Progresso stimato: {int(pct)}% ({current_total}/{total_pages})")

        return {
            "dettaglio": selected_title,
            "metrica": pages_read,
            "unita": "pagine",
            "pagine_totali": total_pages, # Salviamo questo dato per usarlo in futuro
            "custom_date": log_date # Passiamo la data scelta al backend
        }

# --- LE ALTRE CLASSI RIMANGONO UGUALI (Sport, Movie, ecc) ---
# Assicurati di includere anche le altre classi qui sotto o lasciarle invariate
# ...
class SportActivity(BaseActivity):
    name = "💪 Sport"
    def render_ui(self, df):
        # Aggiungo anche qui la data per coerenza, se vuoi
        log_date = st.date_input("Data Sport", value=date.today())
        types = ["Palestra", "Corsa", "Nuoto", "Yoga", "Bici"]
        detail = st.selectbox("Tipo", types)
        metric = st.number_input("Minuti", step=5, min_value=5)
        return {"dettaglio": detail, "metrica": metric, "unita": "minuti", "custom_date": log_date}

class MovieActivity(BaseActivity):
    name = "🎬 Film/Serie"
    def render_ui(self, df):
        log_date = st.date_input("Data Visione", value=date.today())
        detail = st.text_input("Titolo")
        metric = st.slider("Voto", 1, 10)
        return {"dettaglio": detail, "metrica": metric, "unita": "voto", "custom_date": log_date}

class GenericActivity(BaseActivity):
    name = "📝 Altro"
    def render_ui(self, df):
        log_date = st.date_input("Data", value=date.today())
        detail = st.text_input("Attività")
        metric = st.number_input("Valore (opzionale)")
        return {"dettaglio": detail, "metrica": metric, "unita": "generic", "custom_date": log_date}

def get_all_activities():
    return [ReadingActivity(), SportActivity(), MovieActivity(), GenericActivity()]