from fastapi import WebSocket
import json
from typing import Dict, Any

async def handle_chat(websocket: WebSocket, manager, client_id: str = None):
    """
    Handle chat WebSocket connections
    """
    # Accept the connection
    await manager.connect(websocket, client_id or "anonymous")
    
    # Send welcome message
    await manager.send_personal_message(
        {"type": "system", "message": "Welcome to the chat!"}, 
        websocket
    )
    
    # Broadcast join notification
    await manager.broadcast(
        {"type": "system", "message": f"Client {client_id or 'anonymous'} joined the chat"}
    )
    
    # Handle messages
    while True:
        data = await websocket.receive_text()
        try:
            message_data = json.loads(data)
            # Process message
            await manager.broadcast(
                {
                    "type": "chat",
                    "client_id": client_id or "anonymous",
                    "message": message_data.get("message", "")
                }
            )
        except json.JSONDecodeError:
            # If not valid JSON, just broadcast as raw text
            await manager.broadcast(
                {
                    "type": "chat",
                    "client_id": client_id or "anonymous",
                    "message": data
                }
            )

def register_routes(app):
    """
    Register all WebSocket routes in this module
    """
    app.register_route("/ws/chat", handle_chat) 