from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import crud, models, database
from utils.hashing import verify_password
from utils.security import create_access_token, get_current_user
from utils.responses import success_response, error_response

router = APIRouter()

# ---------------------------
# Pobieranie użytkownika po ID
# ---------------------------
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        return error_response("User not found", 404)
    return success_response({
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "pesel": user.pesel
    })

# ---------------------------
# Tworzenie użytkownika
# ---------------------------
@router.post("/")
def create_user(username: str, password: str, full_name: str, pesel: str, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.username == username).first():
        return error_response("Username already exists", 400)

    user = crud.create_user(db, username, password, full_name, pesel)
    return success_response({
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name
    }, "User created successfully")

# ---------------------------
# Logowanie użytkownika
# ---------------------------
@router.post("/login")
def login(username: str, password: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password):
        return error_response("Invalid username or password", 400)

    if user.active_token:
        return error_response("User already logged in", 400)

    # Tworzenie tokenu
    access_token = create_access_token(data={"sub": user.username})
    user.active_token = access_token
    db.commit()
    db.refresh(user)

    return success_response({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "pesel": user.pesel
        }
    }, "Login successful")

# ---------------------------
# Wylogowanie użytkownika
# ---------------------------
@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    current_user.active_token = None
    db.commit()
    db.refresh(current_user)
    return success_response({}, "Logged out successfully")

# ---------------------------
# Odświeżanie tokenu użytkownika
# ---------------------------
@router.post("/refresh")
def refresh_token(current_user: models.User = Depends(get_current_user)):
    new_token = create_access_token(data={"sub": current_user.username})
    current_user.active_token = new_token
    return success_response({
        "access_token": new_token,
        "token_type": "bearer"
    }, "Token refreshed successfully")

