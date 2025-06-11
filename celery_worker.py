from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
import logging

from celery import Celery
from celery.signals import worker_process_init

from dotenv import load_dotenv
import os

# 导入 Celery 配置
from celery_config import *

logger = logging.getLogger(__name__)

DISABLE_TRACING = True  # 设置为 True 来禁用追踪
TRACING_COLLECTOR_ENDPOINT = os.getenv('TRACING_COLLECTOR_ENDPOINT', 'jaeger')
TRACING_COLLECTOR_PORT = os.getenv('TRACING_COLLECTOR_PORT', '14268')


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    if not DISABLE_TRACING and os.getenv("TELEMETRY", ''):
        CeleryInstrumentor().instrument()
        print("CeleryInstrumentation Enabled")
        trace.set_tracer_provider(TracerProvider())

        print("JaegerExporter Enabled")
        jaeger_exporter = JaegerExporter(
            collector_endpoint=f'http://{TRACING_COLLECTOR_ENDPOINT}:{TRACING_COLLECTOR_PORT}/api/traces?format=jaeger.thrift',
        )
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
    else:
        print("Tracing is disabled")

app = Celery(
    "agent_assist_neo",
    broker=os.getenv("AAN_CELERY_BROKER_URI", "amqp://rxadmin:rxadmin321@20.39.130.141:5672"),
    # backend=os.getenv("AAN_CELERY_BACKEND_URI", "redis://localhost:6379/1"),
    include=['aan_extensions.TranscriptionAgent.tasks', 
             'aan_extensions.DispatcherAgent.tasks',
             'aan_extensions.NextBestActionAgent.tasks',
             'aan_extensions.CacheAgent.tasks',
             'aan_extensions.SummaryAgent.tasks',
             ]
)

if __name__ == '__main__':
    app.start()