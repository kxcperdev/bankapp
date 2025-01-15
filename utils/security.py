from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from decouple import config
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User
from cryptography.fernet import Fernet
from utils.responses import success_response, error_response  # Import spójnych odpowiedzi

# Konfiguracja JWT
SECRET_KEY = config("SECRET_KEY")  # Klucz wczytany z pliku .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Konfiguracja szyfrowania AES (PESEL)
ENCRYPTION_KEY = config("ENCRYPTION_KEY").encode()  # Klucz szyfrowania z pliku .env
cipher = Fernet(ENCRYPTION_KEY)

# OAuth2 konfiguracja
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ---------------------------
# Szyfrowanie i deszyfrowanie danych
# ---------------------------
def encrypt_data(data: str) -> str:
    """
    Szyfruje dane za pomocą AES.
    """
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """
    Deszyfruje dane zaszyfrowane za pomocą AES.
    """
    return cipher.decrypt(data.encode()).decode()

# ---------------------------
# Tworzenie tokenu JWT
# ---------------------------
def create_access_token(data: dict):
    """
    Tworzy token JWT z danymi użytkownika i czasem wygaśnięcia.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ---------------------------
# Weryfikacja tokenu JWT
# ---------------------------
def verify_access_token(token: str):
    """
    Weryfikuje token JWT. Sprawdza poprawność i czas ważności.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire = payload.get("exp")
        if datetime.fromtimestamp(expire, timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail=error_response("Token has expired", 401))
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail=error_response("Invalid or expired token", 401))

# ---------------------------
# Pobieranie obecnie zalogowanego użytkownika
# ---------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Pobiera obecnie zalogowanego użytkownika na podstawie tokenu JWT.
    """
    payload = verify_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail=error_response("Invalid token", 401))

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail=error_response("User not found", 404))
    if user.active_token != token:
        raise HTTPException(status_code=401, detail=error_response("Token not associated with user", 401))

    # Odszyfrowanie PESEL
    if user.pesel:
        encrypted_pesel = str(user.pesel)  # Jawne pobranie wartości jako str
        decrypted_pesel = decrypt_data(encrypted_pesel)
        user.pesel = decrypted_pesel  # Nadpisanie odszyfrowaną wartością

    return user

# ---------------------------
# Unieważnianie aktywnego tokenu
# ---------------------------
def invalidate_user_token(user: User, db: Session):
    """
    Unieważnia aktywny token użytkownika (wylogowanie).
    """
    user.active_token = None
    db.commit()
    db.refresh(user)
    return success_response({}, "User logged out successfully")




