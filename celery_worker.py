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

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DISABLE_TRACING = os.getenv('DISABLE_TRACING', False) == 'true'
TRACING_COLLECTOR_ENDPOINT = os.getenv('TRACING_COLLECTOR_ENDPOINT', 'jaeger')
TRACING_COLLECTOR_PORT = os.getenv('TRACING_COLLECTOR_PORT', '14268')

# 任务信号处理
@task_received.connect
def task_received_handler(sender=None, request=None, **kwargs):
    logger.info(f"Task received: {request.name} [{request.id}]")
    logger.debug(f"Task args: {request.args}")
    logger.debug(f"Task kwargs: {request.kwargs}")

@task_success.connect
def task_success_handler(sender=None, **kwargs):
    logger.info(f"Task succeeded: {sender.name} [{sender.request.id}]")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    logger.error(f"Task failed: {sender.name} [{sender.request.id}]")
    logger.error(f"Exception: {exception}")

@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    if os.getenv("TELEMETRY", ''):
        CeleryInstrumentor().instrument()
        logger.info("CeleryInstrumentation Enabled")
    trace.set_tracer_provider(TracerProvider())

    if DISABLE_TRACING:
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    else:
        logger.info("JaegerExporter Enabled")
        jaeger_exporter = JaegerExporter(
            collector_endpoint=f'http://{TRACING_COLLECTOR_ENDPOINT}:{TRACING_COLLECTOR_PORT}/api/traces?format=jaeger.thrift',
        )
        span_processor = BatchSpanProcessor(jaeger_exporter)

    trace.get_tracer_provider().add_span_processor(span_processor)

app = Celery(
    "agent_assist_neo",
    broker=os.getenv("AAN_CELERY_BROKER_URI", "amqp://rxadmin:rxadmin321@20.39.130.141:5672"),
    backend=os.getenv("AAN_CELERY_BACKEND_URI", "redis://localhost:6379/1"),
    include=['aan_extensions.TranscriptionAgent.tasks', 
             'aan_extensions.DispatcherAgent.tasks',
             'aan_extensions.NextBestActionAgent.tasks',
             'aan_extensions.CacheAgent.tasks',
             'aan_extensions.SummaryAgent.tasks',
             ]
)

# 添加新的配置设置
app.conf.broker_connection_retry_on_startup = True
app.conf.task_track_started = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_expires = 3600  # 1 hour
app.conf.worker_prefetch_multiplier = 1  # 确保任务被正确处理

# 配置队列
app.conf.task_queues = {
    'dispatcher': {
        'exchange': 'dispatcher',
        'routing_key': 'dispatcher',
    },
    'transcription': {
        'exchange': 'transcription',
        'routing_key': 'transcription',
    },
    'nextbestaction': {
        'exchange': 'nextbestaction',
        'routing_key': 'nextbestaction',
    },
    'cache': {
        'exchange': 'cache',
        'routing_key': 'cache',
    },
    'summary': {
        'exchange': 'summary',
        'routing_key': 'summary',
    },
}

# 配置路由规则
app.conf.task_routes = {
    'aan_extensions.DispatcherAgent.tasks.*': {'queue': 'dispatcher'},
    'aan_extensions.TranscriptionAgent.tasks.*': {'queue': 'transcription'},
    'aan_extensions.NextBestActionAgent.tasks.*': {'queue': 'nextbestaction'},
    'aan_extensions.CacheAgent.tasks.*': {'queue': 'cache'},
    'aan_extensions.SummaryAgent.tasks.*': {'queue': 'summary'},
}

if __name__ == '__main__':
    app.start()