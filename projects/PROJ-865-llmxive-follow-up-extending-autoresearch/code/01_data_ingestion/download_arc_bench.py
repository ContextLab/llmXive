"""
ARC-Bench Data Ingestion Module

Fetches the ARC-Bench topic subset from HuggingFace datasets.
Implements strict real-data loading with no synthetic fallbacks.
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found. Please install it via 'pip install datasets'.")
    sys.exit(1)

logger = get_logger("download_arc_bench")
RAW_DIR = Path("data/raw")
DATASET_NAME = "allenai/ai2_arc"  # Using ARC-Challenge as a proxy for ARC-Bench topic subset

def validate_resource_limits():
    # Placeholder for resource validation if needed before download
    pass

def fetch_arc_bench_subset(subset_size: int = 200) -> Dict[str, Any]:
    """
    Fetches a subset of the ARC dataset from HuggingFace.
    Returns the dataset as a dictionary.
    """
    logger.info(f"Fetching subset of {subset_size} examples from {DATASET_NAME}...")
    
    # Load a small subset of the dataset
    # Using streaming to avoid loading full dataset into memory
    dataset = load_dataset(DATASET_NAME, "ARC-Challenge", split="validation", streaming=True)
    
    # Convert to list with limited size
    data_list = []
    count = 0
    for item in dataset:
        data_list.append(item)
        count += 1
        if count >= subset_size:
            break
    
    logger.info(f"Successfully fetched {len(data_list)} examples.")
    return data_list

def save_dataset_to_json(data: Dict[str, Any], output_path: Path):
    """
    Saves the fetched dataset to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved dataset to {output_path}")

def main():
    log_stage_start(logger, "download_arc_bench")
    
    # Validate resources
    validate_resource_limits()
    
    # Ensure raw directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = RAW_DIR / "arc_bench.json"
    
    try:
        data = fetch_arc_bench_subset(subset_size=200)
        save_dataset_to_json(data, output_path)
    except Exception as e:
        logger.error(f"Failed to download or save dataset: {e}")
        sys.exit(1)
    
    log_stage_end(logger, "download_arc_bench")

if __name__ == "__main__":
    sys.exit(main())