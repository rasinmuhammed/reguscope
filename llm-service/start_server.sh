#!/bin/bash
set -e

echo "=================================================="
echo "  ReguScope LLM Service (Phi-3 Mini Q4_K_M)"
echo "  Platform: AMD64 (Cloud Run)"
echo "=================================================="

# Download model from Cloud Storage
echo ""
echo "Step 1: Downloading model..."
python3 /app/download_model.py

# Verify model exists
MODEL_PATH="/models/${MODEL_FILE}"
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Error: Model file not found at $MODEL_PATH"
    exit 1
fi

echo ""
echo "Step 2: Starting llama.cpp server..."
echo "  Model: $MODEL_FILE"
echo "  Host: $HOST:$PORT"
echo "  Context Size: 4096 tokens"
echo "  Threads: 1 (Free Tier CPU)"
echo ""

# Start llama.cpp server using the binary from /usr/local/bin
# The binary is called 'llama-server' in newer versions
if command -v llama-server &> /dev/null; then
    LLAMA_BIN="llama-server"
elif command -v server &> /dev/null; then
    LLAMA_BIN="server"
else
    echo "❌ Error: llama.cpp server binary not found"
    exit 1
fi

echo "Using binary: $LLAMA_BIN"

# Start server with optimized settings for Cloud Run Free Tier
$LLAMA_BIN \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --ctx-size 4096 \
    --n-gpu-layers 0 \
    --threads 1 \
    --batch-size 512 \
    --ubatch-size 256 \
    --parallel 1 \
    --cont-batching \
    --metrics \
    --mlock \
    --verbose