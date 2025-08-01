# Use a base image with Python installed
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies including Redis
RUN apt-get update && \
    apt-get install -y net-tools python3-pip python3-setuptools redis-server ufw && \
    apt-get clean && \
    # Remove cache as recommended by SonarQube (docker:S6587)
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    # Install required Python dependencies first
    pip install flask uwsgi wheel

# Copy application requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Configure Redis
RUN echo "bind 0.0.0.0" >> /etc/redis/redis.conf && \
    echo "protected-mode yes" >> /etc/redis/redis.conf

ENV FLASK_APP=snaarf_app/server.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000
ENV FLASK_DEBUG=1
ENV FLASK_ENV=development

# Expose the ports the API and Redis will run on
# Note: Only expose Redis port 6379 in development
EXPOSE 8000 6379

# Allow all traffic on port 8000
RUN ufw allow 8000

# Start both Redis and Flask with password configuration
CMD ["sh", "-c", "\
    trap 'service redis-server stop; exit 0' TERM INT && \
    echo \"requirepass \\\"$REDIS_AUTH_PASSWORD\\\"\" >> /etc/redis/redis.conf && \
    service redis-server start && \
    netstat -tulpn && \
    flask run & \
    wait"]
