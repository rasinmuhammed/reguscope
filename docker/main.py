#!/usr/bin/env python3
"""
ReguScope FastAPI Backend
Production-ready API for Agentic RAG compliance queries
"""
import os
import traceback
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the agent workflow
from backend.rag_agent import agent_workflow_invoke_sync

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="ReguScope API",
    description="Production-grade Agentic RAG for Regulatory Compliance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ComplianceQueryRequest(BaseModel):
    user_query: str
    user_id: str


class ComplianceQueryResponse(BaseModel):
    answer: str
    citations: dict
    trace_id: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reguscope-api",
        "version": "1.0.0",
        "llm_url": os.getenv("CLOUD_RUN_LLM_URL", "not_set"),
        "qdrant_host": os.getenv("QDRANT_HOST", "not_set")
    }


# Main compliance query endpoint
@app.post("/compliance-query", response_model=ComplianceQueryResponse)
async def compliance_query(request: ComplianceQueryRequest):
    """
    Process a regulatory compliance query through the Agentic RAG workflow.
    
    Args:
        request: ComplianceQueryRequest with user_query and user_id
    
    Returns:
        ComplianceQueryResponse with answer, citations, and trace_id
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 Received query from user: {request.user_id}")
        print(f"Query: {request.user_query[:100]}...")
        print(f"{'='*60}")
        
        # Invoke the agent workflow
        result = agent_workflow_invoke_sync(
            query=request.user_query,
            user_id=request.user_id,
            trace_id=None  # Langfuse will generate this if enabled
        )
        
        print(f"✅ Query processed successfully")
        
        return ComplianceQueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            trace_id=result.get("trace_id")
        )
        
    except Exception as e:
        error_msg = f"Error processing compliance query: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "type": type(e).__name__
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "ReguScope API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "compliance_query": "/compliance-query (POST)",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)