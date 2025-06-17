import random
import string
import subprocess
import celery
import sys
import os
import threading

# Define a function to generate a random string of characters
def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# Prefix for the worker name
worker_name_prefix = "agent-"

# Generate a random suffix for the worker name
random_suffix = generate_random_string(8)

# Concatenate the prefix and random suffix to create the worker name
worker_name = worker_name_prefix + random_suffix

# Start the Celery worker with queue configuration
worker_process = subprocess.Popen(
    f"celery -A celery_worker worker --loglevel=DEBUG --pool=solo --concurrency=4 -Q celery,hipri --max-tasks-per-child=1000 --max-memory-per-child=512000 --hostname={worker_name_prefix + generate_random_string(8)} 2>&1",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1,
    encoding='utf-8',
    errors='replace'
)

# Start Flower monitoring
flower_process = subprocess.Popen(
    "celery -A celery_worker flower --port=6006",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1,
    encoding='utf-8',
    errors='replace'
)

# 实时读取并输出日志
def log_output(process, prefix=""):
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"{prefix}{line.strip()}")
            sys.stdout.flush()  # 确保立即输出

# 启动日志输出线程
worker_log_thread = threading.Thread(target=log_output, args=(worker_process, "[Worker] "))
worker_log_thread.daemon = True
worker_log_thread.start()

flower_log_thread = threading.Thread(target=log_output, args=(flower_process, "[Flower] "))
flower_log_thread.daemon = True
flower_log_thread.start()

# 保持主进程运行
try:
    worker_process.wait()
    flower_process.wait()
except KeyboardInterrupt:
    worker_process.terminate()
    flower_process.terminate()
    worker_process.wait()
    flower_process.wait()
