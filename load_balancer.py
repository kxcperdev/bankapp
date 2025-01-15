from fastapi import FastAPI, Request, HTTPException
import requests
from utils.assignment import assign_server  # Import funkcji assign_server
from typing import List
import threading
import time

app = FastAPI()

# Lista serwerów rozproszonych
servers = [
    {"url": "https://localhost:8001", "status": "healthy"},
    {"url": "https://localhost:8002", "status": "healthy"},
    {"url": "https://localhost:8003", "status": "healthy"}
]


def get_healthy_servers() -> List[str]:
    """
    Zwraca listę zdrowych serwerów.
    """
    return [server["url"] for server in servers if server["status"] == "healthy"]


def monitor_servers():
    """
    Monitoruje stan serwerów, wykonując zapytania health check co 10 sekund.
    """
    while True:
        for server in servers:
            try:
                response = requests.get(f"{server['url']}/health", timeout=5)
                if response.status_code == 200:
                    server["status"] = "healthy"
                else:
                    server["status"] = "unhealthy"
            except requests.exceptions.RequestException:
                server["status"] = "unhealthy"
        time.sleep(10)


# Uruchomienie monitorowania serwerów w osobnym wątku
threading.Thread(target=monitor_servers, daemon=True).start()


@app.post("/{path:path}")
async def proxy_request(path: str, request: Request):
    """
    Proxy: Rozdziela żądania klientów do zdrowych serwerów rozproszonych na podstawie użytkownika.
    """
    username = request.headers.get("X-Username")  # Pobranie nazwy użytkownika z nagłówka
    if not username:
        raise HTTPException(status_code=400, detail="Username header is required")

    # Przydzielenie serwera na podstawie nazwy użytkownika
    healthy_servers = get_healthy_servers()
    if not healthy_servers:
        raise HTTPException(status_code=503, detail="No healthy servers available")

    server_url = assign_server(username)  # Przypisanie serwera
    if server_url not in healthy_servers:
        raise HTTPException(status_code=503, detail=f"Assigned server {server_url} is not healthy")

    try:
        body = await request.body()
        headers = dict(request.headers)
        response = requests.post(f"{server_url}/{path}", data=body, headers=headers)
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/health")
def health_check():
    """
    Endpoint do sprawdzania statusu load-balancera.
    """
    return {"status": "ok", "message": "Load balancer is running"}


@app.get("/servers")
def get_servers_status():
    """
    Endpoint do uzyskania statusu wszystkich serwerów rozproszonych.
    """
    return {"servers": servers}

