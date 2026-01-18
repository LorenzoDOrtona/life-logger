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
        log_date = st.date_input("Data Lettura", value=date.today())
        
        # 2. RECUPERO DATI STORICI
        existing_books = []
        book_metadata = {} 
        
        if not df.empty and 'dettaglio' in df.columns:
            reading_df = df[df['activity_type'] == self.name]
            existing_books = reading_df['dettaglio'].dropna().unique().tolist()
            
            if 'pagine_totali' in df.columns:
                for book in existing_books:
                    try:
                        max_p = reading_df[reading_df['dettaglio'] == book]['pagine_totali'].max()
                        if pd.notna(max_p) and max_p > 0:
                            book_metadata[book] = int(max_p)
                    except:
                        pass

        # 3. INTERFACCIA SELEZIONE
        col_mode, col_book = st.columns([1, 2])
        
        with col_mode:
            mode = st.radio("Libro", ["In Corso", "Nuovo"], label_visibility="collapsed")
        
        selected_title = None
        current_total_pages_val = 0

        with col_book:
            if mode == "In Corso":
                if existing_books:
                    selected_title = st.selectbox("Seleziona Titolo", existing_books)
                    current_total_pages_val = book_metadata.get(selected_title, 0)
                else:
                    st.warning("⚠️ Nessun libro in storico. Seleziona 'Nuovo'.")
            else:
                selected_title = st.text_input("Inserisci Titolo Nuovo Libro")
                current_total_pages_val = 0

        if not selected_title:
            return {"custom_date": log_date}

        # 4. INPUT DATI NUMERICI
        st.write("---")
        c1, c2 = st.columns(2)
        
        with c1:
            total_pages = st.number_input(
                "Pagine Totali Libro", 
                min_value=0, 
                step=1,
                value=current_total_pages_val
            )

        with c2:
            pages_read = st.number_input("Pagine lette oggi", min_value=1, step=1)

        # 5. BARRA DI PROGRESSO (SOLO SE "IN CORSO")
        # La visualizziamo solo se siamo in modalità aggiornamento E abbiamo le pagine totali
        if mode == "In Corso" and total_pages > 0:
            already_read = 0
            
            # Calcolo storico preciso
            if not df.empty and 'dettaglio' in df.columns:
                subset = df[(df['activity_type'] == self.name) & (df['dettaglio'] == selected_title)]
                already_read = subset['metrica'].sum()
            
            # Totale cumulativo (Storia + Oggi)
            cumulative_total = already_read + pages_read
            
            # Calcolo percentuale
            pct = (cumulative_total / total_pages) * 100
            display_pct = min(pct, 100.0)
            
            st.info(f"📈 Situazione: Avevi letto **{int(already_read)}** pagine. Con oggi arrivi a **{int(cumulative_total)}**.")
            st.progress(display_pct / 100, text=f"Progresso Totale: {int(display_pct)}%")
            
            if cumulative_total >= total_pages:
                st.success("🏆 Complimenti! Libro completato.")

        return {
            "dettaglio": selected_title,
            "metrica": pages_read,
            "unita": "pagine",
            "pagine_totali": total_pages,
            "custom_date": log_date
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