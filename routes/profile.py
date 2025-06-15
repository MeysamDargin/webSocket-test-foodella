from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import json
import httpx
import asyncio
from typing import Dict, Any, Optional

async def fetch_profile(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch profile data from the API using the access token
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://tapi.foodella.ir/api/profile/", headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        return None

async def handle_profile(websocket: WebSocket, manager, client_id: str = None):
    """
    Handle profile WebSocket connections
    """
    # Get access token from query parameters
    access_token = client_id  # Using client_id as access token
    
    if not access_token:
        # Reject connection if no access token provided
        await websocket.close(code=1008, reason="No access token provided")
        return
    
    # Fetch profile data before accepting the connection
    profile_data = await fetch_profile(access_token)
    
    if not profile_data or not profile_data.get("status"):
        # Reject connection if token is invalid
        await websocket.close(code=1008, reason="Invalid access token")
        return
    
    # Extract user_id from profile data to use as the actual client_id
    # This ensures that webhook updates can reach this connection
    user_id = str(profile_data.get("profile", {}).get("id", ""))
    
    if not user_id:
        await websocket.close(code=1008, reason="Could not determine user ID")
        return
    
    # Accept the connection - this is now handled by the manager.connect method
    # Do NOT call websocket.accept() here
    await manager.connect(websocket, user_id)
    
    try:
        # Send profile data immediately
        await manager.send_personal_message(profile_data, websocket)
        
        # Send confirmation that this connection will receive profile updates
        await manager.send_personal_message(
            {
                "type": "system",
                "message": f"Connected to profile updates for user {user_id}"
            }, 
            websocket
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages but mainly keep the connection alive
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    command = message_data.get("command")
                    
                    # Handle refresh profile command
                    if command == "refresh_profile":
                        profile_data = await fetch_profile(access_token)
                        if profile_data and profile_data.get("status"):
                            await manager.send_personal_message(profile_data, websocket)
                        else:
                            await manager.send_personal_message(
                                {"status": False, "message": "Failed to refresh profile"}, 
                                websocket
                            )
                            
                except json.JSONDecodeError:
                    # Ignore invalid JSON
                    pass
                    
            except WebSocketDisconnect:
                manager.disconnect(websocket, user_id)
                break
                
    except Exception as e:
        print(f"Profile WebSocket error: {str(e)}")
        manager.disconnect(websocket, user_id)

def register_routes(app):
    """
    Register all WebSocket routes in this module
    """
    app.register_route("/ws/profile", handle_profile) 