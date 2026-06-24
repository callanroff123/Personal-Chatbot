# Import required libraries
from dotenv import load_dotenv
from openai import OpenAI
import json
from pypdf import PdfReader
import gradio as gr
from tools import (
    record_unknown_question,
    record_user_details,
    RECORD_UNKNOWN_QUESTION_JSON,
    RECORD_USER_DETAILS_JSON
)
from config import NAME
from context_scraper import load_context


# Set vars
load_dotenv(override = True)
TOOLS = [
    {"type": "function", "function": RECORD_USER_DETAILS_JSON},
    {"type": "function", "function": RECORD_UNKNOWN_QUESTION_JSON}
]


# Chatbot
class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = NAME
        print("Fetching context...", flush = True)
        self.context = load_context()
        print("Context successfully retrieved!", flush = True)
        self.about = [item["text"] for item in self.context if item["type"].lower() == "about"][0]
        self.resume = [item["text"] for item in self.context if item["type"].lower() == "resume"][0]
        self.projects = [item["text"] for item in self.context if item["type"].lower() == "projects"][0]

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush = True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id
                }
            )
        return results
    
    def system_prompt(self):
        system_prompt = f"""
            \nYou are acting as {self.name}. You are answering questions on {self.name}'s website, particularly questions related to {self.name}'s career, background, skills and experience.
            \nYour responsibility is to represent {self.name} for interactions on the website as faithfully as possible.
            \nYou are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions.
            \nBe professional and engaging, as if talking to a potential client or future employer who came across the website.
            \nIf you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career.
            \nIf the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. 
        """
        system_prompt += f"""
            \n## About Me: \n{self.about} \n
            \n## Resume: \n{self.resume} \n
            \n## Projects: \n{self.projects}
        """
        system_prompt += f"""
            \nWith this context, please chat with the user, always staying in character as {self.name}.
        """
        return system_prompt
    
    def chat(self, message, history):
        messages = (
            [{"role": "system", "content": self.system_prompt()}] + 
            history + 
            [{"role": "user", "content": message}]
        )
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model = "gpt-4o-mini", 
                messages = messages, 
                tools = TOOLS
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

# Run program
if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type = "messages").launch(
        server_name = "0.0.0.0",
        server_port = 7860
    )
    