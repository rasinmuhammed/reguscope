import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any

import time
from langfuse import Langfuse
from langfuse import observe

# Assuming this module exists for the agent workflow
from backend.rag_agent import agent_workflow_invoke_sync

# --- Initialization ---
load_dotenv()
app = FastAPI(title="ReguScope Agentic RAG API", version="0.1.0")

# Initialize Langfuse client if keys are provided
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")

langfuse = None
# --- FIX: Uncommented Langfuse initialization block ---
if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    try:
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        print("Langfuse initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize Langfuse: {e}")
        langfuse = None
else:
    print("Warning: Langfuse keys not found. Running without observability tracing.")


# --- Pydantic Data Models (for API Contract) ---

class QueryRequest(BaseModel):
    """Defines the structured input for a compliance query."""
    user_query: str = Field(..., description="The complex regulatory question from the user.")
    user_id: str = Field("anonymous_user", description="A unique identifier for the user or session for memory/tracing.")

class QueryResponse(BaseModel):
    """Defines the structured output, essential for auditability (Section 2.4)."""
    answer: str = Field(..., description="The synthesized, multi-step answer from the Agent.")
    citations: Dict[str, Any] = Field(..., description="The source documents/sections and their metadata used to ground the answer.")
    trace_id: str | None = Field(None, description="The Langfuse trace ID for full auditability.")


# --- API Endpoint ---

@app.post("/compliance-query", response_model=QueryResponse)
# The @observe decorator automatically creates a trace/span for this function execution.
@observe(name="compliance-query-endpoint")
# We modify the signature to accept the trace object injected by the decorator.
def compliance_query(request: QueryRequest, f_trace=None):
    """Primary endpoint with GCP quota tracking"""
    
    start_time = time.time()
    
    # Get trace context from decorator injection
    trace_id = f_trace.id if f_trace else None
    
    # Removed manual trace creation logic (langfuse.trace(...)) as @observe handles it.

    # Invoke Agent Workflow
    try:
        result = agent_workflow_invoke_sync(
            query=request.user_query,
            user_id=request.user_id,
            trace_id=trace_id
        )
        
        # Calculate resource consumption
        duration_seconds = time.time() - start_time
        gib_seconds = 4 * duration_seconds  # 4 GiB memory allocation
        
        # Update trace with resource metrics
        # We only need to check if f_trace was successfully injected
        if f_trace:
            try:
                f_trace.update(
                    output={
                        "answer": result.get("answer", ""),
                        "citation_count": len(result.get("citations", {}))
                    },
                    metadata={
                        "duration_seconds": round(duration_seconds, 2),
                        "gib_seconds_consumed": round(gib_seconds, 4),
                        "estimated_monthly_quota_used": round(gib_seconds / 180000 * 100, 2)  # % of 180,000 GiB-s
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to update trace: {e}")
        
        return QueryResponse(
            answer=result.get("answer", "Error: Agent failed to produce an answer."),
            citations=result.get("citations", {"status": "No citations found."}),
            trace_id=trace_id
        )

    except Exception as e:
        if f_trace:
            try:
                # Log the error on the trace/span
                f_trace.update(
                    output={"error": str(e)},
                    metadata={"status": "failed"}
                )
            except Exception as trace_error:
                print(f"Warning: Failed to update trace with error: {trace_error}")

        print(f"Critical Agent Error: {e}")
        return QueryResponse(
            answer="I am currently experiencing a critical error.",
            citations={"error": str(e)},
            trace_id=trace_id
        )


@app.get("/")
def read_root():
    return {
        "status": "ReguScope API running",
        "message": "Send a POST request to /compliance-query",
        "observability": "enabled" if langfuse else "disabled"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "langfuse_enabled": langfuse is not None
    }