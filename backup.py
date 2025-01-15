import shutil
import os
from datetime import datetime

def create_backup():
    # Ścieżka do pliku bazy danych
    db_file = "bank.db"
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)  # Tworzy folder na backupy, jeśli nie istnieje

    # Nazwa pliku backupu z timestampem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.db"

    # Tworzenie kopii zapasowej
    shutil.copy(db_file, backup_file)
    print(f"Backup został utworzony: {backup_file}")
