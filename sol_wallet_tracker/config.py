from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the Helius API key
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not HELIUS_API_KEY:
    raise ValueError("HELIUS_API_KEY not found. Please add it to your .env file.")
