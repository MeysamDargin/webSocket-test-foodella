from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import importlib
import os
import pkgutil
from typing import Dict, List, Callable, Any

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        try:
            await websocket.accept()
        except RuntimeError as e:
            # If the WebSocket is already accepted, ignore the error
            if "websocket.accept" not in str(e):
                raise
                
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
                
    async def send_personal_message(self, message: Any, websocket: WebSocket):
        await websocket.send_json(message)
        
    async def broadcast(self, message: Any, client_id: str = None):
        if client_id and client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)
        else:
            for connections in self.active_connections.values():
                for connection in connections:
                    await connection.send_json(message)

    def get_connected_clients(self):
        """Get a list of all connected client IDs"""
        return list(self.active_connections.keys())

class WebSocketApp:
    def __init__(self):
        self.app = FastAPI()
        self.manager = WebSocketManager()
        self.routes = {}
        
        # Setup static files
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        @self.app.get("/")
        async def get_index():
            return FileResponse(os.path.join(static_dir, "index.html"))
            
        # Add webhook endpoint for profile updates
        @self.app.post("/webhook/profile")
        async def profile_webhook(request: Request):
            try:
                # Parse the webhook payload
                payload = await request.json()
                
                # Extract user_id and action
                user_id = payload.get("user_id")
                action = payload.get("action")
                profile_data = payload.get("profile", {})
                
                if not user_id:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Missing user_id in payload"}
                    )
                
                # Convert user_id to string for consistency with WebSocket client_id
                user_id = str(user_id)
                
                # Broadcast the profile update to the user's WebSocket connections
                await self.manager.broadcast(
                    {
                        "type": "profile_update",
                        "action": action,
                        "profile": profile_data
                    },
                    client_id=user_id
                )
                
                return JSONResponse(
                    content={
                        "status": "success",
                        "message": f"Profile update for user {user_id} broadcasted successfully",
                        "delivered_to": user_id in self.manager.active_connections
                    }
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to process webhook: {str(e)}"}
                )
                
        # Add endpoint to check connected clients (for debugging)
        @self.app.get("/api/connected-clients")
        async def get_connected_clients():
            return {"clients": self.manager.get_connected_clients()}
            
        self._load_routes()
        
    def _load_routes(self):
        """Dynamically load all WebSocket routes from the routes directory"""
        routes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "routes")
        
        if not os.path.exists(routes_dir):
            os.makedirs(routes_dir)
            
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(routes_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# WebSocket routes package\n")
        
        # Import all modules from routes package
        routes_package = "routes"
        for _, name, is_pkg in pkgutil.iter_modules([routes_dir]):
            if not is_pkg:
                module = importlib.import_module(f"{routes_package}.{name}")
                if hasattr(module, "register_routes"):
                    module.register_routes(self)
    
    def register_route(self, path: str, handler: Callable):
        """Register a WebSocket route handler"""
        self.routes[path] = handler
        
        @self.app.websocket(path)
        async def endpoint(websocket: WebSocket, client_id: str = None):
            try:
                await handler(websocket, self.manager, client_id)
            except WebSocketDisconnect:
                self.manager.disconnect(websocket, client_id or "anonymous")
    
    def get_app(self):
        return self.app

# Create the application instance
websocket_app = WebSocketApp()
app = websocket_app.get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True) 