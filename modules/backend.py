import streamlit as st
import yaml
import pandas as pd
from github import Github
from modules.crypto_utils import encrypt_data, decrypt_data

class GitHubBackend:
    def __init__(self, username):
        self.token = st.secrets["GITHUB_TOKEN"]
        self.repo_name = st.secrets["REPO_NAME"]
        # Nota l'estensione .enc per ricordarci che è criptato
        self.file_path = f"data_{username}.enc" 
        self.github = Github(self.token)
        # Recuperiamo la password dalla sessione per usarla come chiave
        self.user_password = st.session_state.get("encryption_key")
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            self._repo = self.github.get_repo(self.repo_name)
        return self._repo

    def load_data(self) -> pd.DataFrame:
        cols = ["timestamp", "activity_type", "note", "dettaglio", "metrica", "unita"]
        try:
            # 1. Scarica il blob criptato
            contents = self.repo.get_contents(self.file_path)
            encrypted_content = contents.decoded_content.decode("utf-8")
            
            # 2. DECRIPTA
            yaml_str = decrypt_data(encrypted_content, self.user_password)
            
            # 3. Parsa
            data = yaml.safe_load(yaml_str)
            if not data: return pd.DataFrame(columns=cols)
            
            df = pd.DataFrame(data)
            # (Codice pulizia dataframe uguale a prima...)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
            
        except Exception as e:
            # Se errore è "Invalid Token" (password sbagliata) o file mancante
            return pd.DataFrame(columns=cols)

    def save_entry(self, entry: dict):
        try:
            # 1. Scarica e Decripta attuale (per appendere)
            try:
                contents = self.repo.get_contents(self.file_path)
                encrypted_content = contents.decoded_content.decode("utf-8")
                yaml_str = decrypt_data(encrypted_content, self.user_password)
                current_data = yaml.safe_load(yaml_str) or []
                sha = contents.sha
                exists = True
            except:
                current_data = []
                exists = False

            # 2. Aggiungi
            current_data.append(entry)
            
            # 3. Converti in YAML string
            new_yaml_str = yaml.dump(current_data, sort_keys=False, allow_unicode=True)
            
            # 4. CRIPTA TUTTO
            final_encrypted_blob = encrypt_data(new_yaml_str, self.user_password)
            
            # 5. Upload su GitHub
            if exists:
                self.repo.update_file(self.file_path, "Log Encrypted", final_encrypted_blob, sha)
            else:
                self.repo.create_file(self.file_path, "Init Encrypted", final_encrypted_blob)
            return True
            
        except Exception as e:
            st.error(f"Errore Critico Salvataggio: {e}")
            return False