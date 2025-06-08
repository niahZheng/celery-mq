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

# Windows development environment (commented out)
subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --pool=solo --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)

# Azure Premium environment configuration
# Using prefork pool with optimized settings for Premium tier
# subprocess.Popen(
#     f"celery -A celery_worker worker "
#     f"--loglevel=INFO "
#     f"--concurrency=8 "  # Premium tier can handle more concurrent workers
#     f"--max-tasks-per-child=1000 "  # Restart worker after 1000 tasks to prevent memory leaks
#     f"--max-memory-per-child=512000 "  # Restart worker if memory exceeds 512MB
#     f"--hostname={worker_name_prefix + generate_random_string(8)}",
#     shell=True
# )
