from fastapi import FastAPI
from database.database import Base, engine
from routes import users, accounts, realtime  # Import routerów

# Inicjalizacja bazy danych
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Rejestracja routerów
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(realtime.router, prefix="/realtime", tags=["realtime"])

@app.get("/")
def root():
    return {"message": "Serwer bankowy działa!"}

