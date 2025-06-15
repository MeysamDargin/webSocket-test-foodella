#!/usr/bin/env python3
"""
Test script to simulate webhook calls for profile updates
"""
import requests
import json
import argparse
import sys

def send_webhook(user_id, action, server_url="http://localhost:8000"):
    """
    Send a test webhook to the server
    """
    webhook_url = f"{server_url}/webhook/profile"
    
    # Sample profile data
    payload = {
        "action": action,
        "user_id": user_id,
        "profile": {
            "id": user_id,
            "fullName": "کاربر تست",
            "phoneNumber": "09123456789",
            "email": "test@example.com",
            "birthdate": "1990-01-01",
            "biography": "این یک پروفایل تست است",
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
                "url": "https://via.placeholder.com/150",
                "type": "image"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Sending {action} webhook for user {user_id}...")
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def check_connected_clients(server_url="http://localhost:8000"):
    """
    Check which clients are currently connected
    """
    try:
        response = requests.get(f"{server_url}/api/connected-clients")
        if response.status_code == 200:
            clients = response.json().get("clients", [])
            print(f"Connected clients: {clients}")
            return clients
        else:
            print(f"Failed to get connected clients: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error checking connected clients: {str(e)}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test WebSocket webhooks")
    parser.add_argument("--user-id", type=int, required=True, help="User ID to send webhook for")
    parser.add_argument("--action", choices=["created", "updated", "deleted"], default="updated", 
                        help="Action type (created, updated, deleted)")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--check-clients", action="store_true", help="Check connected clients")
    
    args = parser.parse_args()
    
    if args.check_clients:
        check_connected_clients(args.server)
    else:
        success = send_webhook(args.user_id, args.action, args.server)
        sys.exit(0 if success else 1) 