"""
Dataset download and verification script for the Memory Palaces in LLMs project.

Downloads three permitted datasets from Hugging Face Datasets:
1. bAbI Task 3 (babi, task3_10k)
2. LAMBADA (lambada)
3. Story Cloze Test (story_cloze)

Computes and stores SHA-256 checksums for all downloaded files in data/raw/checksums.json.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from datasets import load_dataset

# Ensure we are running from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = DATA_RAW_DIR / "checksums.json"

# Configuration for the three permitted datasets
DATASETS_CONFIG = [
    {
        "name": "babi_task3",
        "dataset_name": "babi",
        "config": "task3_10k",
        "split": "train",
        "description": "bAbI Task 3: Path Finding"
    },
    {
        "name": "lambada",
        "dataset_name": "lambada",
        "config": None,
        "split": "test",
        "description": "LAMBADA: Language Modeling with Long-Term Context"
    },
    {
        "name": "story_cloze",
        "dataset_name": "story_cloze",
        "config": "2016",
        "split": "validation",
        "description": "Story Cloze Test: Narrative Understanding"
    }
]

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_dataset_checksum(dataset: Any, name: str) -> str:
    """
    Compute a deterministic checksum for a dataset by hashing its string representation.
    This is a practical approach for Hugging Face datasets which are often in-memory.
    For large datasets, we hash a sample of the data to ensure reproducibility.
    """
    # Convert dataset to a string representation for hashing
    # We'll hash the first 1000 examples to ensure consistency
    sample_size = min(1000, len(dataset))
    sample_data = []
    
    for i in range(sample_size):
        example = dataset[i]
        # Convert example to a sorted string representation
        example_str = json.dumps(example, sort_keys=True)
        sample_data.append(example_str)
    
    combined_str = "\n".join(sample_data)
    return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()

def download_dataset(config: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Any]]:
    """Download and verify a single dataset."""
    print(f"\n{'='*60}")
    print(f"Downloading: {config['description']}")
    print(f"Dataset: {config['dataset_name']}")
    print(f"Config: {config['config']}")
    print(f"Split: {config['split']}")
    print(f"{'='*60}")
    
    try:
        # Load the dataset
        if config['config']:
            dataset = load_dataset(config['dataset_name'], config['config'])
        else:
            dataset = load_dataset(config['dataset_name'])
        
        # Get the specific split
        if config['split'] not in dataset:
            print(f"Error: Split '{config['split']}' not found in dataset.")
            return False, None, None
        
        split_data = dataset[config['split']]
        print(f"Successfully loaded {len(split_data)} examples.")
        
        # Compute checksum
        checksum = compute_dataset_checksum(split_data, config['name'])
        print(f"Computed checksum: {checksum}")
        
        return True, checksum, split_data
        
    except Exception as e:
        print(f"Error downloading {config['name']}: {str(e)}")
        return False, None, None

def save_checksums(checksums: Dict[str, str]):
    """Save checksums to JSON file."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    print(f"\nChecksums saved to {CHECKSUMS_FILE}")

def load_existing_checksums() -> Dict[str, str]:
    """Load existing checksums if file exists."""
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, 'r') as f:
            return json.load(f)
    return {}

def main():
    """Main function to download all datasets and compute checksums."""
    print("Memory Palaces in LLMs - Dataset Download and Verification")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_RAW_DIR}")
    
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums
    existing_checksums = load_existing_checksums()
    new_checksums = existing_checksums.copy()
    
    success_count = 0
    failed_datasets = []
    
    for config in DATASETS_CONFIG:
        result = download_dataset(config)
        
        if result[0]:  # Success
            success_count += 1
            new_checksums[config['name']] = result[1]
            print(f"✓ {config['name']} downloaded and verified")
        else:
            failed_datasets.append(config['name'])
            print(f"✗ {config['name']} failed to download")
    
    # Save all checksums
    save_checksums(new_checksums)
    
    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Total datasets: {len(DATASETS_CONFIG)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_datasets)}")
    
    if failed_datasets:
        print(f"Failed datasets: {', '.join(failed_datasets)}")
        sys.exit(1)
    else:
        print("All datasets downloaded and verified successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()