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
        server_url = "https://rx-api-server-ddfrdga2exavdcbb.canadacentral-01.azurewebsites.net:443/socket.io"
        print(f"Connecting to {server_url}...")
        
        sio.connect(
            server_url,
            namespaces=['/celery'],
            wait_timeout=10,
            transports=['websocket']
        )
        
        print("Connected! Listening for messages...")
        
        # 保持程序运行，持续监听消息
        while True:
            try:
                time.sleep(1)  # 避免 CPU 使用率过高
            except KeyboardInterrupt:
                print("\nStopping listener...")
                break
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Disconnecting...")
        sio.disconnect()

if __name__ == '__main__':
    main() 