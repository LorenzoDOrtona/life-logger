import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

def derive_key(password: str, salt: bytes = b'static_salt_log_app') -> bytes:
    """Trasforma la password umana in una chiave di crittografia a 32 byte URL-safe."""
    # In produzione, il salt dovrebbe essere univoco per utente, ma per semplicità usiamo uno statico
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_data(data_str: str, password: str) -> str:
    """Cripta una stringa usando la password."""
    key = derive_key(password)
    f = Fernet(key)
    # Fernet vuole bytes, ritorna bytes. Noi lavoriamo con stringhe
    encrypted_bytes = f.encrypt(data_str.encode())
    return encrypted_bytes.decode('utf-8')

def decrypt_data(encrypted_str: str, password: str) -> str:
    """Decripta una stringa usando la password."""
    key = derive_key(password)
    f = Fernet(key)
    decrypted_bytes = f.decrypt(encrypted_str.encode())
    return decrypted_bytes.decode('utf-8')

# Funzioni per gestire gli Hash delle password (Login)
def hash_password(password: str) -> str:
    # Genera un salt e fa l'hash
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())