"""
Data Acquisition Script (T012).

Downloads the CodeSearchNet Python subset from HuggingFace Datasets.
Saves raw data to `data/raw/` and logs metadata to `data/processed/metadata.json`.

Uses the canonical HuggingFace `datasets` loader as per T047.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.logging_config import setup_deterministic_logging, set_seed, get_logger
from utils.memory_guard import check_and_abort_or_downsample

# Setup logging
setup_deterministic_logging()
set_seed(42)
logger = get_logger(__name__)

def main():
    logger.info("Starting data acquisition for CodeSearchNet (Python subset).")
    
    # Define paths
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = raw_dir / "codesearchnet_python.parquet"
    metadata_file = processed_dir / "metadata.json"
    
    logger.info(f"Output path: {output_file}")
    
    # Check memory before starting
    check_and_abort_or_downsample()
    
    try:
        # Load the dataset using the canonical HuggingFace loader
        # Dataset: "codeparrot/code_search_net"
        # Config: "python" (specific language subset)
        # Split: "train"
        logger.info("Loading dataset from HuggingFace (codeparrot/code_search_net, python)...")
        
        dataset = load_dataset(
            "codeparrot/code_search_net",
            "python",
            split="train",
            trust_remote_code=True
        )
        
        logger.info(f"Dataset loaded. Total snippets: {len(dataset)}")
        
        # Check memory again after loading
        check_and_abort_or_downsample()
        
        # Save to parquet
        logger.info(f"Saving to {output_file}...")
        dataset.to_parquet(str(output_file))
        
        # Generate metadata
        metadata = {
            "download_timestamp": datetime.now().isoformat(),
            "source": "codeparrot/code_search_net (python subset)",
            "total_raw_snippets": len(dataset),
            "output_file": str(output_file),
            "status": "completed"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Data acquisition complete. Total snippets: {metadata['total_raw_snippets']}")
        logger.info(f"Metadata saved to {metadata_file}")
        
    except Exception as e:
        logger.error(f"Error during data acquisition: {e}", exc_info=True)
        # Update metadata with error status
        error_metadata = {
            "download_timestamp": datetime.now().isoformat(),
            "source": "codeparrot/code_search_net (python subset)",
            "total_raw_snippets": 0,
            "status": "failed",
            "error": str(e)
        }
        with open(metadata_file, 'w') as f:
            json.dump(error_metadata, f, indent=2)
        raise

if __name__ == "__main__":
    main()