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
# --- NUOVA VERSIONE LETTURA (CON GESTIONE STATO) ---
class ReadingActivity(BaseActivity):
    name = "📚 Lettura"

    def _analyze_library(self, df: pd.DataFrame):
        """
        Analizza il DataFrame e restituisce:
        1. active_books: Dizionario {titolo: {'letti': X, 'totali': Y}} per i libri in corso.
        2. finished_books: Lista di titoli completati.
        """
        active_books = {}
        finished_books = []

        if df.empty or 'dettaglio' not in df.columns:
            return active_books, finished_books

        # Filtra solo attività di lettura
        reading_df = df[df['activity_type'] == self.name]
        unique_titles = reading_df['dettaglio'].dropna().unique()

        for title in unique_titles:
            book_logs = reading_df[reading_df['dettaglio'] == title]
            
            # Calcolo Pagine Lette (Somma metriche)
            read_so_far = book_logs['metrica'].sum()
            
            # Calcolo Pagine Totali (Prendi il massimo dichiarato)
            total_pages = 0
            if 'pagine_totali' in book_logs.columns:
                total_pages = book_logs['pagine_totali'].max()
                if pd.isna(total_pages): total_pages = 0
            
            # Logica di Smistamento
            if total_pages > 0 and read_so_far >= total_pages:
                finished_books.append(title)
            else:
                active_books[title] = {
                    'letti': int(read_so_far),
                    'totali': int(total_pages)
                }
        
        return active_books, finished_books

    def render_ui(self, df: pd.DataFrame):
        # 1. ANALISI AUTOMATICA LIBRARY
        active_books, finished_books = self._analyze_library(df)
        
        # 2. UI SELEZIONE
        st.write(f"📊 **Statistiche:** {len(active_books)} In lettura | {len(finished_books)} Finiti")
        
        log_date = st.date_input("Data Lettura", value=date.today())
        
        # Modalità: "Leggo" (solo attivi) o "Nuovo" (inizia da zero)
        mode = st.radio("Azione", ["📖 Leggo Pagine", "✨ Nuovo Libro"], horizontal=True)
        
        selected_title = None
        total_pages_val = 0
        read_previous = 0

        # --- CASO A: LEGGO PAGINE (Solo libri In Corso) ---
        if mode == "📖 Leggo Pagine":
            if not active_books:
                st.warning("⚠️ Non hai libri in corso! Inizia un 'Nuovo Libro'.")
                return {"custom_date": log_date}
            
            selected_title = st.selectbox("Libro in corso", list(active_books.keys()))
            
            # Recupera dati dalla nostra analisi
            book_data = active_books[selected_title]
            total_pages_val = book_data['totali']
            read_previous = book_data['letti']

            # Mostra info statiche
            st.info(f"Stai leggendo: **{selected_title}** ({read_previous}/{total_pages_val} pag.)")

        # --- CASO B: NUOVO LIBRO ---
        else:
            c_title, c_tot = st.columns([2, 1])
            with c_title:
                selected_title = st.text_input("Titolo Nuovo Libro")
                # Controllo se esiste già nei finiti o attivi
                if selected_title in finished_books:
                    st.error("⚠️ Questo libro risulta già letto e finito!")
                    return {"custom_date": log_date, "is_valid": False}
                if selected_title in active_books:
                    st.warning(f"⚠️ Questo libro è già in corso ({active_books[selected_title]['letti']} pag). Usa l'altra tab per aggiornarlo.")
            
            with c_tot:
                total_pages_val = st.number_input("Pagine Totali", min_value=1, step=1)
            
            read_previous = 0 # È nuovo

        if not selected_title:
            return {"custom_date": log_date}

        st.divider()

        # 3. INPUT LETTURA ODIFIERNA
        # Se è un libro attivo, mostriamo le pagine totali disabilitate (solo lettura)
        # Se è nuovo, permettiamo di modificarle (gestito sopra nel layout colonne)
        
        pages_today = st.number_input("Pagine lette oggi", min_value=1, step=1)

        # 4. VALIDAZIONE E PROGRESSO
        is_valid = True
        
        if total_pages_val > 0:
            new_total = read_previous + pages_today
            
            # Validazione
            if new_total > total_pages_val:
                diff = new_total - total_pages_val
                st.error(f"⛔ Errore: Sfori di {diff} pagine! ({new_total}/{total_pages_val})")
                is_valid = False
            else:
                # Barra Progresso
                pct = (new_total / total_pages_val) * 100
                st.progress(pct/100, text=f"Avanzamento: {int(pct)}%")
                
                # Feedback completamento
                if new_total == total_pages_val:
                    st.balloons()
                    st.success(f"🏆 COMPLETI IL LIBRO OGGI! Verrà spostato nella collezione 'Finiti'.")

        return {
            "dettaglio": selected_title,
            "metrica": pages_today,
            "unita": "pagine",
            "pagine_totali": total_pages_val,
            "custom_date": log_date,
            "is_valid": is_valid
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
        metric = st.number_input("Minuti", step=15, min_value=5)
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