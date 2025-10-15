#!/usr/bin/env python3
"""
Complete end-to-end test of the ReguScope system
"""
import requests
import json
import time
import sys

# Update with your actual API URL
API_URL = "https://reguscope-api-773013301963.us-central1.run.app"

def test_health():
    """Test health endpoints"""
    print("="*60)
    print("1. Testing Health Endpoints")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"✓ API Health: {response.json()}")
    except Exception as e:
        print(f"✗ API Health check failed: {e}")
        return False
    
    return True

def test_compliance_query():
    """Test full compliance query workflow"""
    print("\n" + "="*60)
    print("2. Testing Compliance Query (Full Agent Workflow)")
    print("="*60)
    
    query = {
        "user_query": "What are the civil penalties for ITAR violations and which agency enforces them?",
        "user_id": "test_user_001"
    }
    
    print(f"\nQuery: {query['user_query']}")
    print("\nSending request (may take 60-90s on first call)...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/compliance-query",
            json=query,
            timeout=120,
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✓ Success! (took {duration:.1f}s)")
            print("\n" + "-"*60)
            print("ANSWER:")
            print("-"*60)
            print(result['answer'])
            print("\n" + "-"*60)
            print(f"CITATIONS: {len(result['citations'])} sources")
            print("-"*60)
            
            for source_id, citation in result['citations'].items():
                print(f"\n{source_id}:")
                print(f"  Document: {citation['document_id']}")
                print(f"  Section: {citation['section_number']}")
                print(f"  Jurisdiction: {citation['jurisdiction']}")
                print(f"  Relevance: {citation['relevance_score']}")
            
            if result.get('trace_id'):
                print(f"\n📊 Trace ID: {result['trace_id']}")
                print(f"   View in Langfuse: https://cloud.langfuse.com/trace/{result['trace_id']}")
            
            return True
        else:
            print(f"\n✗ Request failed: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timeout (>120s)")
        print("   The LLM service may be cold starting. Try again in 30s.")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("ReguScope Full System Test")
    print("="*60)
    
    # Test 1: Health
    if not test_health():
        print("\n❌ Health check failed. Aborting tests.")
        sys.exit(1)
    
    # Test 2: Compliance Query
    if not test_compliance_query():
        print("\n❌ Compliance query test failed.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour ReguScope system is fully operational.")
    sys.exit(0)

if __name__ == "__main__":
    main()