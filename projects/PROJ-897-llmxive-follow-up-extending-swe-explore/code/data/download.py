import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Note: This script will fail if 'datasets' is not installed.
# The execution failure log indicated: ModuleNotFoundError: No module named 'datasets'
# This is expected behavior per the "Fail loudly" constraint.
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is not installed.")
    print("Please run: pip install datasets")
    sys.exit(1)

from config import get_path, get_config_summary, HF_DATASET_NAME, HF_DATASET_SPLIT, DATA_RAW

def download_benchmark_dataset(output_file: Optional[Path] = None) -> Path:
    """
    Downloads the benchmark dataset from HuggingFace and saves it as JSONL.
    Raises ConnectionError or FileNotFoundError on failure.
    """
    if output_file is None:
        output_file = DATA_RAW / "bench.final.public.jsonl"
    
    print(f"Downloading dataset: {HF_DATASET_NAME} (split: {HF_DATASET_SPLIT})")
    print(f"Output path: {output_file}")

    try:
        # Use streaming to avoid loading full dataset into memory if possible,
        # but for saving to disk we need to iterate.
        dataset = load_dataset(HF_DATASET_NAME, split=HF_DATASET_SPLIT, streaming=True)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            count = 0
            for item in dataset:
                f.write(json.dumps(item) + '\n')
                count += 1
                if count % 1000 == 0:
                    print(f"Downloaded {count} items...")
        
        print(f"Successfully downloaded {count} items to {output_file}")
        return output_file

    except Exception as e:
        raise ConnectionError(f"Failed to download dataset: {e}")

def main():
    try:
        download_benchmark_dataset()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
