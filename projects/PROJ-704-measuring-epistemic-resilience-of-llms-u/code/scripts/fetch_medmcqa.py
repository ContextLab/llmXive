"""
Fetches the MedMCQA (MedQA) dataset from HuggingFace and verifies checksums.

This script downloads the 'medmcqa' dataset, saves it to data/raw/,
and generates a manifest file with SHA-256 checksums for verification.
"""
import os
import hashlib
import json
from pathlib import Path

from datasets import load_dataset

# Configuration
DATASET_NAME = "medmcqa"
HUGGINGFACE_REPO = "medmcqa/medmcqa"
OUTPUT_DIR = Path("data/raw")
MANIFEST_FILE = OUTPUT_DIR / "manifest.json"
PARTITIONS = ["train", "validation", "test"]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def save_dataset_to_jsonl(dataset, partition_name: str, output_dir: Path) -> Path:
    """Save a dataset partition to a JSONL file."""
    output_path = output_dir / f"{DATASET_NAME}_{partition_name}.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return output_path

def fetch_and_verify():
    """Main execution logic."""
    print(f"Starting fetch of dataset: {HUGGINGFACE_REPO}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_data = {
        "dataset": HUGGINGFACE_REPO,
        "partitions": {}
    }

    try:
        # Load the full dataset
        # The medmcqa dataset on HF typically has train, validation, test splits
        dataset = load_dataset(HUGGINGFACE_REPO)
        
        print("Dataset loaded successfully. Saving partitions...")

        for partition in PARTITIONS:
            if partition not in dataset:
                print(f"Warning: Partition '{partition}' not found in dataset. Skipping.")
                continue

            partition_ds = dataset[partition]
            print(f"Processing partition: {partition} (size: {len(partition_ds)})")

            # Save to JSONL
            jsonl_path = save_dataset_to_jsonl(partition_ds, partition, OUTPUT_DIR)
            
            # Calculate checksum
            checksum = calculate_sha256(jsonl_path)
            
            manifest_data["partitions"][partition] = {
                "file": jsonl_path.name,
                "checksum": checksum,
                "size_rows": len(partition_ds)
            }
            print(f"  Saved: {jsonl_path.name} | Checksum: {checksum[:16]}...")

        # Save manifest
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        
        print(f"\nManifest saved to: {MANIFEST_FILE}")
        print("Fetch and verification complete.")
        return True

    except Exception as e:
        print(f"Error during fetch: {e}")
        raise

if __name__ == "__main__":
    fetch_and_verify()
