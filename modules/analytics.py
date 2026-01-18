import pandas as pd
import plotly.express as px
import streamlit as st

class AnalyticsEngine:
    def __init__(self, df):
        self.df = df.copy()
        # Assicuriamoci che sia un DatetimeIndex
        if not self.df.empty:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df = self.df.set_index('timestamp')

    def render_summary(self):
        if self.df.empty:
            st.info("Nessun dato per le statistiche.")
            return

        timeframe = st.select_slider("Periodo", options=["D", "W", "M", "Y"], value="M", format_func=lambda x: {"D":"Giorni", "W":"Settimane", "M":"Mesi", "Y":"Anni"}[x])
        
        # Filtro per attività
        all_activities = self.df['activity_type'].unique()
        selected_act = st.selectbox("Attività da analizzare", all_activities)

        subset = self.df[self.df['activity_type'] == selected_act]
        
        if subset.empty:
            st.warning("Nessun dato per questa selezione.")
            return

        # Resampling (Magia di Pandas)
        # Sum per pagine/minuti, Mean per voti. Qui semplifichiamo con Sum
        resampled = subset['metrica'].resample(timeframe).sum()
        
        # Grafico
        st.subheader(f"Andamento: {selected_act}")
        st.bar_chart(resampled)
        
        # Statistica totale
        total = subset['metrica'].sum()
        st.metric("Totale nel periodo storico", f"{int(total)}")