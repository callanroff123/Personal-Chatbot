# Allow relative imports
import os
import sys
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_PATH)
os.environ["PYTHONPATH"] = ROOT_PATH


# Import required libraries
import gradio as gr
from src.chatbot import Me
from src.config import (
    SERVER_NAME,
    SERVER_PORT
)
    

# Run program
if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type = "messages").launch(
        server_name = SERVER_NAME,
        server_port = SERVER_PORT
    )
    