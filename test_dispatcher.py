from celery import Celery
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import random
words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "indianberry", "jackfruit"]


# 加载环境变量
load_dotenv()

# 创建 Celery 应用
app = Celery(
    "test_dispatcher",
    broker=os.getenv("AAN_CELERY_BROKER_URI", "amqp://rxadmin:rxadmin321@20.39.130.141:5672"),
    include=[
        'aan_extensions.TranscriptionAgent.tasks', 
        'aan_extensions.DispatcherAgent.tasks',
        'aan_extensions.NextBestActionAgent.tasks',
        'aan_extensions.CacheAgent.tasks',
        'aan_extensions.SummaryAgent.tasks',
    ]
)

def send_test_message():
    print("\nSending test message to dispatcher...")

    test_id = "cda1ce9a-af1e-499d-897c-e82da9c165e5"
    test_type="transcription" # "session_started" "session_ended" "transcription"
    topic = f"agent-assist/{test_id}/{test_type}" 

    # 测试消息 "session_ended"
    # test_message = {
    #     "type": test_type, 
    #     "parameters": {
    #         "conversationid": test_id,
    #         "session_id": test_id,
    #         "conversationStartTime": "2025-06-19 03:37:21.533123",
    #         "conversationEndTime": None, # from UI 
    #         # "conversationEndTime": "2025-06-19 03:55:22.544123", # from Genesys
    #     },
    # }

    # 测试消息 "transcription"
    selected_words = random.sample(words, 3)
    test_message = {
        "type": test_type, 
        "parameters": {
            "conversationid": test_id,
            "session_id": test_id,
            "source": "external",
            "text": " ".join(selected_words) + " at "+ str(datetime.now()),
            "seq": None,
            "timestamp": datetime.now().timestamp(), #68.66, 
        },
    }

    # 测试消息 "session_started"
    # test_message = {
    #     "type": test_type, 
    #     "parameters": {
    #         "conversationid": test_id,
    #         "session_id": test_id,
    #         "conversationStartTime": "2025-06-19 03:37:21.533123",
    #         "conversationEndTime": None,
    #     },
    # }
    
    # 转换为 JSON 字符串
    message_json = json.dumps(test_message)
    
    try:
        task = app.send_task(
            'aan_extensions.DispatcherAgent.tasks.process_transcript',
            args=[topic, message_json]
        )
        print(f"Task sent successfully with ID: {task.id}")
        print(f"Topic: {topic}")
        print(f"Message: {message_json}")
    except Exception as e:
        print(f"Error sending task: {e}")

if __name__ == '__main__':
    send_test_message() 