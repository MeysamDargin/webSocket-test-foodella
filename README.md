# Dynamic WebSocket Manager

A lightweight, modular WebSocket management system built with FastAPI. This project provides a flexible framework for creating and managing WebSocket connections with dynamic routing.

## Features

- Dynamic WebSocket route loading
- Client management with unique IDs
- Broadcast messaging (to all clients or specific clients)
- Simple API for creating new WebSocket endpoints
- Built-in test client interface
- Profile webhook for real-time profile updates

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

Run the following command from the project root:

```bash
python -m app.app
```

or directly:

```bash
python app/app.py
```

or using the run script:

```bash
python run.py
```

The server will start at `http://localhost:8000` and automatically reload when code changes.

### Creating New WebSocket Routes

1. Create a new Python file in the `routes` directory (e.g., `routes/my_route.py`)
2. Define your handler function and register it:

```python
from fastapi import WebSocket

async def handle_my_route(websocket: WebSocket, manager, client_id: str = None):
    # Send welcome message
    await manager.send_personal_message(
        {"type": "system", "message": "Welcome to my route!"},
        websocket
    )

    # Handle messages
    while True:
        data = await websocket.receive_text()
        # Process data...
        await manager.broadcast({"type": "message", "data": data})

def register_routes(app):
    app.register_route("/ws/my_route", handle_my_route)
```

3. The route will be automatically loaded when the server starts

### WebSocket Manager API

- `manager.connect(websocket, client_id)`: Accept a connection and register it
- `manager.disconnect(websocket, client_id)`: Remove a connection
- `manager.send_personal_message(message, websocket)`: Send a message to a specific client
- `manager.broadcast(message, client_id=None)`: Send a message to all clients or a specific client

### Profile Webhook

The server provides a webhook endpoint for receiving profile updates:

```
POST /webhook/profile
```

Example payload:

```json
{
  "action": "updated",
  "user_id": 123,
  "profile": {
    "id": 123,
    "fullName": "نام کاربر",
    "phoneNumber": "09123456789",
    "email": "user@example.com",
    "birthdate": "1990-01-01",
    "biography": "توضیحات کاربر",
    "categories": ["غذا", "نوشیدنی"],
    "province": {
      "id": 1,
      "name": "تهران"
    },
    "city": {
      "id": 1,
      "name": "تهران"
    },
    "medias": {
      "id": 789,
      "url": "https://example.com/profile.jpg",
      "type": "image"
    }
  }
}
```

When the webhook receives an update, it will broadcast the profile data to all WebSocket connections for that user.

### Test Client

Open `http://localhost:8000` in your browser to access the test client interface, which allows you to:

- Connect to the chat WebSocket
- Send and receive chat messages
- Connect to the notifications WebSocket
- Send commands to the notification system

## Project Structure

```
.
├── app/
│   ├── app.py            # Main application file
│   ├── __init__.py       # Package initialization
│   └── static/           # Static files for the test client
│       └── index.html    # Test client interface
├── routes/
│   ├── __init__.py       # Package initialization
│   ├── chat.py           # Chat WebSocket route
│   ├── notifications.py  # Notifications WebSocket route
│   └── profile.py        # Profile WebSocket route
├── run.py                # Entry point script
├── test_webhook.py       # Test script for webhook
└── requirements.txt      # Project dependencies
```

## Testing the Webhook

You can use the included test script to simulate webhook calls:

```bash
# Check connected clients
python test_webhook.py --check-clients

# Send a test webhook for user ID 123
python test_webhook.py --user-id 123 --action updated
```
# webSocket-test-foodella
