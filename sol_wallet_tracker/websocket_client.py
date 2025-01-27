import websockets
import json
import asyncio
import aiohttp
from sol_wallet_tracker.config import HELIUS_API_KEY
from .utils import handle_swap
import requests

class WebSocketClient:
    def __init__(self, account):
        """
        Initializes the WebSocket client with the Helius API key and target account.

        :param account: Public key of the account to track
        """
        if not HELIUS_API_KEY:
            raise ValueError("HELIUS_API_KEY not found. Ensure it is set in your .env file.")

        self.api_url = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        self.RPC_ENDPOINT = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        self.account = account
        self.running = False

    async def on_message(self, message):
        """
        Callback for handling incoming WebSocket messages.

        :param message: The received message in JSON format
        """
        try:
            
            if "params" not in message:  # Initial response without 'params'
                print("Connection established:", message)
            else:
                # Validate the nested keys exist before accessing them
                params = message.get("params", {})
                result = params.get("result", {})
                value = result.get("value", {})
                signature = value.get("signature")
                print("Signature:", signature)
                if signature:
                    # Fetch swap metadata
                    swap_meta = await self.process_signature(signature, self.RPC_ENDPOINT)
                    print("Swap meta:", swap_meta)
                    if swap_meta:
                        # Process the fetched swap metadata
                        await self.process_swap_meta(swap_meta)
                    else:
                        print(f"Swap metadata for signature {signature} is empty or invalid.")
                else:
                    print("Missing 'signature' in message:", message)
        except json.JSONDecodeError as e:
            print("Failed to decode JSON:", e)
        except Exception as e:
            print(f"Unexpected error while handling message: {e}")




    @staticmethod
    async def process_signature(swap_signature, RPC_ENDPOINT):
        # response = requests.post(
        #     RPC_ENDPOINT,
        #     headers={"Content-Type":"application/json"},
        #     json={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[swap_signature,{"encoding":"jsonParsed",'maxSupportedTransactionVersion':0}]}
        # )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RPC_ENDPOINT,
                headers={"Content-Type":"application/json"},
                json={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[swap_signature,{"encoding":"jsonParsed",'maxSupportedTransactionVersion':0}]}
            ) as response:
                print(await response.json())
                if response.status == 200:
                    data = await response.json()
                    print("Data from getTransaction", data)
                    # Safely access nested keys
                    result = data.get('result', {})
                    swap_meta = result.get('meta', {})
                    inner_instructions = swap_meta.get('innerInstructions', [])

                    if not inner_instructions:  # Check if empty or None
                        return None
                    return swap_meta  # Return raw metadata
                else:
                    # Log non-200 responses with details
                    error_message = await response.text()
                    print(f"Error fetching swap metadata: {response.status}, Details: {error_message}")
                    return None


    async def process_swap_meta(self, swap_meta):
        """
        Asynchronously processes a swap transaction.

        :param swap_meta: The swap transaction metadata to process
        """
        try:
            # Handle the swap metadata using your custom function
            action, token_ca, token_amount, sol_amount = handle_swap(swap_meta)

            # Debugging information
            
            print(f"Swap Details - Action: {action}, Token: {token_ca}, Token Amount: {token_amount}, SOL Amount: {sol_amount}")
        except KeyError as e:
            print(f"KeyError while processing swap meta: {e}")
        except Exception as e:
            print(f"Unexpected error in process_swap_meta: {e}")

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
        if not self.running:
            print("WebSocket closed intentionally.")
        else:
            print(f"WebSocket closed unexpectedly with status code {close_status_code} and message: {close_msg}")
            print("Attempting to reconnect...")
            asyncio.create_task(self.run())  # Reconnect if closure was unexpected

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


    async def stop(self):
        """
        Stops the WebSocket client gracefully.
        """
        if self.running:  # Only stop if the client is running
            self.running = False
            print("Stopping WebSocket client...")

    async def run(self):
        """
        Starts the WebSocket client and listens for messages.
        Reconnects if the connection drops.
        """
        self.running = True  # Mark the client as running
        while self.running:
            try:
                async with websockets.connect(self.api_url) as websocket:
                    print("WebSocket connected!")
                    subscription_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "logsSubscribe",
                        "params": [
                            {"mentions": [self.account]},
                            {"commitment": "confirmed"}
                        ]
                    }
                    await websocket.send(json.dumps(subscription_message))
                    print("Subscription request sent for account:", self.account)

                    while self.running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            await self.on_message(data)
                        except json.JSONDecodeError:
                            print("Failed to decode message:", message)
                        except websockets.ConnectionClosed:
                            print("WebSocket connection closed. Reconnecting...")
                            break  # Break the inner loop to reconnect
            except Exception as e:
                print(f"WebSocket connection error: {e}")
                if self.running:  # Only sleep and retry if still running
                    await asyncio.sleep(5)
