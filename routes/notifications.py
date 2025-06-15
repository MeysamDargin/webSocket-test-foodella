from fastapi import WebSocket
import json
import asyncio
from typing import Dict, Any

async def handle_notifications(websocket: WebSocket, manager, client_id: str = None):
    """
    Handle notifications WebSocket connections
    """
    # Accept the connection
    await manager.connect(websocket, client_id or "anonymous")
    
    # Send welcome message
    await manager.send_personal_message(
        {"type": "system", "message": "Notifications channel connected"}, 
        websocket
    )
    
    # Handle commands from client
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                command = message_data.get("command")
                
                if command == "subscribe":
                    # Example of subscribing to a topic
                    topic = message_data.get("topic", "general")
                    await manager.send_personal_message(
                        {"type": "system", "message": f"Subscribed to {topic}"}, 
                        websocket
                    )
                    
                elif command == "send":
                    # Example of sending a notification to all clients or specific client
                    target = message_data.get("target")
                    notification = message_data.get("notification", {})
                    
                    if target:
                        await manager.broadcast(
                            {
                                "type": "notification",
                                "data": notification
                            },
                            client_id=target
                        )
                    else:
                        await manager.broadcast(
                            {
                                "type": "notification",
                                "data": notification
                            }
                        )
                        
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"}, 
                    websocket
                )
    except Exception as e:
        await manager.send_personal_message(
            {"type": "error", "message": str(e)}, 
            websocket
        )

def register_routes(app):
    """
    Register all WebSocket routes in this module
    """
    app.register_route("/ws/notifications", handle_notifications) 