import hashlib

# Lista serwerów rozproszonych
servers = [
    "https://localhost:8443",
    "https://localhost:8444",
    "https://localhost:8445"
]

def hash_user(username: str) -> int:
    """
    Hashuje nazwę użytkownika i zwraca indeks serwera.
    """
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    return hash_value % len(servers)

def assign_server(username: str) -> str:
    """
    Przydziela użytkownika do serwera na podstawie funkcji hashującej.
    """
    server_index = hash_user(username)
    return servers[server_index]
