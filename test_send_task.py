from celery_worker import app
import json
import time

def test_send_task():
    # 准备测试数据
    topic = "test/topic/event"
    message = json.dumps({
        "agent_id": "test_agent_001",
        "content": "This is a test message",
        "timestamp": "2025-06-06T17:30:00Z"
    })
    
    # 发送任务到 TranscriptionAgent
    result = app.send_task(
        'aan_extensions.TranscriptionAgent.tasks.process_transcript',
        args=[topic, message],
        queue='transcription'
    )
    
    print(f"✅ 任务已发送！")
    print(f"任务ID: {result.id}")
    print(f"Topic: {topic}")
    print(f"Message: {message}")
    
    # 等待并检查任务状态
    print("\n等待任务执行...")
    for _ in range(10):  # 最多等待10秒
        state = result.state
        print(f"当前任务状态: {state}")
        if state == 'SUCCESS':
            print("任务执行成功！")
            print(f"结果: {result.get()}")
            break
        elif state == 'FAILURE':
            print("任务执行失败！")
            print(f"错误信息: {result.result}")
            break
        time.sleep(1)
    else:
        print("任务执行超时！")
    
    return result

if __name__ == "__main__":
    test_send_task() 