import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Optional
from utils.config import get_path, get_hyperparameter, ensure_dirs_exist

def download_planbench_xl(output_dir: Optional[Path] = None, max_retries: int = 3) -> Path:
    """Download PlanBench-XL dataset with retry logic."""
    if output_dir is None:
        output_dir = get_path('data/raw')
    
    ensure_dirs_exist(output_dir)
    
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            from datasets import load_dataset
            
            # Stream the dataset to avoid OOM
            dataset = load_dataset("PlanBench/planbench-xl", streaming=True)
            
            # Save a sample to verify download (in real usage, process chunks)
            raw_file = output_dir / "planbench_xl.parquet"
            
            # For streaming, we need to collect data in chunks
            # This is a simplified version - in production, process in chunks
            collected_data = []
            for split in dataset:
                for idx, item in enumerate(dataset[split]):
                    if idx < 100:  # Sample first 100 for verification
                        collected_data.append(item)
            
            # Save as JSONL for now (parquet requires pyarrow)
            jsonl_file = output_dir / "planbench_xl.jsonl"
            with open(jsonl_file, 'w') as f:
                for item in collected_data:
                    f.write(json.dumps(item) + '\n')
            
            return jsonl_file
            
        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                raise RuntimeError(f"Failed to download PlanBench-XL after {max_retries} retries: {e}")
    
    raise RuntimeError(f"Failed to download PlanBench-XL: {last_error}")

def load_injected_data(input_path: Optional[Path] = None) -> list:
    """Load the injected failure subset."""
    if input_path is None:
        input_path = get_path('data/derived/implicit_failure_subset.jsonl')
    
    data = []
    if input_path.exists():
        with open(input_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return data

def main():
    """Main entry point for data loader."""
    output_file = download_planbench_xl()
    print(f"Dataset downloaded to: {output_file}")

if __name__ == "__main__":
    main()
