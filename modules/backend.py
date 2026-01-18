import streamlit as st
import yaml
import pandas as pd
from github import Github

class GitHubBackend:
    def __init__(self):
        self.token = st.secrets["GITHUB_TOKEN"]
        self.repo_name = st.secrets["REPO_NAME"]
        self.file_path = "data.yaml"
        self.github = Github(self.token)
        # Lazy loading della repo per evitare chiamate API inutili all'init
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            self._repo = self.github.get_repo(self.repo_name)
        return self._repo

    def load_data(self) -> pd.DataFrame:
        """Scarica e parsa il YAML in DataFrame."""
        try:
            contents = self.repo.get_contents(self.file_path)
            yaml_content = contents.decoded_content.decode("utf-8")
            data = yaml.safe_load(yaml_content)
            if not data: return pd.DataFrame()
            
            df = pd.DataFrame(data)
            # Converte timestamp in datetime vero per facilitare i calcoli dopo
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            # Se il file non esiste o è vuoto
            return pd.DataFrame()

    def save_entry(self, entry: dict):
        """Aggiunge una entry e fa commit su GitHub."""
        try:
            # 1. Recupera file attuale
            try:
                contents = self.repo.get_contents(self.file_path)
                current_data = yaml.safe_load(contents.decoded_content.decode("utf-8")) or []
                sha = contents.sha
                exists = True
            except:
                current_data = []
                exists = False

            # 2. Aggiungi
            current_data.append(entry)
            
            # 3. Dump YAML
            new_content = yaml.dump(current_data, sort_keys=False, allow_unicode=True)
            
            # 4. Commit
            if exists:
                self.repo.update_file(contents.path, f"Log: {entry['activity_type']}", new_content, sha)
            else:
                self.repo.create_file(self.file_path, "Initial commit", new_content)
                
            return True
        except Exception as e:
            st.error(f"Errore salvataggio: {e}")
            return False