import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# FIX: Import the underlying sentence-transformers library directly to bypass Pydantic/Python 3.9 conflicts
from sentence_transformers import SentenceTransformer 

from uuid import uuid4

# --- Configuration (using values from .env.example) ---
load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "reguscope_compliance_kb")
# REVERT: Using the high-performance BGE-M3 model as defined in the blueprint.
EMBEDDING_MODEL_NAME = "BAAI/bge-m3" 

# --- Compliance Metadata Example ---
# This mirrors the mandatory metadata fields defined in Section 2.3 of the blueprint.
MOCK_METADATA = {
    "ITAR_121_1": {
        "document_ID": "ITAR_121_1",
        "effective_date": "2024-01-15",
        "jurisdiction": "US-DDTC",
        "revision_history": "Rev 4.0",
        "source_file": "sample_regulation.txt"
    }
}

# --- Core Functions ---

def load_and_chunk_documents(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Loads text content and applies advanced chunking.
    The blueprint mandates semantic chunking; RecursiveCharacterTextSplitter is a 
    practical and robust proxy for this MVP.
    """
    print(f"Loading and chunking document: {file_path}")
    
    # 1. Load Document
    try:
        # Use a simple TextLoader for the mock file, but this can be replaced by 
        # PyPDFLoader/Unstructured for real PDFs as required by the blueprint.
        loader = TextLoader(file_path)
        documents = loader.load()
    except Exception as e:
        print(f"Error loading document: {e}")
        return []

    # 2. Split Document (Semantic Chunking Proxy)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n#", "\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    
    # 3. Augment Chunk Metadata (Critical for auditability - Section 2.3)
    for i, chunk in enumerate(chunks):
        doc_id = MOCK_METADATA["ITAR_121_1"]["document_ID"]
        
        # Add the compliance-crucial metadata
        chunk.metadata.update({
            "chunk_index": i,
            "text_preview": chunk.page_content[:150] + "...",
            **MOCK_METADATA["ITAR_121_1"] # Spread the mandatory metadata fields
        })

    print(f"Successfully split into {len(chunks)} chunks.")
    return chunks

def initialize_qdrant_client() -> QdrantClient:
    """Initializes and returns the Qdrant client."""
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    try:
        # Client connects to the Qdrant service
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Check if the connection is alive
        client.get_collections() 
        print("Qdrant connection successful.")
        return client
    except Exception as e:
        print(f"ERROR: Could not connect to Qdrant. Ensure Qdrant is running locally at {QDRANT_HOST}:{QDRANT_PORT}")
        print(f"Details: {e}")
        exit(1)

def run_ragops_pipeline():
    """Executes the full RAGOps ETL pipeline."""
    
    # --- 1. Load and Chunk Data ---
    document_path = "backend/data/sample_regulation.txt"
    chunks = load_and_chunk_documents(document_path)
    if not chunks:
        print("Ingestion failed: No chunks to process.")
        return

    # --- 2. Initialize Qdrant and Embedding Model ---
    qdrant_client = initialize_qdrant_client()

    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}. This may take a moment...")
    try:
        # Instantiate the SentenceTransformer model directly, bypassing LangChain wrapper
        embeddings_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME, 
            device='cpu' # Force CPU usage for compatibility
        )
        # BGE-M3 is 1024 dimensions
        EMBEDDING_DIMENSION = 1024 
    except Exception as e:
        print(f"Error loading embedding model {EMBEDDING_MODEL_NAME}.")
        print(f"Details: {e}")
        return

    # --- 3. Vector Update/Refresh (Collection Management) ---
    print(f"Ensuring Qdrant collection '{QDRANT_COLLECTION_NAME}' is ready...")
    
    # Delete and recreate the collection for a clean slate (MVP approach)
    try:
        qdrant_client.delete_collection(collection_name=QDRANT_COLLECTION_NAME)
        print(f"Collection '{QDRANT_COLLECTION_NAME}' deleted.")
    except:
        pass # Ignore if collection doesn't exist
        
    # FIXED: Removed optimizers_config - default settings work fine for MVP
    qdrant_client.recreate_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
    )
    print(f"Collection '{QDRANT_COLLECTION_NAME}' created with dimension {EMBEDDING_DIMENSION}.")

    # --- 4. Generate Embeddings and Upload Points ---
    points = []
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]

    print("Generating embeddings and preparing points for upload...")
    
    # Generate all embeddings in a batch using the SentenceTransformer's encode method
    vectors = embeddings_model.encode(
        texts, 
        convert_to_numpy=True, 
        normalize_embeddings=True
    ).tolist()
    
    for i, (vector, metadata) in enumerate(zip(vectors, metadatas)):
        # Prepare the PointStruct for Qdrant
        points.append(
            PointStruct(
                id=str(uuid4()), # Unique ID for each point
                vector=vector,
                payload=metadata
            )
        )
        # Update section_number based on chunk content for better filtering
        # Note: This logic is simple and depends on the text_preview
        if "# ITAR Section 121.1" in metadata.get("text_preview", ""):
             metadata["section_number"] = "121.1"
        elif "# AECA Section 202" in metadata.get("text_preview", ""):
             metadata["section_number"] = "202"
        else:
             # Defaulting to the section number from the primary metadata if not found in preview
             metadata["section_number"] = metadata.get("section_number", "N/A")
             
    
    # Upload points
    operation_info = qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        wait=True,
        points=points,
    )

    # --- 5. Validation and Conclusion ---
    print("\n--- RAGOps Pipeline Complete ---")
    print(f"Total chunks indexed: {len(points)}")
    print(f"Qdrant operation status: {operation_info.status.name}")
    print("The Compliance Knowledge Base (CKB) is ready for retrieval.")


if __name__ == "__main__":
    # NOTE: You must have a local Qdrant instance running on port 6333 
    # (or the one specified in .env) before running this script.
    run_ragops_pipeline()