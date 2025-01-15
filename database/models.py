from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    pesel = Column(String, unique=True)
    active_token = Column(String, nullable=True)  # Przechowywanie aktywnego tokenu

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String)  # Np. "transfer", "deposit", "withdraw"
    timestamp = Column(String)  # Możesz użyć datetime
    account_id = Column(Integer, ForeignKey("accounts.id"))
    details = Column(String)  # Dodatkowe szczegóły

