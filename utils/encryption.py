from cryptography.fernet import Fernet
from decouple import config

# Klucz szyfrowania (wczytaj z pliku .env)
ENCRYPTION_KEY = config("ENCRYPTION_KEY").encode()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_data(data: str) -> str:
    """
    Szyfruje dane za pomocą AES (Fernet).
    """
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """
    Deszyfruje dane zaszyfrowane za pomocą AES (Fernet).
    """
    return cipher.decrypt(data.encode()).decode()
