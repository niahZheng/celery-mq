from kombu import Exchange, Queue
from celery import Celery
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 定义交换器
default_exchange = Exchange(
    'default',
    type='direct',
    auto_delete=True
)

high_priority_exchange = Exchange(
    'high_priority',
    type='direct',
    auto_delete=True
)

# 定义队列
task_queues = (
    Queue('high_priority', high_priority_exchange, routing_key='high_priority'),
    Queue('default', default_exchange, routing_key='default'),
)

# Celery 配置
broker_url = os.getenv("AAN_CELERY_BROKER_URI", "amqp://rxadmin:rxadmin321@20.39.130.141:5672")

# 基本配置
broker_connection_retry_on_startup = True
broker_connection_max_retries = 10
broker_connection_timeout = 30

# 任务配置
task_queues = task_queues
task_default_queue = 'default'
task_default_exchange = 'default'
task_default_routing_key = 'default'

# 性能配置
worker_prefetch_multiplier = 1  # 限制每个worker预取的任务数
worker_max_tasks_per_child = 1000  # 每个worker处理的最大任务数
worker_max_memory_per_child = 512000  # 每个worker的最大内存使用量（KB）

# 路由配置
task_routes = {
    'aan_extensions.TranscriptionAgent.tasks.process_transcript': {'queue': 'high_priority'},
    'aan_extensions.NextBestActionAgent.tasks.process_transcript': {'queue': 'high_priority'},
    'aan_extensions.SummaryAgent.tasks.process_transcript': {'queue': 'high_priority'},
    'aan_extensions.CacheAgent.tasks.process_transcript': {'queue': 'default'},
    'aan_extensions.DispatcherAgent.tasks.process_transcript': {'queue': 'default'},
} 