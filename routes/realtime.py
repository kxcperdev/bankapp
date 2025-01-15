from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
active_connections = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Odbieranie danych od klienta (opcjonalne)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
