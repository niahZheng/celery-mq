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

# Start the Celery worker with the generated hostname
subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)
subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)
subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)
# subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)
# subprocess.Popen(f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name_prefix + generate_random_string(8)}", shell=True)
