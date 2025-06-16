import random
import string
import subprocess
import celery
import sys
import os

# Define a function to generate a random string of characters
def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# Prefix for the worker name
worker_name_prefix = "agent-"

# # Generate a random suffix for the worker name
# random_suffix = generate_random_string(8)

# # Concatenate the prefix and random suffix to create the worker name
# worker_name = worker_name_prefix + random_suffix

# Generate a unique worker name with a random suffix
worker_name = f"{worker_name_prefix}{generate_random_string(8)}"
command = [
    "celery", "-A", "celery_worker", "worker",
    "--loglevel=INFO",
    "--pool=eventlet",
    "--concurrency=20",
    "--max-tasks-per-child=1000",
    "--max-memory-per-child=200000",  # 明确为 200MB
    "--prefetch-multiplier=1",
    "--without-gossip",
    "--without-mingle",
    "--without-heartbeat",
    f"--hostname={worker_name}"
]

command = [
    "celery", "-A", "celery_worker", "worker",
    "--loglevel=INFO",
    "--pool=eventlet",
    "--concurrency=20",
    "--max-tasks-per-child=1000",
    "--max-memory-per-child=200000",  # 明确为 200MB
    "--prefetch-multiplier=1",
    "--without-gossip",
    "--without-mingle",
    "--without-heartbeat",
    f"--hostname={worker_name}"
]

# Start the Celery worker with the generated hostname
process = subprocess.Popen(
    #f"celery -A celery_worker worker --loglevel=INFO --pool=solo --concurrency=2 --max-tasks-per-child=1000 --max-memory-per-child=512000 --hostname={worker_name_prefix + generate_random_string(8)} 2>&1",
    command,
    shell=True,
    stdout=subprocess.PIPE,  # 捕获标准输出
    stderr=subprocess.STDOUT,  # 将标准错误重定向到标准输出
    universal_newlines=True,  # 使用文本模式
    bufsize=1,  # 行缓冲
    encoding='utf-8',  # 使用 UTF-8 编码
    errors='replace'  # 替换无法解码的字符
)

# 实时读取并输出日志
def log_output(process):
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"[{worker_name}]line.strip()")
            sys.stdout.flush()  # 确保立即输出

# 启动日志输出线程
import threading
log_thread = threading.Thread(target=log_output, args=(process,))
log_thread.daemon = True
log_thread.start()

# 保持主进程运行
try:
    process.wait()
except KeyboardInterrupt:
    process.terminate()
    process.wait()
