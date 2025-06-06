import pika
import sys

def test_amqp_connection(url):
    try:
        # 创建连接参数
        parameters = pika.URLParameters(url)
        
        # 尝试建立连接
        connection = pika.BlockingConnection(parameters)
        
        # 如果成功连接，打印成功信息
        print("✅ 连接成功！")
        print(f"已连接到: {url}")
        
        # 关闭连接
        connection.close()
        return True
        
    except pika.exceptions.AMQPConnectionError as e:
        print("❌ 连接失败！")
        print(f"错误信息: {str(e)}")
        return False
    except Exception as e:
        print("❌ 发生未知错误！")
        print(f"错误信息: {str(e)}")
        return False

if __name__ == "__main__":
    # AMQP URL
    amqp_url = "amqp://rxadmin:rxadmin321@20.39.130.141:5672"
    
    # 测试连接
    test_amqp_connection(amqp_url) 