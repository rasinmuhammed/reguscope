#!/usr/bin/env python3
import os
from google.cloud import storage

def download_model():
    """Download model from Cloud Storage if not exists locally"""
    bucket_name = os.getenv('MODEL_BUCKET')
    model_file = os.getenv('MODEL_FILE')
    local_path = f'/models/{model_file}'
    
    # Skip if already downloaded
    if os.path.exists(local_path):
        print(f"Model already exists at {local_path}")
        return local_path
    
    print(f"Downloading model from gs://{bucket_name}/{model_file}...")
    
    # Download from GCS
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(model_file)
    blob.download_to_filename(local_path)
    
    print(f"Model downloaded successfully to {local_path}")
    return local_path

if __name__ == "__main__":
    download_model()