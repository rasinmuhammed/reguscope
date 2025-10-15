FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements-ragops.txt .
RUN pip install --no-cache-dir -r requirements-ragops.txt

# Copy ingestion script
COPY backend/ingestion.py .
COPY backend/data/ ./data/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run ingestion
CMD ["python", "ingestion.py"]
