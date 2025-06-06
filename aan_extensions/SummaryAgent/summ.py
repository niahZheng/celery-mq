# Import necessary libraries
import ibm_watson_machine_learning
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes, DecodingMethods
# import textwrap
# import nltk
import os
# from nltk.tokenize import sent_tokenize, word_tokenize
# from collections import Counter
import logging

logging.basicConfig(level=logging.INFO)

# nltk.download('punkt')
# Check the installed version of ibm_watson_machine_learning

# from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes

# # List all available model types
# for model_type in ModelTypes:
#     print(model_type)


DETAIL = 0.5
MAX_NEW_TOKENS = 500
TOKEN_LIMIT = 1024
# Initialize the model
generate_params = {GenParams.MAX_NEW_TOKENS: MAX_NEW_TOKENS}
model_name = os.environ.get('AAN_SUMMARIZATION_LLM_MODEL_NAME', 'ibm/granite-13b-chat-v2')
logging.info(f'LLM model name to be used: {model_name}')
model = Model(
    model_id=model_name,
    params=generate_params,
    credentials={
        "apikey": os.environ.get('AAN_WML_APIKEY'),
        "url": os.environ.get('AAN_WML_URL', "https://us-south.ml.cloud.ibm.com")
    },
    project_id=os.environ.get('AAN_WML_PROJECT_ID')
)

def summarize_text(segment):
    """
    Summarize a given text segment using the Llama 2 model, ensuring the summary is a single paragraph.

    :param segment: The text segment to be summarized.
    :return: The summary of the segment as a single paragraph.
    """
    try:
        system_prompt = "<<SYS>>You are a concise and efficient summarizer. " \
                        "Generate a summary that condenses the conversation into a single paragraph, " \
                        "focusing on main points, emotions, and outcomes. " \
                        "Avoid itemizing the dialogue or adding new information. " \
                        "Ensure the summary is coherent, neutral, and unbiased.<</SYS>>"
        
        instruction_prompt = f"{segment}"

        full_prompt = f"<s>[INST]{system_prompt}\n\n{instruction_prompt}[/INST]</s>"

        summary_response = model.generate_text(prompt=full_prompt)

        summary_text = summary_response if isinstance(summary_response, str) else summary_response.get('generated_text', '')

        summary_text = ' '.join(summary_text.splitlines())

        return summary_text
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return ""



def summarize(transcript):
    """
    Summarize the updated transcript, incorporating the new sentence and speaker information.

    :param new_sentence: The latest sentence added to the transcript.
    :param transcript: The full transcript of the call so far.
    :param current_summary: The current summary of the transcript.
    :param speaker: The speaker of the new sentence ('external' or 'internal').
    :return: The updated summary.
    """

    # if not is_valuable_sentence(new_sentence, current_summary):
    #     return current_summary

    #speaker_tag = "[Agent]" if speaker == "internal" else "[Client]"
    #annotated_sentence = f"{speaker_tag} {new_sentence}"
    #updated_transcript = f"{transcript} {annotated_sentence}" if transcript else annotated_sentence

    #segments = segment_transcript(updated_transcript)

    #segment_summaries = [summarize_text(segment) for segment in segments]

    #combined_summary = ' '.join(segment_summaries)
    combined_summary = summarize_text(transcript)

    if len(combined_summary.split()) > 80:
        combined_summary = summarize_text(combined_summary)

    # if len(combined_summary.split()) < 30:
    #     logging.warning("The summary may be too concise. Consider adjusting the segmenting or summarization logic.")

    return combined_summary

