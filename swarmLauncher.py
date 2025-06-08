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

# Generate a random suffix for the worker name
random_suffix = generate_random_string(8)

# Concatenate the prefix and random suffix to create the worker name
worker_name = worker_name_prefix + random_suffix

# Start the Celery worker with the generated hostname
process = subprocess.Popen(
    f"celery -A celery_worker worker --loglevel=INFO --pool=solo --hostname={worker_name_prefix + generate_random_string(8)} 2>&1",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

# 实时读取并输出日志
def log_output(process):
    for line in iter(process.stdout.readline, ''):
        if line:
            print(line.strip())
            sys.stdout.flush()

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
