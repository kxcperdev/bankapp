from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import crud, database, models
from utils.security import get_current_user

router = APIRouter()

# ---------------------------
# Lista aktywnych połączeń WebSocket
# ---------------------------
active_connections = []

# ---------------------------
# Endpoint WebSocket
# ---------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Możesz obsłużyć wiadomości od klienta (opcjonalne)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# ---------------------------
# Powiadamianie przez WebSockety
# ---------------------------
async def notify_all(message: str):
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            active_connections.remove(connection)

# ---------------------------
# Pobieranie informacji o koncie
# ---------------------------
@router.get("/{account_id}")
def get_account(account_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    return account

# ---------------------------
# Tworzenie nowego konta
# ---------------------------
@router.post("/")
async def create_account(balance: int = 0, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    account = crud.create_account(db, owner_id=current_user.id, balance=balance)
    await notify_all(f"New account created for user {current_user.username}, account ID: {account.id}")
    return {"message": "Account created successfully", "account_id": account.id, "balance": account.balance}

# ---------------------------
# Pobieranie salda konta
# ---------------------------
@router.get("/{account_id}/balance")
def get_balance(account_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    return {"balance": account.balance}

# ---------------------------
# Wpłata na konto
# ---------------------------
@router.post("/{account_id}/deposit")
async def deposit(account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    account.balance += amount
    db.commit()
    crud.log_operation(db, account_id, "deposit", f"Deposited {amount}")
    await notify_all(f"Deposit of {amount} made to account ID: {account_id}")
    return {"message": "Deposit successful", "new_balance": account.balance}

# ---------------------------
# Wypłata z konta
# ---------------------------
@router.post("/{account_id}/withdraw")
async def withdraw(account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be greater than zero")
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    if account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    account.balance -= amount
    db.commit()
    crud.log_operation(db, account_id, "withdraw", f"Withdrew {amount}")
    await notify_all(f"Withdrawal of {amount} made from account ID: {account_id}")
    return {"message": "Withdrawal successful", "new_balance": account.balance}

# ---------------------------
# Przelew między kontami
# ---------------------------
@router.post("/transfer")
async def transfer(from_account_id: int, to_account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero")
    from_account = crud.get_account(db, from_account_id)
    to_account = crud.get_account(db, to_account_id)
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="One or both accounts not found")
    if from_account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    if from_account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    from_account.balance -= amount
    to_account.balance += amount
    db.commit()
    crud.log_operation(db, from_account_id, "transfer", f"Transferred {amount} to account {to_account_id}")
    crud.log_operation(db, to_account_id, "transfer", f"Received {amount} from account {from_account_id}")
    await notify_all(f"Transfer of {amount} from account {from_account_id} to account {to_account_id}")
    return {"message": "Transfer successful", "from_account_id": from_account_id, "to_account_id": to_account_id, "amount": amount}

# ---------------------------
# Pobieranie logów operacji
# ---------------------------
@router.get("/{account_id}/logs")
def get_account_logs(account_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this account")
    logs = crud.get_logs_for_account(db, account_id)
    return logs


