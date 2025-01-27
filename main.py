# main.py
from sol_wallet_tracker.websocket_client import WebSocketClient
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from .env file
load_dotenv()


async def main():
    # Replace with the public key of the account you want to track
    account_public_key = os.getenv("ACCOUNT_PUBLIC_KEY")
    if not account_public_key:
        raise ValueError("ACCOUNT_PUBLIC_KEY environment variable is not set")

    # Create the WebSocket client and run it
    client = WebSocketClient(account_public_key)
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())


