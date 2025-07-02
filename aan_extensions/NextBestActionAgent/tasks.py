from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
import logging
import json
import re
from .nba import generate_next_best_action, check_action_completion, create_session, get_quick_actions

from opentelemetry import trace
from opentelemetry.trace import SpanKind

logger = logging.getLogger(__name__)

# 存储 actions 的字典
actions = {}

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

def update_action_status(session_id, action_id, status):
    if session_id in actions:
        for action in actions[session_id]:
            if action['action_id'] == action_id:
                action['status'] = status
                break

def publish_action(client, session_id, action, action_id, options=[]):
    if action == "noresponse":
        return
    topic = f"agent-assist/{session_id}/nextbestaction"
    message = json.dumps({
        "type": "new_action",
        "parameters": {
            "text": action,
            "action_id": action_id,
            "options": options 
        }
    })

    logging.info(f"Publishing action to {topic}: {message}")
    result = client.publish(topic, message)
    logging.info(f"Publish result: {result.rc}")

def get_or_create_idv_data(self, client_id):
    """获取或创建IDV数据"""
    idv_object = self.redis_client.get(client_id + '_idv')
    if idv_object:
        idv_data = json.loads(idv_object)
        return {
            'identified': idv_data.get('identified', 'unidentified'),
            'verified': idv_data.get('verified', 'unverified'),
            'intentType': idv_data.get('intentType'),
            'pre_intent': idv_data.get('pre_intent'),
            'message': idv_data.get('message'),
            'data': idv_data
        }
    else:
        # 如果不存在，创建默认的idv对象
        idv_data = {
            'identified': 'unidentified',
            'verified': 'unverified',
            'conversationid': client_id,
            'intentType': None,
            'pre_intent': None,
            'message': None
        }
        self.redis_client.set(client_id + '_idv', json.dumps(idv_data))
        return {
            'identified': 'unidentified',
            'verified': 'unverified',
            'intentType': None,
            'pre_intent': None,
            'message': None,
            'data': idv_data
        }

def should_get_quick_actions(pre_intent, identified_flag, verified_flag):
    """判断是否应该获取快速操作"""
    return (
        (pre_intent == "identify" and identified_flag == "failed") or
        (pre_intent == "verify" and identified_flag == "identified" and 
         (verified_flag == "failed" or verified_flag == "verified")) or
        (pre_intent == "OrderStatus" or pre_intent is None)
    )

def emit_celery_message(self, client_id, quickActions, intentType, message_data):
    """发送Celery消息给前端UI"""
    celeryMessage = json.dumps({
        "type": "new_action",
        "parameters": {
            "text": None,
            "action_id": None,
            "options": None,
            "quickActions": quickActions,
            "intentType": intentType,
        },
        "conversationid": message_data['conversationid']
    })
    
    logging.info(f"new_action celeryMessage: {celeryMessage}")
    celeryTopic = f"agent-assist/{client_id}/nextbestaction"
    
    self.sio.emit(
        "celeryMessage",
        {
            "payloadString": celeryMessage,
            "destinationName": celeryTopic,
            'conversationid': message_data['conversationid']
        },
        callback=lambda *args: print("Message sent successfully:", args)
    )
    print(f"new quick actions->ragResponse->emit_socketio: {celeryMessage}")

def handle_identify_intent(self, client_id, wxoResponse, idv_data):
    """处理identify意图，并更新idv_data"""
    idv_data['identified'] = "identified"
    idv_data['intentType'] = wxoResponse.get('intentType')
    idv_data['pre_intent'] = "identify"
    idv_data['message'] = wxoResponse.get('message')
    self.redis_client.set(client_id + '_idv', json.dumps(idv_data))

# WORK IN PROGRESS - PLACEHOLDER
# this runs after cache agent, which means the transcriptions are there
@app.task(base=BaseTask.BaseTask, bind=True)
def process_transcript(self, topic, message):
    with trace.get_tracer(__name__).start_as_current_span(
        "process_transcript", kind=SpanKind.PRODUCER
    ) as span:
        result = topic + "---" + message

        print(
            f"NextBestAction {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}"
        )
        print(self.sio)
        
        try:
            client_id = self.extract_client_id(topic)
            print(f"initial client_id--------NBA: {client_id}")
            
            with trace.get_tracer(__name__).start_as_current_span("redis_op"):
                message_data = json.loads(message)
                event_type = self.extract_event(topic)
                session_id_pattern = re.compile(r"agent-assist/([^/]+)/.*")
                match = session_id_pattern.match(topic)

                if topic == "agent-assist/session" and message_data['type'] == 'session_started':
                    # create wa session and store in redis
                    # create actions list and store in redis
                    # actually you can't have empty lists in redis
                    # self.redis_client.rpush(client_id + '_actions', json.dumps())
                    # client_id = message_data['parameters']['session_id']
                    # wa_session_id = create_session()
                    # wa_session_id = "1234567890"
                    # print(f"client_id: {client_id} - wa_session_id {wa_session_id}")
                    # self.redis_client.set(client_id + '_nba_wa', wa_session_id)
                    pass
                elif match and message_data['type'] == 'session_ended':
                    # self.redis_client.delete(client_id + '_identification')
                    # self.redis_client.delete(client_id + '_verified')
                    # self.redis_client.delete(client_id + '_quick_actions')
                    # self.redis_client.delete(client_id)
                    pass
                elif event_type == 'transcription':
                    snum = 0
                    # external - GNBA
                    # internal - check completion
                    #last_transcript = json.loads(self.redis_client.lindex(client_id, -1))
                    message_data = json.loads(message)
                    last_transcript = message_data["parameters"]

                    # wa_session = self.redis_client.get(client_id + '_nba_wa')
                    # print(f"client_id: {client_id} - redis_wa_session_id {wa_session}")
                    print(f"last_transcript: {last_transcript}")
                    
                    if last_transcript['source'] == 'external':
                        #check if there is an active action
                        # nba_length = self.redis_client.llen(client_id + '_nba_actions')
                        # print(f"nba_length {nba_length}")
                        # if nba_length == 0:
                        transcripts_history = self.redis_client.lrange(client_id, 0, -1)
                        print(f"transcripts_history: {transcripts_history}")
                        
                        # 从 redis 获取或创建IDV数据
                        idv_info = get_or_create_idv_data(self, client_id)
                        identified_flag = idv_info['identified']
                        verified_flag = idv_info['verified']
                        intentType = idv_info['intentType']
                        pre_intent = idv_info['pre_intent']
                        idv_message = idv_info['message']
                        idv_data = idv_info['data']

                        # 判断是否需要获取快速操作
                        if should_get_quick_actions(pre_intent, identified_flag, verified_flag):
                            # wxoResponse = get_quick_actions(
                            #     client_id, identified_flag, verified_flag, 
                            #     intentType, pre_intent, transcripts_history, idv_message
                            # )
                            wxoResponse = {
                                "conversationId": client_id,
                                "intentType": "OrderStatus", ## identify/verify/None/OrderStatus...
                                "quickActions": ["check_order"],
                                "message":"guest: I want to check my order detals"
                            }
                        else:
                            logging.info(f"Waiting for guest to identify or verify, no quick actions")
                            wxoResponse = None

                        if wxoResponse:
                            logging.info(f"WXO_Response: {wxoResponse}")
                            intentType = wxoResponse.get('intentType')
                            quickActions = wxoResponse.get('quickActions')
                            pre_intent = intentType
                            
                            # 首次遇到 identify 时，将 identified 设置为 identified
                            if intentType == "identify":
                                handle_identify_intent(self, client_id, wxoResponse, idv_data)
                        else:
                            quickActions = None                        
                        
                        if quickActions:
                            # maybe the action IDs can be random
                            # or they should be defined on the WA skill itself
                            # action_id = self.redis_client.llen(client_id + '_nba_actions') or 0
                            # action_payload = {"action_id": action_id, "action": action, "status": "pending"}
                            self.redis_client.rpush(client_id + '_quick_actions', json.dumps(quickActions))
                            # emit messages to UI
                            #publish_action(client, client_id, action, action_id,options)
                            # celeryMessage = json.dumps({
                            #     "type": "new_action",
                            #     "parameters": {
                            #         "text": action,
                            #         "action_id": action_id,
                            #         "options": options
                            #     }
                            # })                            
                            celeryMessage = json.dumps({
                                "type": "new_action",
                                "parameters": {
                                    "text": f"=== {snum} === This is a quick action demo",
                                    "action_id": "action789",
                                    "options": ["option1", "option2"],
                                    "quickActions": quickActions,
                                    "intentType": intentType,
                                },
                                "conversationid": message_data['conversationid']
                            })
                            logging.info(f"new_action celeryMessage: {celeryMessage}")
                            celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                            self.sio.emit(
                                    "celeryMessage",
                                    {
                                        "payloadString": celeryMessage,
                                        "destinationName": celeryTopic,
                                        'conversationid': message_data['conversationid']
                                    },
                                    callback=lambda *args: print("Message sent successfully:", args)
                                    
                            )
                            print(f"new quick actions->ragResponse->emit_socketio: {celeryMessage}")
                    elif last_transcript['source'] == 'internal':
                        pass
                        #actions = json.loads(self.redis_client.lindex(client_id + '_nba_actions', -1) or "[]")
                        # actions = self.redis_client.lrange(client_id + '_nba_actions', 0, -1) or []
                        # actions is array of:
                        # {"action_id": action_id, "action": action, "status": "pending"}
                        # completed_action_ids_idxs, completed_actions_ids = check_action_completion(client_id, last_transcript["text"], actions)
                        
                        # 伪造已完成的动作 ID
                        # completed_actions_ids = ["action789", "action790"]  # 使用与之前发送的 action_id 匹配的值
                        # print(f"Mock completed actions: {completed_actions_ids}")

                        # first we emit all the action IDs that are completed for the frontend (fast!)
                        # for action_id in completed_actions_ids:
                        #     celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                        #     celeryMessage = json.dumps({
                        #         "type": "completed_action",
                        #         "parameters": {
                        #             "action_id": action_id
                        #         },
                        #         "conversationid": message_data['conversationid']
                        #     })

                        #     emit_data = {
                        #         'payloadString': celeryMessage,
                        #         'destinationName': celeryTopic
                        #     }
                            
                        #     # 如果存在 conversationid，则添加到发送数据中
                        #     if 'conversationid' in message_data:
                        #         emit_data['conversationid'] = message_data['conversationid']
                            
                        #     self.sio.emit('celeryMessage', emit_data,
                        #                 callback=lambda *args: print("Message sent successfully:", args))
                        # then we update those action indexs on redis
                        #self.redis_client.ltrim(client_id + '_nba_actions', 99 , 0) # we delete it

                        ## TODO we need to finish the action on assistant and then reset the action object

                        # for action_id_idx in completed_action_ids_idxs:
                        #     existing_action = action[action_id_idx]
                        #     existing_action['status'] =  "completed"
                        #     self.redis_client.lset(client_id + '_nba_actions', action_id_idx, json.dumps(existing_action))                          
                #  `agent-assist/${session_id}/nextbestaction-completion`
                elif match and message_data['type'] == 'manual_completion':
                    # agent clicked on UI
                    wa_session = self.redis_client.get(client_id + '_nba_wa')
                    # action, options = generate_next_best_action(client_id, message_data['parameters']['text'],wa_session,True) 
                    action, options = "Do something", ["option1", "option2"]
                    logging.info(f"Manual completion - Action type: {type(action)}, Action value: '{action}'")
                    if action:
                            action_id = self.redis_client.llen(client_id + '_nba_actions') or 0
                            action_payload = {"action_id": action_id, "action": action, "status": "pending"}
                            self.redis_client.rpush(client_id + '_nba_actions', json.dumps(action_payload) )
                            # emit messages to UI
                            #publish_action(client, client_id, action, action_id,options)
                            celeryMessage = json.dumps({
                                "type": "new_action",
                                "parameters": {
                                    "text": action,
                                    "action_id": action_id,
                                    "options": options 
                                }
                            })
                            celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                            self.sio.emit(
                                    "celeryMessage",
                                    {
                                        "payloadString": celeryMessage,
                                        "destinationName": celeryTopic,
                                        'conversationid': message_data['conversationid']
                                    },
                                    callback=lambda *args: print("Message sent successfully:", args)
                                    
                            )
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result
