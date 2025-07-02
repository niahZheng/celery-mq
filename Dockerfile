FROM python:3.12-slim

# Install system dependencies (add more if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

# Set working directory
WORKDIR /usr/src/app

# Copy dependency file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Change file permissions
RUN chown -R celeryuser:celeryuser /usr/src/app

# Switch to non-root user
USER celeryuser

# Expose commonly used port (adjust if needed)
EXPOSE 3000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default startup command (adjust as needed)
CMD ["python", "swarmLauncher.py"]

