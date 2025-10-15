import os
import requests
from typing import Dict, Any, TypedDict, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "reguscope_compliance_kb")
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

# Cloud Run LLM Configuration
CLOUD_RUN_LLM_URL = os.getenv("CLOUD_RUN_LLM_URL")  # Set this to your service URL

# Initialize global resources
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embeddings_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')


# --- Custom LLM Wrapper for Cloud Run ---
class CloudRunLLM:
    """Wrapper for llama.cpp server running on Cloud Run"""
    
    def __init__(self, endpoint_url: str, timeout: int = 60):
        self.endpoint_url = endpoint_url.rstrip('/') + '/completion'
        self.timeout = timeout
    
    def invoke(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Call the Cloud Run LLM service"""
        try:
            response = requests.post(
                self.endpoint_url,
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stop": ["\n\n", "###"]
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('content', '').strip()
        
        except requests.exceptions.Timeout:
            raise Exception("LLM request timeout - Cloud Run may be cold starting")
        except requests.exceptions.RequestException as e:
            raise Exception(f"LLM request failed: {str(e)}")


# Initialize LLM
llm = CloudRunLLM(endpoint_url=CLOUD_RUN_LLM_URL)


# --- Agent State Definition ---
class AgentState(TypedDict):
    """The state that flows through the Agentic RAG workflow."""
    original_query: str
    decomposed_queries: List[str]
    retrieved_contexts: List[Dict[str, Any]]
    synthesized_answer: str
    citations: Dict[str, Any]
    validation_passed: bool
    error: str | None


# --- Node 1: Query Decomposition Agent ---
def query_decomposition_node(state: AgentState) -> AgentState:
    """Breaks down complex compliance queries into sub-queries."""
    print("🔍 Node 1: Query Decomposition")
    
    original_query = state["original_query"]
    
    # Optimized prompt for Phi-3 Mini
    decomposition_prompt = f"""Task: Break this regulatory question into 2-3 specific sub-questions.

Question: {original_query}

Format: Return only numbered sub-questions, one per line.

Sub-questions:"""

    try:
        response = llm.invoke(decomposition_prompt, max_tokens=300, temperature=0.3)
        
        # Parse the response
        sub_queries = [
            line.strip() 
            for line in response.strip().split('\n') 
            if line.strip() and any(c.isdigit() for c in line[:3])
        ]
        
        # Fallback
        if not sub_queries:
            sub_queries = [original_query]
        
        state["decomposed_queries"] = sub_queries
        print(f"   Decomposed into {len(sub_queries)} sub-queries")
        
    except Exception as e:
        print(f"   Error in decomposition: {e}")
        state["decomposed_queries"] = [original_query]
        state["error"] = f"Decomposition error: {str(e)}"
    
    return state


# --- Node 2: Retrieval Agent (Unchanged) ---
def retrieval_node(state: AgentState) -> AgentState:
    """Executes semantic search against Qdrant."""
    print("📚 Node 2: Retrieval from Qdrant")
    
    all_contexts = []
    
    for sub_query in state["decomposed_queries"]:
        print(f"   Searching for: {sub_query[:60]}...")
        
        try:
            query_vector = embeddings_model.encode(
                sub_query, 
                convert_to_numpy=True,
                normalize_embeddings=True
            ).tolist()
            
            search_results = qdrant_client.search(
                collection_name=QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                limit=3,
                with_payload=True
            )
            
            for result in search_results:
                context = {
                    "content": result.payload.get("text_preview", ""),
                    "document_id": result.payload.get("document_ID", "Unknown"),
                    "section_number": result.payload.get("section_number", "N/A"),
                    "effective_date": result.payload.get("effective_date", "Unknown"),
                    "jurisdiction": result.payload.get("jurisdiction", "Unknown"),
                    "score": result.score,
                    "sub_query": sub_query
                }
                all_contexts.append(context)
            
        except Exception as e:
            print(f"   Retrieval error: {e}")
            state["error"] = f"Retrieval error: {str(e)}"
    
    state["retrieved_contexts"] = all_contexts
    print(f"   Retrieved {len(all_contexts)} total contexts")
    
    return state


# --- Node 3: Synthesis Agent ---
def synthesis_node(state: AgentState) -> AgentState:
    """Synthesizes answer from retrieved contexts."""
    print("💡 Node 3: Synthesis and Reasoning")
    
    original_query = state["original_query"]
    contexts = state["retrieved_contexts"]
    
    # Build context string with citations
    context_str = "\n\n".join([
        f"[Source {i+1}] Doc: {ctx['document_id']}, Section: {ctx['section_number']}\n{ctx['content']}"
        for i, ctx in enumerate(contexts)
    ])
    
    # Optimized synthesis prompt for Phi-3 Mini
    synthesis_prompt = f"""You are a regulatory compliance expert. Answer this question using ONLY the provided sources.

Question: {original_query}

Sources:
{context_str}

Instructions:
1. Answer directly and accurately
2. Cite sources as [Source X]
3. If information is missing, state it clearly
4. Be concise but complete

Answer:"""

    try:
        answer = llm.invoke(synthesis_prompt, max_tokens=600, temperature=0.5)
        state["synthesized_answer"] = answer.strip()
        
        # Create citations
        citations = {}
        for i, ctx in enumerate(contexts):
            citations[f"source_{i+1}"] = {
                "document_id": ctx["document_id"],
                "section_number": ctx["section_number"],
                "effective_date": ctx["effective_date"],
                "jurisdiction": ctx["jurisdiction"],
                "relevance_score": round(ctx["score"], 3),
                "snippet": ctx["content"][:200] + "..."
            }
        
        state["citations"] = citations
        print(f"   Generated answer with {len(citations)} citations")
        
    except Exception as e:
        print(f"   Synthesis error: {e}")
        state["synthesized_answer"] = "Error generating answer."
        state["citations"] = {}
        state["error"] = f"Synthesis error: {str(e)}"
    
    return state


# --- Node 4: Validation Agent (Unchanged) ---
def validation_node(state: AgentState) -> AgentState:
    """Basic validation checks."""
    print("✅ Node 4: Validation")
    
    answer = state["synthesized_answer"]
    citations = state["citations"]
    
    has_content = len(answer) > 50
    has_citations = len(citations) > 0
    
    state["validation_passed"] = has_content and has_citations
    
    if not state["validation_passed"]:
        print("   ⚠️ Validation failed")
    else:
        print("   ✓ Validation passed")
    
    return state


# --- Build LangGraph Workflow (Unchanged) ---
def build_agent_graph():
    """Constructs the stateful LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("decompose", query_decomposition_node)
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("synthesize", synthesis_node)
    workflow.add_node("validate", validation_node)
    
    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "retrieve")
    workflow.add_edge("retrieve", "synthesize")
    workflow.add_edge("synthesize", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()


agent_graph = build_agent_graph()


# --- Main Invocation Function (Unchanged) ---
def agent_workflow_invoke_sync(query: str, user_id: str, trace_id: str | None) -> Dict[str, Any]:
    """Executes the full Agentic Flow Protocol."""
    print(f"\n{'='*60}")
    print(f"🚀 Processing query for user {user_id}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    initial_state = {
        "original_query": query,
        "decomposed_queries": [],
        "retrieved_contexts": [],
        "synthesized_answer": "",
        "citations": {},
        "validation_passed": False,
        "error": None
    }
    
    try:
        final_state = agent_graph.invoke(initial_state)
        
        return {
            "answer": final_state["synthesized_answer"],
            "citations": final_state["citations"]
        }
        
    except Exception as e:
        print(f"❌ Critical workflow error: {e}")
        return {
            "answer": f"I encountered an error processing your compliance query: {str(e)}",
            "citations": {"error": str(e)}
        }