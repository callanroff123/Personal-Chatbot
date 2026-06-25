# Import required libraries
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
import json
from src.tools import (
    record_unknown_question,
    record_user_details,
    RECORD_UNKNOWN_QUESTION_JSON,
    RECORD_USER_DETAILS_JSON
)
from src.config import NAME
from src.context_scraper import load_context


# Set vars
load_dotenv(override = True)
TOOLS = [
    {"type": "function", "function": RECORD_USER_DETAILS_JSON},
    {"type": "function", "function": RECORD_UNKNOWN_QUESTION_JSON}
]


# Pydantic model for evaluation
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


# Chatbot
class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.openai_eval = OpenAI()
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
    
    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"""
            \nYou are an evaluator that decides whether a response to a question is acceptable.
            \nYou are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality.
            \nThe Agent is playing the role of {self.name} and is representing {self.name} on their website.
            \nThe Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website.
            \nThe Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:
        """
        evaluator_system_prompt += f"""
            \n## About Me: \n{self.about} \n
            \n## Resume: \n{self.resume} \n
            \n## Projects: \n{self.projects}
        """
        evaluator_system_prompt += f"""
            \nWith this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback.
        """
        return evaluator_system_prompt

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt
    
    def evaluate(self, reply, message, history) -> Evaluation:
        messages = (
            [{"role": "system", "content": self.evaluator_system_prompt()}] +
            [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        )
        response =self.openai_eval.beta.chat.completions.parse(
            model = "gpt-4o-mini", 
            messages = messages, 
            response_format = Evaluation
        )
        return response.choices[0].message.parsed
    
    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt()
        updated_system_prompt += f"\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = (
            [{"role": "system", "content": updated_system_prompt}] +
            history + 
            [{"role": "user", "content": message}]
        )
        response = self.openai.chat.completions.create(
            model = "gpt-4o-mini", 
            messages = messages,
            tools = TOOLS
        )
        return response.choices[0].message.content
    
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
        reply = response.choices[0].message.content
        evaluation = self.evaluate(reply, message, history)
        if evaluation.is_acceptable:
            print("Passed evaluation!")
        else:
            print("Failed evaluation - retrying...")
            print(evaluation.feedback)
            reply = self.rerun(reply, message, history, evaluation.feedback)
        return reply