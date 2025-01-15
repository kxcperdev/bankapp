from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import crud, database, models
from utils.security import get_current_user
from utils.responses import success_response, error_response
from datetime import datetime

router = APIRouter()

# ---------------------------
# Lista aktywnych połączeń WebSocket
# ---------------------------
active_connections = []

# ---------------------------
# Endpoint WebSocket dla powiadomień w czasie rzeczywistym
# ---------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Utrzymuje połączenie WebSocket z klientami do powiadomień w czasie rzeczywistym.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# ---------------------------
# Powiadamianie wszystkich klientów WebSocket
# ---------------------------
async def notify_all(message: str):
    """
    Wysyła wiadomość do wszystkich aktywnych klientów WebSocket.
    """
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
    """
    Pobiera informacje o koncie na podstawie jego ID, jeśli użytkownik ma do niego dostęp.
    """
    account = crud.get_account(db, account_id)
    if not account or account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)

    return success_response({
        "id": account.id,
        "balance": account.balance,
        "owner_id": account.owner_id
    })

# ---------------------------
# Tworzenie nowego konta
# ---------------------------
@router.post("/")
async def create_account(balance: int = 0, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """
    Tworzy nowe konto dla zalogowanego użytkownika.
    """
    account = crud.create_account(db, owner_id=current_user.id, balance=balance)
    await notify_all(f"New account created for user {current_user.username}, account ID: {account.id}")
    return success_response({
        "account_id": account.id,
        "balance": account.balance
    }, "Account created successfully")

# ---------------------------
# Pobieranie salda konta
# ---------------------------
@router.get("/{account_id}/balance")
def get_balance(account_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """
    Pobiera saldo konta, jeśli użytkownik ma do niego dostęp.
    """
    account = crud.get_account(db, account_id)
    if not account or account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)

    return success_response({"balance": account.balance})

# ---------------------------
# Wpłata na konto
# ---------------------------
@router.post("/{account_id}/deposit")
async def deposit(account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """
    Wpłaca środki na konto użytkownika.
    """
    if amount <= 0:
        return error_response("Deposit amount must be greater than zero", 400)

    account = db.query(models.Account).filter(models.Account.id == account_id).with_for_update().first()
    if not account or account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)

    account.balance += amount
    db.commit()
    crud.log_operation(db, account_id, "deposit", f"Deposited {amount}")
    await notify_all(f"Deposit of {amount} made to account ID: {account_id}")

    return success_response({
        "new_balance": account.balance
    }, "Deposit successful")

# ---------------------------
# Wypłata z konta
# ---------------------------
@router.post("/{account_id}/withdraw")
async def withdraw(account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """
    Wypłaca środki z konta użytkownika.
    """
    if amount <= 0:
        return error_response("Withdrawal amount must be greater than zero", 400)

    account = db.query(models.Account).filter(models.Account.id == account_id).with_for_update().first()
    if not account or account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)
    if account.balance < amount:
        return error_response("Insufficient funds", 400)

    account.balance -= amount
    db.commit()
    crud.log_operation(db, account_id, "withdraw", f"Withdrew {amount}")
    await notify_all(f"Withdrawal of {amount} made from account ID: {account_id}")

    return success_response({
        "new_balance": account.balance
    }, "Withdrawal successful")

# ---------------------------
# Przelew między kontami
# ---------------------------
@router.post("/transfer")
async def transfer(from_account_id: int, to_account_id: int, amount: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """
    Przelewa środki z jednego konta użytkownika na inne.
    """
    if amount <= 0:
        return error_response("Transfer amount must be greater than zero", 400)

    from_account = db.query(models.Account).filter(models.Account.id == from_account_id).with_for_update().first()
    to_account = db.query(models.Account).filter(models.Account.id == to_account_id).with_for_update().first()

    if not from_account or not to_account or from_account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)
    if from_account.balance < amount:
        return error_response("Insufficient funds", 400)

    from_account.balance -= amount
    to_account.balance += amount
    db.commit()
    crud.log_operation(db, from_account_id, "transfer", f"Transferred {amount} to account {to_account_id}")
    crud.log_operation(db, to_account_id, "transfer", f"Received {amount} from account {from_account_id}")
    await notify_all(f"Transfer of {amount} from account {from_account_id} to account {to_account_id}")

    return success_response({
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": amount
    }, "Transfer successful")

# ---------------------------
# Pobieranie logów operacji z filtrowaniem
# ---------------------------
@router.get("/{account_id}/logs")
def get_account_logs(
    account_id: int,
    start_date: str = None,
    end_date: str = None,
    operation_type: str = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Pobiera logi operacji na koncie z możliwością filtrowania.
    """
    account = crud.get_account(db, account_id)
    if not account or account.owner_id != current_user.id:
        return error_response("Account not found or access denied", 403)

    logs = crud.get_logs_for_account(db, account_id)

    # Filtrowanie według zakresu dat
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            logs = [log for log in logs if log.timestamp >= start_date_obj]
        except ValueError:
            return error_response("Invalid start_date format. Use YYYY-MM-DD.", 400)

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            logs = [log for log in logs if log.timestamp <= end_date_obj]
        except ValueError:
            return error_response("Invalid end_date format. Use YYYY-MM-DD.", 400)

    # Filtrowanie według rodzaju operacji
    if operation_type:
        logs = [log for log in logs if log.operation == operation_type]

    return success_response(logs, "Logs retrieved successfully")



