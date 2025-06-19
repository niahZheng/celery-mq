from celery import Celery
import json
import os
from dotenv import load_dotenv

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
    
    # 测试消息
    # test_message = {
    #     "type": "transcription",
    #     "parameters": {
    #         "source": "external",
    #         "text": "so you're um already extended you're a pretire it will end on august 24 so you need to give us a call back before always 20 fourth to give us a feedback if you i mean what happened to the product if it didn't something you know it give you the benefits such in it but let's say uh you love the product you like the product you don't need to give us a call back then it will be automatically uh you will be receiving a not a bottle for your subscription and uh set up a call i heard that you're not you know um sure uh you're dilling about the price which is $83 and 8 right okay so what i can do for you is aside from extending the your pre trial for another 15 days i'm also giving you my employee discount which is 20 percent of the scott so instead of paying $83 and 8 sets going to pay only $67.04 how about that",
    #         "seq": None,
    #         "timestamp": 68.66
    #     },
    #     "conversationid": "cda1ce9a-af1e-499d-897c-e82da9c165e5"
    # }
    test_message = {
        "type": "session_ended", 
        "conversationStartTime": "2025-06-19T03:37:21.533Z",
        "conversationEndTime": "2025-06-19T03:55:22.544Z",
        "conversationid": "cda1ce9a-af1e-499d-897c-e82da9c165e5",
        "parameters": {
            "session_id": "cda1ce9a-af1e-499d-897c-e82da9c165e5",
        },
    }
    
    # 转换为 JSON 字符串
    message_json = json.dumps(test_message)
    
    # 构建任务参数
    # topic = f"agent-assist/{test_message['conversationid']}/transcription"
    topic = f"agent-assist/{test_message['conversationid']}/session_ended"
    
    try:
        # 创建并发送任务
        # task = app.send_task(
        #     'aan_extensions.DispatcherAgent.tasks.process_transcript',
        #     args=[topic, message_json]
        # )
        task = app.send_task(
            'aan_extensions.SummaryAgent.tasks.process_transcript',
            args=[topic, message_json]
        )
        print(f"Task sent successfully with ID: {task.id}")
        print(f"Topic: {topic}")
        print(f"Message: {message_json}")
    except Exception as e:
        print(f"Error sending task: {e}")

if __name__ == '__main__':
    send_test_message() 