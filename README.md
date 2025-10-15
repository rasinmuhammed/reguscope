# 🏛️ ReguScope: Production-Grade Agentic RAG for Regulatory Compliance

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GCP Cloud Run](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4)](https://cloud.google.com/run)
[![Powered by LangGraph](https://img.shields.io/badge/Powered%20by-LangGraph-green)](https://github.com/langchain-ai/langgraph)

> [Building] **A production-ready, open-source Agentic RAG platform for high-stakes regulatory compliance analysis, featuring multi-step reasoning, full auditability, and enterprise-grade observability.**

---

## 🎯 Overview

ReguScope transforms regulatory compliance from reactive document search into **proactive, auditable risk analysis**. Built specifically for high-compliance industries (defense, life sciences, manufacturing), it uses advanced Agentic RAG to synthesize multi-part regulatory questions into comprehensive, citation-backed answers.

### Key Differentiators

- **🤖 Agentic Multi-Step Reasoning**: Query decomposition → focused retrieval → synthesis → validation
- **📊 Full Auditability**: Every answer includes source citations with document metadata
- **🔍 Enterprise Observability**: Complete LLM trace logging via Langfuse
- **💰 Cost-Optimized**: Runs on GCP Free Tier (~11,250 queries/month at $0)
- **🔓 100% Open Source**: No vendor lock-in, Apache 2.0 licensed models

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────┐
│                  ReguScope Architecture                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐     ┌──────────────┐                  │
│  │   NextJS     │────▶│  FastAPI     │                  │
│  │  Frontend    │     │  (Agents)    │                  │
│  └──────────────┘     └───────┬──────┘                  │
│                               │                          │
│                    ┌──────────┴──────────┐              │
│                    │                     │              │
│              ┌─────▼─────┐      ┌───────▼──────┐       │
│              │  Phi-3    │      │   Qdrant     │       │
│              │  LLM      │      │   VectorDB   │       │
│              │ (Cloud    │      │  (GKE/Cloud) │       │
│              │  Run)     │      │              │       │
│              └───────────┘      └──────────────┘       │
│                                                          │
│              ┌─────────────────────────────┐            │
│              │  RAGOps Pipeline            │            │
│              │  (Cloud Run Job)            │            │
│              │  - Chunking                 │            │
│              │  - BGE-M3 Embeddings        │            │
│              │  - Vector Indexing          │            │
│              └─────────────────────────────┘            │
│                                                          │
│              ┌─────────────────────────────┐            │
│              │  Langfuse Observability     │            │
│              │  - Trace Logging            │            │
│              │  - Cost Tracking            │            │
│              │  - Performance Metrics      │            │
│              └─────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **GCP Account** with billing enabled (Free Tier sufficient)
- **Docker** installed locally
- **Python 3.10+**
- **gcloud CLI** configured

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/reguscope.git
cd reguscope
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```bash
# GCP
PROJECT_ID=reguscope-rag-prod
CLOUD_RUN_LLM_URL=https://llm-service-xxxxx-uc.a.run.app

# Qdrant
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=reguscope_compliance_kb

# Langfuse (Optional but recommended)
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

### 3. Deploy to GCP
```bash
# Deploy LLM Service
cd llm-service
gcloud builds submit --tag gcr.io/$PROJECT_ID/llm-service:v1
gcloud run deploy llm-service \
    --image gcr.io/$PROJECT_ID/llm-service:v1 \
    --region us-central1 \
    --memory 4Gi \
    --cpu 1 \
    --allow-unauthenticated

# Deploy FastAPI Backend
cd ../docker
gcloud builds submit --tag gcr.io/$PROJECT_ID/reguscope-api:v1
gcloud run deploy reguscope-api \
    --image gcr.io/$PROJECT_ID/reguscope-api:v1 \
    --region us-central1 \
    --memory 2Gi \
    --allow-unauthenticated

# Deploy RAGOps Job
cd ../ragops-job
gcloud builds submit --tag gcr.io/$PROJECT_ID/ragops-job:v1
gcloud run jobs create ragops-ingestion \
    --image gcr.io/$PROJECT_ID/ragops-job:v1 \
    --region us-central1

# Run initial data ingestion
gcloud run jobs execute ragops-ingestion --region us-central1 --wait
```

### 4. Test the System
```bash
# Get your API URL
API_URL=$(gcloud run services describe reguscope-api \
    --region us-central1 \
    --format 'value(status.url)')

# Test query
curl -X POST "$API_URL/compliance-query" \
    -H "Content-Type: application/json" \
    -d '{
        "user_query": "What are the penalties for ITAR violations?",
        "user_id": "test_user"
    }' | jq .
```

---

## 📚 Core Components

### 1. Agentic RAG Workflow (LangGraph)

**File**: `docker/backend/rag_agent.py`

The agent workflow consists of 4 coordinated nodes:
```python
1. Query Decomposition Agent
   └─→ Breaks complex questions into focused sub-queries
   
2. Retrieval Agent
   └─→ Semantic search against Qdrant using BGE-M3 embeddings
   
3. Synthesis Agent
   └─→ LLM generates comprehensive answer with citations
   
4. Validation Agent
   └─→ Quality checks (content length, citations present)
```

**Example Flow**:
```
User Query: "What are ITAR penalties and who enforces them?"
    ↓
Decomposition: 
  1. "What are civil penalties under ITAR?"
  2. "Which agency enforces ITAR regulations?"
    ↓
Retrieval: Finds 6 relevant chunks from 2 sub-queries
    ↓
Synthesis: "According to ITAR Section 202, civil penalties..."
    ↓
Validation: ✓ Answer >50 chars, ✓ 6 citations present
```

### 2. LLM Service (Phi-3 Mini via llama.cpp)

**Files**: `llm-service/Dockerfile`, `llm-service/start_server.sh`

- **Model**: Phi-3 Mini 4K Instruct (Q4_K_M quantized)
- **Context Window**: 4,096 tokens
- **Deployment**: Cloud Run (1 vCPU, 4 GiB RAM)
- **Cost**: ~$0 on Free Tier for <11,250 queries/month

**Performance**:
- Cold start: 20-40s (model download + loading)
- Warm inference: 2-5s per query
- Throughput: ~20 tokens/second (CPU inference)

### 3. RAGOps Pipeline

**File**: `ragops-job/backend/ingestion.py`

ETL pipeline for knowledge base updates:
```python
1. Document Loading → TextLoader/PyPDF
2. Semantic Chunking → RecursiveCharacterTextSplitter
3. Metadata Augmentation → Compliance fields (jurisdiction, effective_date, etc.)
4. Embedding Generation → BGE-M3 (1024-dim vectors)
5. Vector Indexing → Qdrant upsert with deduplication
```

**Scheduled Execution**: Weekly via Cloud Scheduler

### 4. Observability (Langfuse)

**File**: `docker/main.py` (decorated endpoints)

Tracks:
- **Agent Traces**: Complete workflow execution logs
- **Latency**: Per-node timing metrics
- **Cost**: GiB-seconds consumption tracking
- **Quality**: Validation pass/fail rates

View traces at: `https://cloud.langfuse.com/trace/{trace_id}`

---

## 📖 API Documentation

### Endpoints

#### `POST /compliance-query`

Submit a regulatory compliance question.

**Request**:
```json
{
  "user_query": "What are the export control requirements for technical data under ITAR?",
  "user_id": "user_12345"
}
```

**Response**:
```json
{
  "answer": "According to ITAR Section 121.1(b), the release or transfer of technical data...",
  "citations": {
    "source_1": {
      "document_id": "ITAR_121_1",
      "section_number": "121.1",
      "jurisdiction": "US-DDTC",
      "effective_date": "2024-01-15",
      "relevance_score": 0.892,
      "snippet": "Technical Data Transfer: The release or transfer..."
    }
  },
  "trace_id": "abc123-trace-id"
}
```

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "langfuse_enabled": true
}
```

---

## 🛠️ Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run Qdrant locally
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Run ingestion pipeline
python backend/ingestion.py

# Start FastAPI server
uvicorn main:app --reload --port 8000

# Test locally
curl -X POST "http://localhost:8000/compliance-query" \
    -H "Content-Type: application/json" \
    -d '{"user_query":"Test query","user_id":"dev"}'
```

### Running Tests
```bash
# Full system test
python scripts/test_full_system.py

# Check quota usage
python scripts/monitor_quota.py
```

### Project Structure
```
reguscope/
├── backend/
│   ├── data/
│   │   └── sample_regulation.txt      # Mock compliance data
│   ├── ingestion.py                   # RAGOps ETL pipeline
│   └── rag_agent.py                   # LangGraph agent workflow
├── docker/
│   ├── Dockerfile                     # FastAPI backend
│   ├── main.py                        # API endpoints
│   └── requirements.txt
├── llm-service/
│   ├── Dockerfile                     # Phi-3 Mini deployment
│   ├── download_model.py
│   └── start_server.sh
├── ragops-job/
│   ├── Dockerfile                     # Scheduled ingestion job
│   └── requirements-ragops.txt
├── scripts/
│   ├── test_full_system.py            # E2E tests
│   └── monitor_quota.py               # GCP quota monitoring
├── cloudbuild.yaml                    # CI/CD pipeline
├── .env.example
└── README.md
```

---

## 📊 Performance & Costs

### Free Tier Capacity

| Resource | Limit | Usage per Query | Monthly Capacity |
|----------|-------|-----------------|------------------|
| Cloud Run (Compute) | 180,000 GiB·s | ~16 GiB·s | ~11,250 queries |
| Cloud Storage | 5 GB | ~2 MB (model) | Unlimited reads |
| Egress | 1 GB/month | ~5 KB | ~200,000 queries |

### Optimization Tips

1. **Enable Request Caching**: Cache frequent queries in Redis
2. **Batch Processing**: Group similar queries together
3. **Prompt Optimization**: Reduce token usage in synthesis prompts
4. **Model Quantization**: Already using Q4_K_M (optimal for CPU)

---

## 🔐 Security & Compliance

### Production Checklist

- [ ] Enable Cloud IAM authentication
- [ ] Set up VPC Service Controls
- [ ] Configure DLP API for PII detection
- [ ] Implement rate limiting (via Cloud Armor)
- [ ] Enable Cloud Logging & Monitoring
- [ ] Set up budget alerts


### Model Licenses

- **Phi-3 Mini**: MIT License
- **BGE-M3**: Apache 2.0
- **llama.cpp**: MIT License

---

## 🙏 Acknowledgments

Built following the **ReguScope Blueprint** architecture, leveraging:

- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [Qdrant](https://qdrant.tech/) for vector search
- [Langfuse](https://langfuse.com/) for LLM observability
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for efficient CPU inference

---


## 🗺️ Roadmap

- [ ] NextJS frontend UI
- [ ] Real-time streaming responses
- [ ] Multi-document comparison
- [ ] Regulatory change detection
- [ ] PDF upload & processing
- [ ] Multi-language support
- [ ] Reranking with Cohere/Jina

---
