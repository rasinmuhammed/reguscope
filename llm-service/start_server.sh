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

# Find the llama.cpp server binary
LLAMA_BIN=""
for bin_name in llama-server server llama-cli; do
    if command -v "$bin_name" &> /dev/null; then
        LLAMA_BIN="$bin_name"
        break
    fi
    
    # Check in /usr/local/bin
    if [ -f "/usr/local/bin/$bin_name" ]; then
        LLAMA_BIN="/usr/local/bin/$bin_name"
        break
    fi
    
    # Check in build directory
    if [ -f "/usr/local/build/bin/$bin_name" ]; then
        LLAMA_BIN="/usr/local/build/bin/$bin_name"
        break
    fi
done

if [ -z "$LLAMA_BIN" ]; then
    echo "❌ Error: llama.cpp server binary not found"
    echo "Searching in common locations..."
    find /usr/local -name "*server*" -o -name "*llama*" 2>/dev/null || true
    exit 1
fi

echo "Using binary: $LLAMA_BIN"

# Start server with optimized settings for Cloud Run Free Tier
"$LLAMA_BIN" \
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