#!/usr/bin/env python3
"""
Diagnostic script to find issues with the RAG agent workflow
"""
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    """Check all required environment variables"""
    print("\n" + "="*60)
    print("1. CHECKING ENVIRONMENT VARIABLES")
    print("="*60)
    
    required_vars = [
        "QDRANT_HOST",
        "QDRANT_PORT", 
        "OPENAI_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("\n✓ All environment variables set")
    return True


def test_qdrant_connection():
    """Test connection to Qdrant"""
    print("\n" + "="*60)
    print("2. TESTING QDRANT CONNECTION")
    print("="*60)
    
    try:
        from qdrant_client import QdrantClient
        
        host = os.getenv("QDRANT_HOST")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        print(f"  Connecting to {host}:{port}...")
        client = QdrantClient(host=host, port=port, timeout=10)
        
        # Test connection
        collections = client.get_collections()
        print(f"  ✓ Connected successfully")
        print(f"  Collections: {[c.name for c in collections.collections]}")
        
        # Check if regulatory_docs collection exists
        try:
            collection_info = client.get_collection("regulatory_docs")
            print(f"  ✓ Collection 'regulatory_docs' exists")
            print(f"    Points count: {collection_info.points_count}")
            print(f"    Vector size: {collection_info.config.params.vectors.size}")
            return True
        except Exception as e:
            print(f"  ✗ Collection 'regulatory_docs' not found: {e}")
            return False
            
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        traceback.print_exc()
        return False


def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n" + "="*60)
    print("3. TESTING OPENAI API")
    print("="*60)
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("  Testing with simple completion...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        
        print(f"  ✓ OpenAI API working")
        print(f"    Model: {response.model}")
        print(f"    Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"  ✗ OpenAI API failed: {e}")
        traceback.print_exc()
        return False


def test_agent_import():
    """Test if the agent module can be imported"""
    print("\n" + "="*60)
    print("4. TESTING AGENT MODULE IMPORT")
    print("="*60)
    
    try:
        print("  Importing backend.rag_agent...")
        from backend.rag_agent import agent_workflow_invoke_sync
        print("  ✓ Agent module imported successfully")
        print(f"    Function: {agent_workflow_invoke_sync}")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("\n  Trying alternative import...")
        try:
            sys.path.insert(0, os.getcwd())
            from backend.rag_agent import agent_workflow_invoke_sync
            print("  ✓ Agent module imported (with path adjustment)")
            return True
        except Exception as e2:
            print(f"  ✗ Alternative import failed: {e2}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        traceback.print_exc()
        return False


def test_simple_query():
    """Test a simple query through the agent"""
    print("\n" + "="*60)
    print("5. TESTING SIMPLE AGENT QUERY")
    print("="*60)
    
    try:
        from backend.rag_agent import agent_workflow_invoke_sync
        
        test_query = "What is ITAR?"
        print(f"  Query: {test_query}")
        print("  Invoking agent (this may take 30-60s)...")
        
        result = agent_workflow_invoke_sync(
            query=test_query,
            user_id="test_user",
            trace_id=None
        )
        
        print(f"\n  ✓ Agent responded")
        print(f"  Result type: {type(result)}")
        print(f"  Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            answer = result.get("answer", "")
            citations = result.get("citations", {})
            
            print(f"\n  Answer preview: {answer[:200]}...")
            print(f"  Citations count: {len(citations)}")
            
            if answer and answer != "Error generating answer.":
                print("\n  ✓ Agent is working correctly")
                return True
            else:
                print("\n  ✗ Agent returned empty or error answer")
                print(f"  Full result: {result}")
                return False
        else:
            print(f"\n  ✗ Agent returned unexpected type: {type(result)}")
            print(f"  Value: {result}")
            return False
            
    except Exception as e:
        print(f"\n  ✗ Agent query failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all diagnostics"""
    print("\n" + "="*60)
    print("REGUSCOPE AGENT DIAGNOSTICS")
    print("="*60)
    
    results = {
        "Environment": check_environment(),
        "Qdrant": test_qdrant_connection(),
        "OpenAI": test_openai_connection(),
        "Agent Import": test_agent_import(),
        "Agent Query": test_simple_query()
    }
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All diagnostics passed! Your system should be working.")
    else:
        print("\n❌ Some diagnostics failed. Fix the issues above.")
        print("\nCommon fixes:")
        print("  - Set missing environment variables in .env")
        print("  - Ensure Qdrant is running and accessible")
        print("  - Check OpenAI API key is valid")
        print("  - Run ragops-ingestion job to populate Qdrant")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())