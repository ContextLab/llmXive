"""
ARC-Bench Data Ingestion Module

Fetches the ARC-Bench topic subset from HuggingFace datasets.
Implements strict real-data loading with no synthetic fallbacks.
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

logger = get_logger(__name__)

# Configuration
DATASET_NAME = "allenai/ai2_arc"
DATASET_SPLIT = "challenge"  # ARC-Challenge is the harder subset
TARGET_TOPIC_SUBSET = "science"  # We will filter for science-related topics if available, 
                                 # or use the full challenge set as the "topic subset"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "raw" / "arc_bench_challenge.json"
MAX_ENTRIES = 1000  # Limit for initial ingestion to manage memory, adjust as needed

def fetch_arc_bench_subset(
    dataset_name: str = DATASET_NAME,
    split: str = DATASET_SPLIT,
    output_path: Optional[Path] = None,
    max_entries: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches the ARC-Bench dataset from HuggingFace and saves it locally.
    
    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'challenge', 'test').
        output_path: Path to save the JSON file. Defaults to data/raw/arc_bench_challenge.json.
        max_entries: Maximum number of entries to fetch. If None, fetches all.
    
    Returns:
        List of dictionaries representing the dataset entries.
    
    Raises:
        ImportError: If the 'datasets' library is not installed.
        Exception: If the dataset cannot be fetched or processed.
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching dataset: {dataset_name} (split: {split})")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via 'pip install datasets'.")
        raise ImportError("Missing dependency: datasets") from None
    
    # Validate resource limits before loading large data
    validate_resource_limits()
    
    try:
        # Load the dataset
        # Note: We use streaming=False to load into memory for processing, 
        # but we could use streaming=True if memory is tight and we process in chunks.
        # Given the constraint of 7GB RAM, we load the specific split.
        dataset = load_dataset(dataset_name, split=split)
        
        logger.info(f"Dataset loaded successfully. Total rows: {len(dataset)}")
        
        # Convert to list of dicts
        data_list = dataset.to_list()
        
        # Apply max_entries limit if specified
        if max_entries is not None and len(data_list) > max_entries:
            logger.info(f"Limiting output to {max_entries} entries.")
            data_list = data_list[:max_entries]
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(data_list)} entries to {output_path}")
        
        return data_list
        
    except Exception as e:
        logger.error(f"Failed to fetch or process dataset: {e}")
        raise RuntimeError(f"Dataset fetch failed: {e}") from e

def main():
    """
    Main entry point for the script.
    Fetches the ARC-Bench dataset and saves it to the configured output path.
    """
    log_stage_start("Data Ingestion: Download ARC-Bench")
    
    try:
        # Validate resource limits at the start of the script
        validate_resource_limits()
        
        data = fetch_arc_bench_subset(
            dataset_name=DATASET_NAME,
            split=DATASET_SPLIT,
            output_path=OUTPUT_FILE,
            max_entries=MAX_ENTRIES
        )
        
        log_stage_end("Data Ingestion: Download ARC-Bench", success=True)
        logger.info("Task completed successfully.")
        return 0
        
    except Exception as e:
        log_stage_end("Data Ingestion: Download ARC-Bench", success=False)
        logger.error(f"Task failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())