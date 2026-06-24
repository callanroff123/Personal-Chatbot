# Import required libraries
from dotenv import load_dotenv
import os
import requests


# Load environment variables
load_dotenv(override=True)


# Handle push notifications via Pushover API
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )