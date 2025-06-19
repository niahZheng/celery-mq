from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
from opentelemetry import trace
from opentelemetry.trace import SpanKind
import traceback
# from .summ import summarize
import logging
import json

logger = logging.getLogger(__name__)


class colors:
    OKGREEN = "\033[92m"
    OKBLUE = "\033[94m"
    ENDC = "\033[0m"


# WORK IN PROGRESS - PLACEHOLDER
@app.task(base=BaseTask.BaseTask, bind=True)
def process_transcript(self, topic, message):
    
    with trace.get_tracer(__name__).start_as_current_span(
        "process_transcript", kind=SpanKind.PRODUCER
    ) as span:
        #--------# the return result is stored in the celery backend, at the end
        result = topic + "---" + message
        print(f"SummaryAgent ============= {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}")

        #--------# try block of processing for sio 
        try:
            message_data = json.loads(message)
            client_id = message_data["conversationid"] #it is conversation id from Geneysis UI 
            print(f"SummaryAgent ============= client_id: {client_id} \n")
            print( "SummaryAgent ============= message start ============= \n")
            print(json.dumps(message_data, indent=2, ensure_ascii=False))
            print(" SummaryAgent ============= message end ============= \n")

            with trace.get_tracer(__name__).start_as_current_span("redis_op"):
                print("-----------------------testing, summary 1")
                if isinstance(client_id, str) and len(client_id) > 5: # must have client_id 

                    print("-----------------------testing, summary 2")
                    ###=============check type to see if we need to do summarization....start
                    message_type = message_data["type"]
                    if message_type == "session_ended" or message_type == "session_manual":
                        pass # yes, we should do summary here 
                    else:
                        print("SummaryAgent ============= there is no need to do summary for type: ", message_type)
                        return

                    ###=============check type to see if we need to do summarization....end 
                    print("-----------------------testing, summary 3")

                    ###=============get history chats....start
                    transcripts_obj=[]
                    transcription_text=''
                    """
                    try: 
                        print("-----------------------testing, summary 4")
                        turns_counter = self.redis_client.llen(client_id) or 0
                        print("-----------------------testing, summary 5")
                        print(f"Turns counter: {turns_counter}")
                        if (turns_counter != 0) and (turns_counter % 2 == 0):
                            transcripts_obj = self.redis_client.lrange(
                                client_id, 0, -1
                            )
                            transcripts_dicts = [
                                json.loads(item) for item in transcripts_obj
                            ]
                            transcription_text = "\n".join(
                                f"{'Agent' if item['source'] == 'internal' else 'Customer'}: {item['text']}"
                                for item in transcripts_dicts
                            )
                    except Exception as e:
                        print(f"redis error message: {str(e)}")
                        print(f"redis error type: {type(e)}")
                    """
                    ###=============get history chats....end 


                    with trace.get_tracer(__name__).start_as_current_span(
                        "summarize"
                    ):
                        # new_summary = summarize(transcription_text) # the real summary from LLM 
                        print("SummaryAgent ============= input list:", transcripts_obj)
                        print("SummaryAgent ============= input for LLM:" + transcription_text)
                        new_summary = "*********This is a test summary This is a test summary This is a test summary This is a test summary"

                        if new_summary:
                            summary_topic = f"agent-assist/{client_id}/summarization"
                            summary_message = json.dumps(
                                {
                                    "type": "summary",
                                    "parameters": {
                                        "text": new_summary,
                                        "final":  True if message_type == "session_ended" else False,
                                    },
                                    "conversationStartTime": message_data["conversationStartTime"],
                                    "conversationEndTime": message_data["conversationEndTime"],
                                    "conversationid": message_data["conversationid"],
                                    "session_id": message_data["parameters"]["session_id"],
                                }
                            )

                            if not self.sio:
                                print("Error -------------- Socket.IO client is None")
                                return

                            if not self.sio.connected:
                                print("Error -------------- Socket.IO client is not connected")
                                return
        
                            try:
                                print(f"SummaryAgent ============= Sending Socket.IO message to {summary_topic}")
                                print(f"Message content: {summary_message}")
                                self.sio.emit(
                                    "celeryMessage",
                                    {
                                        "payloadString": summary_message,
                                        "destinationName": summary_topic,
                                        "conversationid": message_data["conversationid"],
                                    },
                                    callback=lambda *args: print("Message sent successfully:", args),
                                )
                                print("SummaryAgent ============= Socket.IO message sent")
                            except Exception as e:
                                print(f"Error sending Socket.IO message: {str(e)}")
                                print(f"Error type: {type(e)}")
                                print(f"Error traceback: {traceback.format_exc()}")
                else:
                    print(f"SummaryAgent ============= client_id is NOT good, please check the message data \n")

        #--------# catch exception
        except Exception as e:
            print(f"Unexpected error message: {str(e)}")
            print(f"Unexpected error type: {type(e)}")

        #--------# the return result is stored in the celery backend
        return result
    
