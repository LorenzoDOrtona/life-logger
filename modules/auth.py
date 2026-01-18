import streamlit as st

def check_password():
    """Ritorna True se l'utente è loggato correttemente."""
    
    # Se la password è già corretta nella sessione, passa
    if st.session_state.get("password_correct", False):
        return True

    # Callback per verificare la password
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Rimuovi password dalla memoria
        else:
            st.session_state["password_correct"] = False

    # UI Login
    st.title("🔒 Login Life Logger")
    st.text_input(
        "Password", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password errata.")

    return False