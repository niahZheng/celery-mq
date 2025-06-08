import socketio
import os
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建 Socket.IO 客户端
sio = socketio.Client(
    logger=True, 
    engineio_logger=True,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1000
)

@sio.event
def connect():
    print('Connected to server')

@sio.event
def connect_error(data):
    print('Connection error:', data)

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.event
def celeryMessage(data):
    print('Received message:', data)

@sio.event
def error(data):
    print('Error:', data)

def main():
    try:
        # 连接到服务器
        server_url = "wss://rx-api-server-ddfrdga2exavdcbb.canadacentral-01.azurewebsites.net:443/socket.io"
        print(f"Connecting to {server_url}...")
        
        sio.connect(
            server_url,
            namespaces=['/celery'],
            wait_timeout=10,
            transports=['websocket']
        )
        
        # 发送测试消息
        test_message = {
            "payloadString": "Test message",
            "destinationName": "test/topic",
            "agent_id": "test_agent"
        }
        
        print("Sending test message...")
        sio.emit('celeryMessage', test_message, namespace='/celery')
        
        # 等待一段时间以接收响应
        print("Waiting for response...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Disconnecting...")
        sio.disconnect()

if __name__ == '__main__':
    main() 