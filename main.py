# main.py
from sol_wallet_tracker.websocket_client import WebSocketClient
from dotenv import load_dotenv
import os
import asyncio
import signal
import sys

# Load environment variables from .env file
load_dotenv()

def validate_env_vars():
    """
    Validate that all required environment variables are set.
    """
    required_vars = ["ACCOUNT_PUBLIC_KEY", "HELIUS_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"{var} environment variable is not set")

async def main():
    """
    Entry point for the WebSocket client application.
    """
    # Validate required environment variables
    validate_env_vars()

    # Get the account public key from the environment
    account_public_key = os.getenv("ACCOUNT_PUBLIC_KEY")

    # Create the WebSocket client
    client = WebSocketClient(account_public_key)

    # Set up graceful shutdown
    stop_event = asyncio.Event()

    def shutdown():
        print("\nGraceful shutdown initiated...")
        stop_event.set()

    signal.signal(signal.SIGINT, lambda s, f: shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown())

    # Run the WebSocket client
    try:
        await asyncio.gather(client.run(), stop_event.wait())
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        print("WebSocket client stopped. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


