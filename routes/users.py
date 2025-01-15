from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import crud, models, database
from utils.hashing import verify_password
from utils.security import create_access_token, oauth2_scheme, verify_access_token
from utils.security import get_current_user

router = APIRouter()


# ---------------------------
# Pobieranie użytkownika po ID
# ---------------------------
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        return {"error": "User not found"}
    return user


# ---------------------------
# Tworzenie użytkownika
# ---------------------------
@router.post("/")
def create_user(username: str, password: str, full_name: str, pesel: str, db: Session = Depends(database.get_db)):
    user = crud.create_user(db, username, password, full_name, pesel)
    return user


# ---------------------------
# Logowanie użytkownika
# ---------------------------
@router.post("/login")
def login(username: str, password: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Sprawdź, czy użytkownik ma aktywną sesję
    if user.active_token:
        raise HTTPException(status_code=400, detail="User already logged in")

    # Utwórz nowy token
    access_token = create_access_token(data={"sub": user.username})
    user.active_token = access_token
    db.commit()
    db.refresh(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "pesel": user.pesel
        }
    }


# ---------------------------
# Wylogowanie użytkownika
# ---------------------------
@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    # Usuń aktywny token
    current_user.active_token = None
    db.commit()
    db.refresh(current_user)

    return {"message": "Logged out successfully"}


# ---------------------------
# Odświeżanie tokenu użytkownika
# ---------------------------
@router.post("/refresh")
def refresh_token(current_user: models.User = Depends(get_current_user)):
    # Utwórz nowy token na podstawie bieżącego użytkownika
    new_token = create_access_token(data={"sub": current_user.username})
    current_user.active_token = new_token
    return {"access_token": new_token, "token_type": "bearer"}


# ---------------------------
# Pobieranie obecnie zalogowanego użytkownika
# ---------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Pobiera obecnie zalogowanego użytkownika na podstawie tokenu JWT.
    """
    payload = verify_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.active_token != token:
        raise HTTPException(status_code=401, detail="Token not associated with user")

    return user
