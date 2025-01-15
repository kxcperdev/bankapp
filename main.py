from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from database.database import Base, engine
from routes import users, accounts, realtime  # Import routerów
from decouple import config
import uvicorn
import asyncio
import websockets
from typing import List

# Aktualizacja struktury bazy danych
Base.metadata.create_all(bind=engine)
print("Zaktualizowano strukturę bazy danych.")

# Inicjalizacja aplikacji
app = FastAPI(
    title="Banking API",
    description="API dla serwera bankowego",
    version="1.0.0"
)

# Rejestracja routerów
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(realtime.router, prefix="/realtime", tags=["realtime"])

@app.get("/")
def root():
    return {"message": "Serwer bankowy działa!"}

# Obsługa favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")  # Ścieżka do pliku favicon.ico

# ---------------------------
# Synchronizacja WebSocket
# ---------------------------
active_connections: List[WebSocket] = []

@app.websocket("/sync")
async def sync_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket do synchronizacji danych między serwerami.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Odbiór danych od jednego z serwerów
            await broadcast(data)  # Rozesłanie danych do pozostałych serwerów
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast(message: str):
    """
    Wysyła wiadomość do wszystkich aktywnych połączeń WebSocket.
    """
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            active_connections.remove(connection)

# ---------------------------
# Połączenia WebSocket z innymi serwerami
# ---------------------------
peer_servers = [
    "ws://localhost:8001/sync",
    "ws://localhost:8002/sync",
    "ws://localhost:8003/sync"
]

async def connect_to_peers():
    """
    Łączy serwer z pozostałymi serwerami w sieci za pomocą WebSocketów.
    """
    for server in peer_servers:
        try:
            async with websockets.connect(server) as websocket:
                print(f"Connected to peer: {server}")
                while True:
                    message = await websocket.recv()  # Odbiór danych z innego serwera
                    print(f"Received message from {server}: {message}")
        except Exception as e:
            print(f"Could not connect to {server}: {e}")

@app.on_event("startup")
async def startup_event():
    """
    Funkcja uruchamiana przy starcie aplikacji. Rozpoczyna połączenia WebSocket.
    """
    asyncio.create_task(connect_to_peers())

if __name__ == "__main__":
    # Wczytaj ścieżki do certyfikatów z pliku .env
    ssl_certfile = config("SSL_CERTFILE", default=None)  # Ścieżka do certyfikatu
    ssl_keyfile = config("SSL_KEYFILE", default=None)    # Ścieżka do klucza prywatnego

    # Użyj certyfikatów tylko jeśli są dostępne
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,  # Zmieniony port na 8443
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
