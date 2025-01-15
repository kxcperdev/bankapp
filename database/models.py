from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)  # Indeks dla klucza głównego
    username = Column(String, unique=True, index=True)  # Unikalny indeks dla username
    password = Column(String, nullable=False)  # Hasło musi być zawsze ustawione
    full_name = Column(String, nullable=False)  # Pełne imię i nazwisko
    pesel = Column(String, unique=True, index=True)  # Unikalny indeks dla PESEL
    active_token = Column(String, nullable=True)  # Aktywny token do autoryzacji

    # Relacja z kontami użytkownika
    accounts = relationship("Account", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)  # Indeks dla klucza głównego
    balance = Column(Integer, default=0)  # Domyślne saldo 0
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)  # Indeks dla owner_id
    owner = relationship("User", back_populates="accounts")  # Relacja z tabelą `users`

    # Dodanie indeksów wielopolowych
    __table_args__ = (
        Index("ix_owner_id_balance", "owner_id", "balance"),  # Indeks wielopolowy
    )

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)  # Indeks dla klucza głównego
    operation = Column(String, index=True)  # Indeks dla rodzaju operacji
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)  # Poprawione na timezone-aware datetime
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)  # Indeks dla account_id
    details = Column(String, nullable=True)  # Szczegóły operacji (opcjonalne)
    account = relationship("Account", back_populates="logs")  # Relacja z tabelą `accounts`

    # Dodanie indeksów wielopolowych
    __table_args__ = (
        Index("ix_account_id_operation", "account_id", "operation"),  # Indeks wielopolowy
    )

# Relacja między `accounts` a `logs`
Account.logs = relationship("Log", back_populates="account")

