FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iptables \
    ip6tables \
    iproute2 \
    curl \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/sentinel-v

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py database.py monitors.py actions.py dashboard.py .

# Create templates directory
RUN mkdir -p templates

# Setup non-root user (optional, but recommended)
RUN useradd -m -s /bin/bash sentinel || true

# Expose dashboard port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=5000

# Run the application
CMD ["python", "main.py"]
