from sqlalchemy.orm import Session
from database import models
from utils.hashing import hash_password
from utils.security import encrypt_data, decrypt_data
from datetime import datetime, timezone
import asyncio
import websockets

# Lista adresów innych serwerów do synchronizacji
peer_servers = [
    "ws://localhost:8001/sync",
    "ws://localhost:8002/sync",
    "ws://localhost:8003/sync"
]

# ---------------------------
# Funkcja do powiadamiania serwerów
# ---------------------------
async def notify_peers(data: str):
    """
    Wysyła dane do innych serwerów za pomocą WebSocketów.
    """
    for server in peer_servers:
        try:
            async with websockets.connect(server) as websocket:
                await websocket.send(data)
        except Exception as e:
            print(f"Failed to notify {server}: {e}")

# ---------------------------
# Operacje CRUD dla User
# ---------------------------
def get_user(db: Session, user_id: int):
    """
    Pobiera użytkownika z bazy danych i odszyfrowuje jego PESEL.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        encrypted_pesel = getattr(user, "pesel")  # Pobranie zaszyfrowanego PESEL
        decrypted_pesel = decrypt_data(encrypted_pesel)  # Odszyfrowanie PESEL
        user.pesel = decrypted_pesel  # Nadpisanie odszyfrowaną wartością
    return user

def create_user(db: Session, username: str, password: str, full_name: str, pesel: str):
    """
    Tworzy nowego użytkownika w bazie danych z zahaszowanym hasłem i zaszyfrowanym PESEL.
    """
    hashed_password = hash_password(password)
    encrypted_pesel = encrypt_data(pesel)  # Szyfrowanie PESEL
    user = models.User(username=username, password=hashed_password, full_name=full_name, pesel=encrypted_pesel)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ---------------------------
# Operacje CRUD dla Account
# ---------------------------
def get_account(db: Session, account_id: int):
    """
    Pobiera informacje o koncie na podstawie jego ID.
    """
    return db.query(models.Account).filter(models.Account.id == account_id).first()

def create_account(db: Session, owner_id: int, balance: int = 0):
    """
    Tworzy nowe konto przypisane do danego użytkownika.
    """
    account = models.Account(owner_id=owner_id, balance=balance)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def update_account_balance(db: Session, account_id: int, amount: int):
    """
    Aktualizuje saldo konta z blokadą na poziomie bazy danych.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).with_for_update().first()
    if account:
        account.balance += amount
        db.commit()
        db.refresh(account)
    return account

# ---------------------------
# Logowanie operacji
# ---------------------------
def log_operation(db: Session, account_id: int, operation: str, details: str):
    """
    Loguje operację na koncie, zapisuje ją w bazie danych i synchronizuje z innymi serwerami.
    """
    encrypted_details = encrypt_data(details)  # Szyfrowanie szczegółów logu
    log = models.Log(
        account_id=account_id,
        operation=operation,
        details=encrypted_details,
        timestamp=datetime.now(timezone.utc)  # Użycie timezone-aware datetime
    )
    db.add(log)
    db.commit()

    # Notyfikacja innych serwerów
    asyncio.create_task(notify_peers(f"Log: {operation}, Details: {details}"))

    return log

# ---------------------------
# Pobieranie logów operacji
# ---------------------------
def get_logs_for_account(db: Session, account_id: int, start_date=None, end_date=None, operation_type=None):
    """
    Pobiera logi operacji z możliwością filtrowania i odszyfrowaniem szczegółów.
    """
    query = db.query(models.Log).filter(models.Log.account_id == account_id)

    # Filtrowanie według zakresu dat
    if start_date:
        query = query.filter(models.Log.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Log.timestamp <= end_date)

    # Filtrowanie według rodzaju operacji
    if operation_type:
        query = query.filter(models.Log.operation == operation_type)

    logs = query.order_by(models.Log.timestamp.desc()).all()

    # Odszyfrowanie szczegółów logów
    for log in logs:
        encrypted_details = getattr(log, "details")  # Pobranie wartości pola
        decrypted_details = decrypt_data(encrypted_details)  # Odszyfrowanie danych
        log.details = decrypted_details  # Nadpisanie odszyfrowanej wartości

    return logs



