#!/usr/bin/env python3
import os
import sys

def download_model_at_build_time():
    bucket_name = os.getenv('MODEL_BUCKET', 'reguscope-models')
    model_file = os.getenv('MODEL_FILE', 'Phi-3-mini-4k-instruct-Q4_K_M.gguf')
    project_id = os.getenv('PROJECT_ID', 'reguscope-rag-prod')
    local_path = f'/models/{model_file}'
    
    print(f"="*60)
    print(f"BUILD-TIME MODEL DOWNLOAD")
    print(f"Project: {project_id}")
    print(f"Bucket: gs://{bucket_name}/{model_file}")
    print(f"Target: {local_path}")
    
    if os.path.exists(local_path):
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"✓ Model exists ({size_mb:.1f} MB)")
        return local_path
    
    print("Downloading from GCS...")
    
    try:
        from google.cloud import storage
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(model_file)
        blob.download_to_filename(local_path)
        
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"✓ Downloaded ({size_mb:.1f} MB)")
        return local_path
    except Exception as e:
        print(f"✗ Failed: {e}")
        print(f"   Check: gsutil ls gs://{bucket_name}/{model_file}")
        sys.exit(1)

if __name__ == "__main__":
    download_model_at_build_time()
