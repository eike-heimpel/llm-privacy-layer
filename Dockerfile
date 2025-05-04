FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with specific order for better compatibility
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy the application
COPY . .

# Expose the port the app runs on
EXPOSE 8010

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"] 