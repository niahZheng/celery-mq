from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import json

env_id = '2823393c-3dd5-4528-9f5e-5cfd435a55a9'
authenticator = IAMAuthenticator('hUFu6P1tLIhOcrdRV28m3wod3p1P2nwilrNccPMLlRaC') 
assistant = AssistantV2(
    version='2024-08-25',
    authenticator=authenticator
)

assistant.set_service_url('https://api.eu-gb.assistant.watson.cloud.ibm.com')
# assistant.set_http_config({'timeout': 100})

test_id = "cda1ce9a-af1e-499d-897c-e82da9c165e5"
test_type="session_ended" # "session_started" "session_ended" "transcription"
topic = f"agent-assist/{test_id}/{test_type}" 
test_message = {}

if test_type == "session_ended": 
    test_message = {
        "type": test_type, 
        "parameters": {
            "conversationid": test_id,
            "session_id": test_id,
            "conversationStartTime": "2025-06-19 03:37:21.533123", 
            # nothing if from UI 
            "conversationEndTime": str(datetime.now()), # "2025-06-19 03:55:22.544123", # from Genesys
        },
    }

response = assistant.message(
    assistant_id = env_id,
    # environment_id = env_id,
    session_id= session_res.get('session_id'),
    input={
        'message_type': 'text',
        'text': 'Will I be charged if my luggage is over the limit?',
        'options': {'return_context': True}
        }
        ,
    context={
        'skills': {
            'actions skill': {
                'skill_variables': {
                    'Identified': "True",
                    'Verified': "True"
                }
            }
        }
    }
    ).get_result()

session_variables = response.get("context", {}).get("skills", {}).get("actions skill", {}).get("skill_variables", {})
print("Session Variables:", session_variables)

print(json.dumps(response, indent=2))