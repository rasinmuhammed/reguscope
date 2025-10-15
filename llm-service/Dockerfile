# Multi-stage build for optimized AMD64 deployment
FROM --platform=linux/amd64 ubuntu:22.04 AS builder

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for building llama.cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone llama.cpp
WORKDIR /app
RUN git clone https://github.com/ggerganov/llama.cpp.git
WORKDIR /app/llama.cpp

# Build with CMake (new build system)
RUN cmake -S . -B build -DLLAMA_CURL=ON && cmake --build build -j4

# ───────────────────────────────────────────────
# Runtime image (smaller)
FROM --platform=linux/amd64 ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python packages
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    google-cloud-storage==2.14.0 \
    requests==2.31.0

# Copy compiled binaries and any shared libraries
COPY --from=builder /app/llama.cpp/build/ /usr/local/
ENV LD_LIBRARY_PATH=/usr/local/bin:/usr/local/lib:$LD_LIBRARY_PATH



# Create model directory
RUN mkdir -p /models

# Copy app files
WORKDIR /app
COPY download_model.py /app/download_model.py
COPY start_server.sh /app/start_server.sh
RUN chmod +x /app/start_server.sh

# Expose port (Cloud Run expects $PORT)
ENV MODEL_BUCKET=reguscope-models
ENV MODEL_FILE=phi-3-mini-4k-instruct-q4.gguf
ENV HOST=0.0.0.0
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start the model server
CMD ["/app/start_server.sh"]