# gunicorn.conf.py
# Gunicorn configuration for Render deployment

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Request handling
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# Application
preload_app = True

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "hireqa-api"

# Worker recycling
max_worker_memory = 200000  # 200MB per worker
worker_tmp_dir = "/dev/shm"

# Graceful shutdown
graceful_timeout = 30
