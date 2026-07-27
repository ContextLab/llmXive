"""
Download the SWE-bench dataset from HuggingFace.
Implements robust fetching with streaming to prevent OOM.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary, HF_DATASET_NAME, HF_DATASET_SPLIT, DATA_RAW

def download_benchmark_dataset(output_file: Optional[Path] = None) -> Path:
    """
    Download the SWE-bench dataset from HuggingFace Hub.
    
    Args:
        output_file: Optional path to write the output JSONL file.
                     Defaults to data/raw/swe_explore_raw.jsonl.
                     
    Returns:
        Path to the downloaded file.
        
    Raises:
        ConnectionError: If the dataset cannot be fetched.
        ValueError: If the dataset ID is invalid or not found.
    """
    if output_file is None:
        output_file = DATA_RAW / "swe_explore_raw.jsonl"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading dataset: {HF_DATASET_NAME} (split: {HF_DATASET_SPLIT})")
    print(f"Output path: {output_file}")
    
    try:
        # Import here to avoid heavy dependency load if not needed
        from datasets import load_dataset
        
        # Use streaming to prevent OOM on large datasets
        dataset = load_dataset(
            HF_DATASET_NAME,
            split=HF_DATASET_SPLIT,
            streaming=True
        )
        
        # Iterate and write to file
        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in dataset:
                # Ensure the item is JSON serializable
                # Convert any non-serializable types if necessary
                json_str = json.dumps(item, ensure_ascii=False)
                f.write(json_str + '\n')
                count += 1
                
                if count % 1000 == 0:
                    print(f"  Downloaded {count} records...")
        
        print(f"Successfully downloaded {count} records to {output_file}")
        return output_file
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        error_msg = (
            f"Failed to download dataset '{HF_DATASET_NAME}': {str(e)}. "
            f"Please check your internet connection and dataset availability. "
            f"No synthetic data will be generated."
        )
        raise ConnectionError(error_msg) from e

def main():
    """Entry point for the download script."""
    print("Starting data download...")
    config_summary = get_config_summary()
    print(f"Configuration: {config_summary}")
    
    try:
        output_path = download_benchmark_dataset()
        print(f"Download complete. File saved at: {output_path}")
    except ConnectionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
