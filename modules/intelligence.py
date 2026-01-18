from datetime import datetime
import pandas as pd

class SuggestionEngine:
    def __init__(self, df):
        self.df = df
        self.today_str = datetime.now().strftime("%Y-%m-%d")

    def get_prompts(self):
        prompts = []
        if self.df.empty: return prompts

        # Filtra dati di oggi
        # Assicuriamoci che timestamp sia datetime o stringa gestibile
        self.df['date_str'] = self.df['timestamp'].astype(str).str.slice(0, 10)
        today_data = self.df[self.df['date_str'] == self.today_str]

        # SUGGERIMENTO 1: Non hai ancora letto?
        # Controlla se ieri hai letto un libro e oggi no
        last_reading = self.df[self.df['activity_type'] == "📚 Lettura"].sort_values('timestamp').tail(1)
        if not last_reading.empty:
            book_title = last_reading.iloc[0]['dettaglio']
            # Se quel libro non è stato loggato oggi
            if book_title not in today_data['dettaglio'].values:
                prompts.append({
                    "id": "read_cont",
                    "msg": f"Continui a leggere '{book_title}'?",
                    "activity": "📚 Lettura",
                    "dettaglio": book_title
                })

        # SUGGERIMENTO 2: Non hai fatto sport?
        if "💪 Sport" not in today_data['activity_type'].values:
            prompts.append({
                "id": "sport_check",
                "msg": "Niente sport oggi? Inserisci sessione rapida.",
                "activity": "💪 Sport",
                "dettaglio": "Palestra" # Default
            })
            
        return prompts