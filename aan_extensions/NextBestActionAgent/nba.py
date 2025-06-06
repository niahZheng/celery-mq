import json
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Watson Assistant credentials
assistant_apikey = os.getenv('AAN_ASSISTANT_APIKEY')
assistant_url = os.getenv('AAN_ASSISTANT_URL')
assistant_id = os.getenv('AAN_ASSISTANT_ID') or os.getenv('AAN_ASSISTANT_ENVIRONMENT_ID')

# Initialize Watson Assistant
authenticator = IAMAuthenticator(assistant_apikey)
assistant = AssistantV2(
    version='2023-06-15',
    authenticator=authenticator
)
assistant.set_service_url(assistant_url)

def create_session():
    # Creates a new session and returns session_id
    response = assistant.create_session(assistant_id=assistant_id).get_result()
    return response['session_id']

def check_if_worth_sending(transcript):
    if len(transcript.split(" ")) < 3:
        return False
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "common_phrases.txt")
    with open(file_path, "r") as file:
        common_phrases = file.read().splitlines()

    transcript_cleaned = transcript.lower().strip()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([transcript_cleaned] + list(common_phrases))
    transcript_vector = tfidf_matrix[0:1] 
    max_similarity = 0

    for i in range(1, tfidf_matrix.shape[0]): 
        similarity = cosine_similarity(transcript_vector, tfidf_matrix[i:i+1])[0][0]
        max_similarity = max(max_similarity, similarity)

    threshold = 0.9 
    return max_similarity < threshold
    #return True

def generate_next_best_action(session_id, transcript, assistant_session_id, bypass=False):
    if check_if_worth_sending(transcript) or bypass:
        response = assistant.message(
            assistant_id=assistant_id,
            session_id=assistant_session_id,
            input={
                'message_type': 'text',
                'text': transcript
            }
        ).get_result()

        logging.info(f"Watson Assistant response for session {assistant_session_id}: {json.dumps(response, indent=2)}")

        action_text = 'No action suggested.'
        options = []

        if 'output' in response and 'generic' in response['output']:
            for response_item in response['output']['generic']:
                if response_item.get('response_type') == 'text':
                    action_text = response_item.get('text', action_text)
                    
                    # so far, on assistant, it will send a noresponse text back for blank action
                    if action_text == 'noresponse':
                        action_text = ""
                        options = ""
                elif response_item.get('response_type') == 'option':
                    options = response_item.get('options', [])

        return action_text, options
    print(f"not worth sending transcript: {transcript}")
    return "",""

def check_action_completion(session_id, agent_message,actions):
    # actions is a python list of strings
    completed_actions_idx = []
    completed_actions_id = []
    agent_sentences, _ = tokenize(agent_message)
    logging.info(f"Checking action completion for session {session_id} with message: {agent_message[:50]}")

    # modified
    # actions is array of:
    # {"action_id": action_id, "action": action, "status": "pending"}
    for idx, action_details_str in enumerate(actions):
        action_details = json.loads(action_details_str)
        print(f"action_details: {action_details}")
        action_id = action_details['action_id']
        action_text = action_details['action'].lower().strip()
        for sentence in agent_sentences:
            similarity = calculate_similarity(sentence, action_text)
            print(f"similarity: {similarity} for {sentence}")
            if similarity > 0.5:
                completed_actions_idx.append(idx)
                completed_actions_id.append(action_id)
                logging.info(f"Marking action ID {action_id} as completed for session {session_id}")
                break
    return completed_actions_idx, completed_actions_id

def tokenize(text):
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    return sentences, words

def calculate_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similarity[0][0]
