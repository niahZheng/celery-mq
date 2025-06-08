import random
import string
import subprocess
import celery

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

# Azure App Service environment configuration
# 使用 2>&1 将 stderr 重定向到 stdout，这样所有日志都会显示在 Log Stream 中
subprocess.Popen(
    f"celery -A celery_worker worker "
    f"--loglevel=INFO "
    f"--pool=solo "
    f"--max-tasks-per-child=1000 "
    f"--max-memory-per-child=512000 "
    f"--hostname={worker_name_prefix + generate_random_string(8)} "
    f"2>&1",  # 关键修改：重定向 stderr 到 stdout
    shell=True
)
