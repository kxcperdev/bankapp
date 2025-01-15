from sqlalchemy.orm import Session
from database import models
from utils.hashing import hash_password


# ---------------------------
# Operacje CRUD dla User
# ---------------------------
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, username: str, password: str, full_name: str, pesel: str):
    hashed_password = hash_password(password)
    user = models.User(username=username, password=hashed_password, full_name=full_name, pesel=pesel)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------
# Operacje CRUD dla Account
# ---------------------------
def get_account(db: Session, account_id: int):
    return db.query(models.Account).filter(models.Account.id == account_id).first()


def create_account(db: Session, owner_id: int, balance: int = 0):
    account = models.Account(owner_id=owner_id, balance=balance)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account_balance(db: Session, account_id: int, new_balance: int):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if account:
        account.balance = new_balance
        db.commit()
        db.refresh(account)
    return account


# ---------------------------
# Logowanie operacji
# ---------------------------
def log_operation(db: Session, account_id: int, operation: str, details: str):
    log = models.Log(account_id=account_id, operation=operation, details=details)
    db.add(log)
    db.commit()
    return log


def get_logs_for_account(db: Session, account_id: int):
    return db.query(models.Log).filter(models.Log.account_id == account_id).all()

