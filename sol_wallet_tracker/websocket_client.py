import websocket
import json
from sol_wallet_tracker.config import HELIUS_API_KEY

class WebSocketClient:
    def __init__(self, account):
        """
        Initializes the WebSocket client with the Helius API key and target account.

        :param account: Public key of the account to track
        """
        if not HELIUS_API_KEY:
            raise ValueError("HELIUS_API_KEY not found. Ensure it is set in your .env file.")

        self.api_url = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        self.account = account

    def on_message(self, ws, message):
        """
        Callback for handling incoming WebSocket messages.

        :param ws: WebSocket connection object
        :param message: The received message in JSON format
        """
        try:
            data = json.loads(message)
            print("Received message:", json.dumps(data, indent=4))
            # Add custom logic to parse and process token swap data here
        except json.JSONDecodeError as e:
            print("Failed to decode JSON:", e)

    def on_error(self, ws, error):
        """
        Callback for handling WebSocket errors.

        :param ws: WebSocket connection object
        :param error: The error encountered
        """
        print("WebSocket error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        """
        Callback for handling WebSocket closure.

        :param ws: WebSocket connection object
        :param close_status_code: Status code for the closure
        :param close_msg: Closure message
        """
        print(f"WebSocket closed with status code {close_status_code} and message: {close_msg}")

    def on_open(self, ws):
        """
        Callback for when the WebSocket connection is successfully opened.

        :param ws: WebSocket connection object
        """
        print("WebSocket connected!")
        subscription_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {
                    "mentions":[self.account],
                },
                {"commitment": "confirmed"}
            ]
        }
        ws.send(json.dumps(subscription_message))
        print("Subscription request sent for account:", self.account)

    def run(self):
        """
        Starts the WebSocket client and listens for messages.
        """
        ws = websocket.WebSocketApp(
            self.api_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.on_open = self.on_open
        ws.run_forever(ping_interval=30, ping_timeout=10)
