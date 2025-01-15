from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from decouple import config
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User

# Konfiguracja JWT
SECRET_KEY = config("SECRET_KEY")  # Klucz wczytany z pliku .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 konfiguracja
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ---------------------------
# Tworzenie tokenu JWT
# ---------------------------
def create_access_token(data: dict):
    """
    Tworzy token JWT z danymi użytkownika i czasem wygaśnięcia.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        if datetime.utcfromtimestamp(expire) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token has expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------------------
# Odświeżanie tokenu JWT
# ---------------------------
def refresh_access_token(token: str):
    """
    Odświeża token JWT, jeśli jest jeszcze ważny.
    """
    payload = verify_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Tworzy nowy token
    new_token = create_access_token({"sub": username})
    return new_token

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
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.active_token != token:
        raise HTTPException(status_code=401, detail="Token not associated with user")

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


