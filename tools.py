# Import push notification handler
from push_notification import push


# record_user_detail tool handler
RECORD_USER_DETAILS_JSON = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}


# record_unknown_question
RECORD_UNKNOWN_QUESTION_JSON = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}


# Tool to send push notification of user details
# Triggers when LLM receives a question related to connecting with person
def record_user_details(
    email, 
    name = "Name not provided", 
    notes="not provided"
):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


# Tool to send push notification when LLM receives a query it can't respond to with the context it's given
def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}