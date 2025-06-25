from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
from opentelemetry import trace
from opentelemetry.trace import SpanKind
import traceback
from .summary import summarize
import logging
import json
from datetime import datetime

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
            client_id = 'none' # it is conversation id from Geneysis UI 
            if "conversationid" in message_data:
                client_id = message_data["conversationid"]
            else:
                if "parameters" in message_data and "conversationid" in message_data["parameters"]:
                    client_id = message_data['parameters']["conversationid"]
                    print("'conversationid' in 'parameters' , it is expected=====================client_id:"+client_id)
                else:
                    print("'conversationid' does not exist in 'parameters', unexpected=====================message:"+message)
                    return


            print(f"SummaryAgent ============= client_id: {client_id} \n")
            print( "SummaryAgent ============= message start ============= \n")
            print(json.dumps(message_data, indent=2, ensure_ascii=False))
            print(" SummaryAgent ============= message end ============= \n")

            with trace.get_tracer(__name__).start_as_current_span("redis_op"):
                
                if isinstance(client_id, str) and len(client_id) > 5: # must have client_id 

                    ###=============check type to see if we need to do summarization....start
                    message_type = message_data["type"]
                    if message_type == "session_ended":
                        # message_type == "session_ended" or message_type == "session_manual":
                        # session_manual is combined into session_ended, with conversationEndTime is null 
                        pass # yes, we should do summary here 
                    else:
                        print("SummaryAgent ============= there is no need to do summary for type: ", message_type)
                        return

                    ###=============check type to see if we need to do summarization....end 
                    
                    try:
                        transcripts_obj=[]
                        transcription_text=''
                        start_time=str(datetime.now())
                        end_time=str(datetime.now())

                        #-----------get start time.......start
                        turns_counter = self.redis_client.llen(client_id+"_session_started") or 0
                        print(f"Turns counter session_started: {turns_counter}")
                        if turns_counter > 0:
                            start_body = self.redis_client.lindex(client_id+"_session_started", 0)
                            start_info = json.loads(start_body)
                            start_time = start_info["conversationStartTime"]
                        #-----------get start time.......end
                        
                        #-----------get chat history.......start
                        turns_counter = self.redis_client.llen(client_id) or 0
                        print(f"Turns counter transcription: {turns_counter}")
                        
                        # if (turns_counter != 0) and (turns_counter % 2 == 0):
                        if turns_counter != 0:
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
                            print("SummaryAgent ============= input list 111:", transcripts_obj)
                            print("SummaryAgent ============= input for LLM 111:" + transcription_text)
                        #-----------get chat history.......end

                        print("SummaryAgent ============= input list 222:", transcripts_obj)
                        print("SummaryAgent ============= input for LLM 222:" + transcription_text)

                        #-----------get end time.......start
                        if "parameters" in message_data and "conversationEndTime" in message_data["parameters"]:
                            end_time = message_data["parameters"]["conversationEndTime"]
                        else:
                            end_time = None
                        #-----------get end time.......end

                        with trace.get_tracer(__name__).start_as_current_span(
                            "summarize"
                        ):
                            print("SummaryAgent ============= input list:", transcripts_obj)
                            print("SummaryAgent ============= input for LLM:" + transcription_text)
                            new_summary = summarize(transcription_text) # the real summary from LLM 
                            new_summary_json = json.loads(new_summary) 
                            if "ata" not in new_summary_json:
                                new_summary_json["ata"]=[]

                            # new_summary = "*********This is a test summary This is a test summary This is a test summary This is a test summary"  
                            # new_summary = "*********This is a test summary:\nVerified customer’s identity and booking details.\nChecked availability for the new date (September 11th).\nConfirmed seat preference (Window seat).\nNoted unchanged meal preference (Standard meal).\nUpdated booking with new flight details.\nConfirmed booking update via email."

                            if new_summary:
                                summary_topic = f"agent-assist/{client_id}/summarization"
                                summary_body = {
                                    "type": "summary",
                                    "parameters": {
                                        "conversationStartTime": start_time,
                                        "conversationid": client_id,
                                        "text": new_summary_json,
                                     },
                                    "conversationid": client_id,
                                } 
                                if end_time == None:
                                    # UI click to trigger this, no end time
                                    pass
                                else:
                                    # chat ends normally with end time 
                                    summary_body["conversationEndTime"] = end_time

                                #final string 
                                summary_message = json.dumps(summary_body)

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
                                            "conversationid": client_id,
                                        },
                                        callback=lambda *args: print("Message sent successfully:", args),
                                    )
                                    print("SummaryAgent ============= Socket.IO message sent")
                                except Exception as e:
                                    print(f"Error sending Socket.IO message: {str(e)}")
                                    print(f"Error type: {type(e)}")
                                    print(f"Error traceback: {traceback.format_exc()}")

                    except Exception as e:
                        print(f"redis error message: {str(e)}")
                        print(f"redis error type: {type(e)}")
                    
                else:
                    print(f"SummaryAgent ============= client_id is NOT good, please check the message data \n")

        #--------# catch exception
        except Exception as e:
            print(f"Unexpected error message: {str(e)}")
            print(f"Unexpected error type: {type(e)}")

        #--------# the return result is stored in the celery backend
        return result
    
