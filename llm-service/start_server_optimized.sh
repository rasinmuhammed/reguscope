#!/bin/bash
set -e

echo "=================================================="
echo "  ReguScope LLM Service - OPTIMIZED"
echo "  Model: Pre-loaded (no download)"
echo "=================================================="

MODEL_PATH="/models/${MODEL_FILE}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model not found at $MODEL_PATH"
    exit 1
fi

echo "✅ Model verified at: $MODEL_PATH"
ls -lh "$MODEL_PATH"

echo ""
echo "Starting llama-server..."

exec llama-server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --ctx-size 4096 \
    --n-gpu-layers 0 \
    --threads 2 \
    --batch-size 512 \
    --ubatch-size 256 \
    --parallel 1 \
    --cont-batching \
    --metrics \
    --mlock \
    --verbose
