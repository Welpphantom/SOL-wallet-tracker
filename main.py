# main.py
from sol_wallet_tracker.websocket_client import WebSocketClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def main():
    # Replace with the public key of the account you want to track
    account_public_key = os.getenv("ACCOUNT_PUBLIC_KEY")

    # Create the WebSocket client and run it
    client = WebSocketClient(account_public_key)
    client.run()

if __name__ == "__main__":
    main()


