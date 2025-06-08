from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
import logging

from celery import Celery
from celery.signals import worker_process_init, task_received, task_success, task_failure
from celery.utils.log import get_task_logger

from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
DISABLE_TRACING = os.getenv('DISABLE_TRACING', 'true') == 'true'
TRACING_COLLECTOR_ENDPOINT = os.getenv('TRACING_COLLECTOR_ENDPOINT', 'localhost')
TRACING_COLLECTOR_PORT = os.getenv('TRACING_COLLECTOR_PORT', '14268')

# 任务信号处理
@task_received.connect
def task_received_handler(sender=None, request=None, **kwargs):
    logger.info(f"任务已接收: {request.name} [{request.id}]")
    logger.info(f"任务参数: {request.args}")
    logger.info(f"任务关键字参数: {request.kwargs}")
    logger.info(f"任务队列: {request.delivery_info.get('routing_key', 'unknown')}")

@task_success.connect
def task_success_handler(sender=None, **kwargs):
    logger.info(f"任务执行成功: {sender.name} [{sender.request.id}]")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    logger.error(f"任务执行失败: {sender.name} [{sender.request.id}]")
    logger.error(f"错误信息: {exception}")

@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    global DISABLE_TRACING
    if not DISABLE_TRACING:
        try:
            CeleryInstrumentor().instrument()
            print("CeleryInstrumentation Enabled")
            trace.set_tracer_provider(TracerProvider())

            jaeger_exporter = JaegerExporter(
                collector_endpoint=f'http://{TRACING_COLLECTOR_ENDPOINT}:{TRACING_COLLECTOR_PORT}/api/traces?format=jaeger.thrift',
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            print("JaegerExporter Enabled")
        except Exception as e:
            print(f"Failed to initialize tracing: {e}")
            DISABLE_TRACING = True

app = Celery(
    "agent_assist_neo",
    broker=os.getenv("AAN_CELERY_BROKER_URI", "amqp://rxadmin:rxadmin321@20.39.130.141:5672"),
    # backend=os.getenv("AAN_CELERY_BACKEND_URI", f"rediss://default:{os.getenv('REDIS_PASSWORD')}@rx-redis.redis.cache.windows.net:6380/1"),
    include=['aan_extensions.TranscriptionAgent.tasks', 
             'aan_extensions.DispatcherAgent.tasks',
             'aan_extensions.NextBestActionAgent.tasks',
             'aan_extensions.CacheAgent.tasks',
             'aan_extensions.SummaryAgent.tasks',
             ]
)

# 添加新的配置设置
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_retry = True
app.conf.task_track_started = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_expires = 3600  # 1 hour
app.conf.worker_prefetch_multiplier = 1  # 确保任务被正确处理
app.conf.task_ignore_result = True  # 忽略任务结果，因为我们不需要存储结果

# Worker 配置
app.conf.worker_concurrency = os.getenv('CELERY_WORKER_CONCURRENCY', 4)  # 默认4个进程
app.conf.worker_max_tasks_per_child = 1000  # 每个进程处理1000个任务后重启
app.conf.worker_max_memory_per_child = 200000  # 每个进程最大内存使用量（KB）

# 配置队列
app.conf.task_queues = {
    'celery': {
        'exchange': 'celery',
        'routing_key': 'celery',
    },
    'dispatcher': {
        'exchange': 'dispatcher',
        'routing_key': 'dispatcher',
    },
    'transcription': {
        'exchange': 'transcription',
        'routing_key': 'transcription',
    }
}

# 配置路由规则
app.conf.task_routes = {
    'aan_extensions.DispatcherAgent.tasks.process_transcript': {'queue': 'celery'},  # 确保 process_transcript 任务接收 celery 队列的消息
    'aan_extensions.TranscriptionAgent.tasks.*': {'queue': 'transcription'},
    '*': {'queue': 'celery'},  # 默认路由到 celery 队列
}

# 确保 worker 监听所有队列
app.conf.task_default_queue = 'celery'
app.conf.task_default_exchange = 'celery'
app.conf.task_default_routing_key = 'celery'

if __name__ == '__main__':
    app.start()