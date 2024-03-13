FROM python:3.7-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up the working directory
WORKDIR /app
COPY . .

# Expose the port and run the app
EXPOSE 8080
CMD ["streamlit", "run", "attendance.py", "--server.port", "8080", "--server.enableCORS", "false"]
