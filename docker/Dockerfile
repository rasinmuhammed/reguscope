FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY backend/ ./backend/

# Expose port
EXPOSE 8080

# Set environment variable for Cloud Run
ENV PORT=8080

# Start FastAPI
CMD uvicorn main:app --host 0.0.0.0 --port $PORT