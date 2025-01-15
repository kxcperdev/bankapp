from fastapi import FastAPI
from fastapi.responses import FileResponse
from database.database import Base, engine
from routes import users, accounts, realtime  # Import routerów
from decouple import config
import uvicorn

# Inicjalizacja bazy danych
Base.metadata.create_all(bind=engine)

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
