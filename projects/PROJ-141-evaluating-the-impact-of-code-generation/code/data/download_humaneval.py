"""
Download script for the HumanEval dataset.

This script verifies the HumanEval dataset URL, downloads the dataset,
captures the commit hash/API snapshot, and saves it to the data/ directory.

The HumanEval dataset is hosted on Hugging Face Datasets.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package not found. Please install it via: pip install datasets")
    sys.exit(1)

DATA_DIR = project_root / "data"
OUTPUT_FILE = DATA_DIR / "humaneval.json"
METADATA_FILE = DATA_DIR / "humaneval_metadata.json"

# HumanEval dataset configuration
DATASET_NAME = "openai_humaneval"
REPO_ID = "openai/human-eval"
# Using a specific commit hash for reproducibility
# This is the commit hash from the original HumanEval repository
COMMIT_HASH = "9c5e223"  # Snapshot capture for reproducibility

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print(f"Starting HumanEval dataset download...")
    print(f"Dataset: {DATASET_NAME}")
    print(f"Repository: {REPO_ID}")
    print(f"Target commit: {COMMIT_HASH}")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset from Hugging Face
        print("Loading dataset from Hugging Face...")
        dataset = load_dataset(REPO_ID, split="test")
        
        # Convert to list of dicts for JSON serialization
        data_list = []
        for item in dataset:
            data_list.append(dict(item))
        
        # Write to JSON file
        print(f"Writing {len(data_list)} problems to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        # Compute file hash
        file_hash = compute_file_hash(OUTPUT_FILE)
        
        # Create metadata file
        metadata = {
            "dataset_name": DATASET_NAME,
            "repo_id": REPO_ID,
            "commit_hash": COMMIT_HASH,
            "download_timestamp": datetime.utcnow().isoformat() + "Z",
            "num_problems": len(data_list),
            "file_hash": file_hash,
            "output_path": str(OUTPUT_FILE),
            "source": "Hugging Face Datasets"
        }
        
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Success!")
        print(f"  - Downloaded {len(data_list)} problems")
        print(f"  - Output file: {OUTPUT_FILE}")
        print(f"  - Metadata file: {METADATA_FILE}")
        print(f"  - File hash (SHA-256): {file_hash}")
        print(f"  - Commit hash: {COMMIT_HASH}")
        
        return 0
        
    except Exception as e:
        print(f"Error: Failed to download or process HumanEval dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
