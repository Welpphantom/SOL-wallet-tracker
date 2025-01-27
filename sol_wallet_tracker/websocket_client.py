import websockets
import json
import asyncio
import aiohttp
from sol_wallet_tracker.config import HELIUS_API_KEY
from .utils import handle_swap

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

    async def on_message(self, message):
        """
        Callback for handling incoming WebSocket messages.

        :param message: The received message in JSON format
        """
        try:
            data = json.loads(message)
            # Handle initial response that does not contain the params key
            if "params" not in data:
                print("Connection established:", data)
            elif "params" in data:
                signature = data['params']['result']['value']['signature']
                await self.process_signature(signature)
            else:
                print("Unexpected message structure:", data)

        except json.JSONDecodeError as e:
            print("Failed to decode JSON:", e)
        except KeyError as e:
            print(f"KeyError: Missing expected key in message - {e}")

    @staticmethod
    async def process_signature(swap_signature):
        """
        Asynchronously fetches swap transaction details.

        :param swap_signature: The transaction signature to fetch details for
        :return: Swap metadata (raw JSON) or None if an error occurs
        """
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [swap_signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            }
            try:
                async with session.post(
                    f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        swap_meta = data['result']['meta']
                        if len(swap_meta['innerInstructions']) == 0:
                            return None
                        return swap_meta  # Return raw metadata
                    else:
                        print(f"Error fetching swap metadata: {response.status}")
                        return None
            except Exception as e:
                print(f"Error in process_signature: {e}")
                return None

    async def process_swap(self, signature):
        """
        Asynchronously processes a swap transaction.

        :param signature: The transaction signature to process
        """
        swap_meta = await self.process_signature(signature)
        if swap_meta:
            # Call handle_swap to process the metadata
            action, token_ca, token_amount, sol_amount = handle_swap(swap_meta)
            print(f"Swap Details - Action: {action}, Token: {token_ca}, Token Amount: {token_amount}, SOL Amount: {sol_amount}")
        else:
            print("No swap details found or error occurred.")

    def on_error(self, ws, error):
        """
        Callback for handling WebSocket errors.

        :param ws: WebSocket connection object
        :param error: The error encountered
        """
        print("WebSocket error:", error)
        if hasattr(error, 'args'):
            print("Error details:", error.args)

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

    async def run(self):
        """
        Starts the WebSocket client and listens for messages.
        """
        async with websockets.connect(self.api_url) as websocket:
            print("WebSocket connected!")
            subscription_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {
                        "mentions": [self.account],
                    },
                    {"commitment": "confirmed"}
                ]
            }
            await websocket.send(json.dumps(subscription_message))
            print("Subscription request sent for account:", self.account)

            while True:
                message = await websocket.recv()
                await self.on_message(message)
