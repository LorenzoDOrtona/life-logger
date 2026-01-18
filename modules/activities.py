import streamlit as st
from abc import ABC, abstractmethod
import pandas as pd

class BaseActivity(ABC):
    """Classe base per ogni attività."""
    @property
    @abstractmethod
    def name(self): pass
    
    @abstractmethod
    def render_ui(self, history_df: pd.DataFrame) -> dict: pass

# --- IMPLEMENTAZIONI ---

class ReadingActivity(BaseActivity):
    name = "📚 Lettura"
    def render_ui(self, df):
        # Logica: trova libri già iniziati
        existing = []
        if not df.empty and 'dettaglio' in df.columns:
            existing = df[df['activity_type'] == self.name]['dettaglio'].dropna().unique().tolist()
        
        col1, col2 = st.columns(2)
        with col1: mode = st.radio("Modalità", ["In Corso", "Nuovo"], horizontal=True, label_visibility="collapsed")
        
        detail = ""
        if mode == "In Corso" and existing:
            with col2: detail = st.selectbox("Libro", existing)
        else:
            with col2: detail = st.text_input("Nuovo Titolo")
            
        metric = st.number_input("Pagine lette", step=1, min_value=1)
        return {"dettaglio": detail, "metrica": metric, "unita": "pagine"}

class SportActivity(BaseActivity):
    name = "💪 Sport"
    def render_ui(self, df):
        types = ["Palestra", "Corsa", "Nuoto", "Yoga", "Bici"]
        detail = st.selectbox("Tipo", types)
        metric = st.number_input("Minuti", step=5, min_value=5)
        return {"dettaglio": detail, "metrica": metric, "unita": "minuti"}

class MovieActivity(BaseActivity):
    name = "🎬 Film/Serie"
    def render_ui(self, df):
        detail = st.text_input("Titolo")
        metric = st.slider("Voto", 1, 10)
        return {"dettaglio": detail, "metrica": metric, "unita": "voto"}

class GenericActivity(BaseActivity):
    name = "📝 Altro"
    def render_ui(self, df):
        detail = st.text_input("Attività")
        metric = st.number_input("Valore (opzionale)")
        return {"dettaglio": detail, "metrica": metric, "unita": "generic"}

# Registro delle attività disponibili
def get_all_activities():
    return [ReadingActivity(), SportActivity(), MovieActivity(), GenericActivity()]