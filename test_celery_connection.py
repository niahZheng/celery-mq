from celery import Celery
import os

def test_celery_connection():
    try:
        # 创建 Celery 实例
        app = Celery(
            "test_app",
            broker="amqp://rxadmin:rxadmin321@20.39.130.141:5672"
        )
        
        # 获取连接
        with app.connection() as conn:
            # 如果成功连接，打印成功信息
            print("✅ 连接成功！")
            print(f"已连接到: amqp://rxadmin:rxadmin321@20.39.130.141:5672")
            return True
            
    except Exception as e:
        print("❌ 连接失败！")
        print(f"错误信息: {str(e)}")
        return False

if __name__ == "__main__":
    test_celery_connection() 