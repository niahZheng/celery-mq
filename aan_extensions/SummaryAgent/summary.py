import requests
import json
import os

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get('AAN_WML_APIKEY')
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
WATSONX_URL = os.environ.get('AAN_WML_URL', "https://us-south.ml.cloud.ibm.com") + "/ml/v1/text/chat?version=2023-05-29"
PROJECT_ID=os.environ.get('AAN_WML_PROJECT_ID')
MODEL_ID = os.environ.get('AAN_SUMMARIZATION_LLM_MODEL_NAME', 'ibm/granite-13b-chat-v2')
#MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
#MODEL_ID = "meta-llama/llama-3-2-3b-instruct"

def get_iam_token():
    """Retrieve IAM token using API key"""
    try:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY}
        response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"get_iam_token.....IAM token request failed.....error message: {response.text}")
            raise Exception(f"IAM token request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"get_iam_token......error message: {str(e)}")
        print(f"get_iam_token......error type: {type(e)}")

def format_chat_history_for_prompt(conversations_json):
    """Format chat history into transcript string"""
    formatted_lines = []
    for turn in conversations_json:
        for speaker, utterance in turn.items():
            clean_utterance = utterance.replace('\n', ' ').strip()
            formatted_lines.append(f"[{speaker.upper()}]: {clean_utterance}")
    return "\n".join(formatted_lines)

def summarize(conversations_string):
    """
    Call WatsonX LLM with formatted chat history
    Returns API response JSON
    """

    # Get IAM token
    access_token = 'none'
    try:
        access_token = get_iam_token()
        # print(access_token)
    except Exception as e:
        print(f"try to get access_token......error message: {str(e)}")
        print(f"try to get access_token......error type: {type(e)}")

    # Construct prompt (PRESERVED EXACTLY AS REQUESTED)
    prompt_template = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
You are a helpful assistant that summarizes customer support chat transcripts. Given a chat conversation between a customer and an agent, extract:

1. Intent - the customer's initial request or purpose for contacting.
2. Request Changes - Summary of actions, tasks, or requests completed during the conversation, such as flight changed, ticket booked, or customer question answered. This includes any updates or modifications made based on the customer's input.

Output the result strictly in a valid JSON format with keys: intent, request_changes.
Do not include any additional text or explanations, just the JSON output.

### Example 1:

Chat Transcript:
Customer: Hi, I need to change my flight.
Agent: Sure, I can help you with that. What date would you like to change it to?
Customer: Please move it from July 7 to July 8.
Agent: Done. I've rebooked you for July 8. Is there anything else?
Customer: No, that's all. Thanks!
Agent: You're welcome! [Quick Action: Rebook Flight]

Output:

{{
  \"intent\": \"Change flight date\",
  \"request_changes\": \"Flight changed from July 7 to July 8\"
}}
### Example 2:

Chat Transcript:
Customer: Hi, I want to cancel my hotel booking.
Agent: I can help with that. Which booking would you like to cancel?
Customer: The one for Las Vegas on June 30.
Agent: It is canceled now. [Quick Action: Cancel Booking]

Output:
{{
  \"intent\": \"Cancel hotel booking\",
  \"request_changes\": \"Canceled hotel booking for Las Vegas on June 30\"
}}
### Now process the following chat:

ONLY use the chat transcript below to summarize the output in JSON format, do NOT speculate.

Chat Transcript:
{conversations_string}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
    
    # Prepare request body
    body = {
        "messages": [{"role": "user", "content": prompt_template}],
        "project_id": PROJECT_ID,
        "model_id": MODEL_ID,
        "max_tokens": 2000,
        "temperature": 0,
        "top_p": 1
    }
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Make API call
    print("Starting LLM API call...")
    response = requests.post(WATSONX_URL, headers=headers, json=body)
    
    if response.status_code == 200:
        # return response.json()
        result = response.json()
        try: 
            if "choices" in result and len(result["choices"])>0:
                #===================special hard coding for returned JSON string.....start
                print("result choices 0..............", result["choices"][0])
                # return result["choices"][0]["message"]["content"]
                xxx = result["choices"][0]["message"]["content"] 
                # it is a string, sometimes with a wrong format, 
                # 'content': '{\n  "intent": "Reschedule flight",\n  "request_changes": "Flight changed from August 20 to September 22"'}
                # it is 22"'}, but it should be 22"}'
                if '{' in xxx and '}' in xxx:
                    print("JSON string..............we have both {}...we are good") 
                    pass
                elif '{' in xxx and '}' not in xxx:
                    print("JSON string..............missing }") 
                    xxx = xxx + '\n}'
                elif '{' not in xxx and '}' in xxx:
                    print("JSON string..............missing {") 
                    xxx = '{\n ' + xxx 
                else:    
                    print("JSON string..............missing both {}") 
                    xxx = '{\n ' + xxx + '\n}'
                #===================special hard coding for returned JSON string.....end 
                return xxx
            
            else:
                print(f"response something wrong......error message: {response.text}")
                raise Exception(f"Error something wrong ({response.status_code}), returned text: {response.text}")
        except Exception as e:
            print(f"Unexpected error message......error message: {response.text}")
            print(f"Unexpected error message: {str(e)}")
            print(f"Unexpected error type: {type(e)}")
            raise Exception(f"Error something wrong ({response.status_code}), returned text: {response.text}")
        
    else:
        raise Exception(f"LLM API Error ({response.status_code}): {response.text}")

#===================================================================Example usage
if __name__ == "__main__":


    chat_input = {
        "conversations": [
            {"guest": "hello", "concierge": "Welcome! How can I help?"},
            {"guest": "I need to book a ticket to Bei Jing Jun 30", "concierge": "Sure, let me book it for you! It is done."},
            {"guest": "Thanks", "concierge":" You're welcome!"}
        ]
    }

    formatted = format_chat_history_for_prompt(chat_input["conversations"])
    
    try:
        result = summarize(formatted)
        print("LLM Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")