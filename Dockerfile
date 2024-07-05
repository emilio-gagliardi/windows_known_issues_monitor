# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    netcat-openbsd \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# COPY app/ ./app
# COPY wait-for-it.sh start.sh ./
COPY . .
RUN playwright install
RUN playwright install-deps
# Set correct permissions
# RUN chmod +x /app/wait-for-it.sh /app/start.sh
# Expose the ports the app runs on (FastAPI and Streamlit)
EXPOSE 80 8000 8501

# Command to run the application (we'll use a startup script)
# CMD ["sh", "start.sh"]
CMD ["tail", "-f", "/dev/null"]