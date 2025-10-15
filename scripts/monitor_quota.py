#!/usr/bin/env python3
"""
Monitor GCP Free Tier usage via Langfuse traces
"""
import os
from langfuse import Langfuse
from datetime import datetime, timedelta

def check_monthly_quota():
    """Calculate current month's GiB-second consumption"""
    
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY")
    )
    
    # Get traces from current month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    
    traces = langfuse.fetch_traces(
        from_timestamp=start_of_month
    )
    
    total_gib_seconds = 0
    total_queries = 0
    
    for trace in traces.data:
        if trace.metadata and "gib_seconds_consumed" in trace.metadata:
            total_gib_seconds += trace.metadata["gib_seconds_consumed"]
            total_queries += 1
    
    # Free tier limit: 180,000 GiB-seconds/month
    FREE_TIER_LIMIT = 180000
    usage_percent = (total_gib_seconds / FREE_TIER_LIMIT) * 100
    
    print(f"\n{'='*60}")
    print(f"GCP Cloud Run Free Tier Usage - {datetime.now().strftime('%B %Y')}")
    print(f"{'='*60}")
    print(f"Total Queries Processed: {total_queries}")
    print(f"GiB-Seconds Consumed: {total_gib_seconds:.2f}")
    print(f"Free Tier Limit: {FREE_TIER_LIMIT}")
    print(f"Usage: {usage_percent:.2f}%")
    print(f"Remaining: {FREE_TIER_LIMIT - total_gib_seconds:.2f} GiB-seconds")
    
    if usage_percent > 80:
        print(f"\n⚠️  WARNING: Approaching free tier limit!")
    elif usage_percent > 100:
        print(f"\n❌ CRITICAL: Free tier exceeded! Charges may apply.")
    else:
        print(f"\n✅ Within free tier limits")
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    check_monthly_quota()