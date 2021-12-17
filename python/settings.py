from dotenv import load_dotenv
import os

# Load env vars from .env file
load_dotenv()

HOST = "0.0.0.0"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}/"

# GitHub
GITHUB_CLIENT_ID = os.getenv("CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("CLIENT_SECRET")