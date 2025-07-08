import requests
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

auth_url = f"{os.getenv('AAN_ASSISTANT_URL')}/icp4d-api/v1/authorize"
payload = {
    "username": os.getenv('AAN_ASSISTANT_USERNAME'),
    "password": os.getenv('AAN_ASSISTANT_PASSWORD')
}
response = requests.post(auth_url, json=payload, verify=False)
wa_token =response.json()["token"]
print("watsonx assistant token:", wa_token)

assistant_url = f"{os.getenv('AAN_ASSISTANT_URL')}/assistant/ibm-software-hub-services-wo-wa"
assistant_instance = os.getenv('AAN_ASSISTANT_INSTANCE')
assistant_id = os.getenv('AAN_ASSISTANT_ID')
api_version = os.getenv('AAN_ASSISTANT_API_VERSION') 


def create_session():
    # Create session
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "accept": "application/json"
    }
    ############## This Request is for creating new session to get session ID 
    # First request to create session
    session_url = f"{assistant_url}/instances/{assistant_instance}/api/v2/assistants/{assistant_id}/sessions?version={api_version}"
    try:
        response = requests.post(
            session_url,
            headers=headers,
            verify=False
        )
        #response.raise_for_status()
        body = response.json()    
        sessionId = body['session_id']
        return sessionId
    except requests.exceptions.RequestException as error:
        print(f"Error: {error}")
        raise

def generate_quick_actions(wa_session_id, message_payload):
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "accept": "application/json"
    }
    try:
        message_url = f"{assistant_url}/instances/{assistant_instance}/api/v2/assistants/{assistant_id}/sessions/{wa_session_id}/message?version={api_version}"  # Add your URL here
        
        response = requests.post(
            message_url,
            headers=headers,
            json=message_payload,
            verify=False
        )
        response_data= response.json()
        response_texts = [
            item["text"]
            for item in response_data.get("output", {}).get("generic", [])
            if item.get("response_type") == "text"
        ]
        custom_response = {
            "session_ID": response_data.get("context", {}).get("global", {}).get("session_id", "unknown"),
            "intentType": response_data.get("context", {}).get("skills", {}).get("actions skill", {}).get("skill_variables", {}).get("intent", "None"),
            "quickActions": response_texts,
            "query" :response_data.get("context", {}).get("skills", {}).get("actions skill", {}).get("skill_variables", {}).get("query_", ""),
            "conversation_ID":  response_data.get("context", {}).get("skills", {}).get("actions skill", {}).get("skill_variables", {}).get("conversation_ID", "None"),
        }
        return custom_response        
    except requests.exceptions.RequestException as error:
        print(f"Error: {error}")
        raise

    