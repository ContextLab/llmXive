"""
T010: Implement Robust Data Fetcher.
Downloads the SWE-Explore benchmark dataset from HuggingFace using streaming.
Writes the raw data to data/raw/swe_explore_raw.jsonl.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, get_config_summary, DATA_RAW

# Constants for the dataset
HF_DATASET_NAME = "bench.final.public"
HF_DATASET_SPLIT = "train"
TARGET_FILENAME = "swe_explore_raw.jsonl"

def download_benchmark_dataset(
    dataset_name: str = HF_DATASET_NAME,
    split: str = HF_DATASET_SPLIT,
    output_dir: Optional[Path] = None,
    streaming: bool = True
) -> Path:
    """
    Fetches the SWE-Explore dataset from HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'train').
        output_dir: Directory to write the output file.
        streaming: If True, streams data to avoid loading full dataset into RAM.

    Returns:
        Path to the written JSONL file.

    Raises:
        ConnectionError: If the dataset cannot be fetched or is unavailable.
        FileNotFoundError: If the dataset does not contain the expected file structure.
    """
    # Import datasets here to fail fast if missing, before other logic
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required. "
            "Please install it: pip install datasets"
        )

    if output_dir is None:
        output_dir = get_path(DATA_RAW)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / TARGET_FILENAME

    print(f"Fetching dataset: {dataset_name} (split={split})...")
    
    try:
        # Load dataset in streaming mode to handle large sizes
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
    except Exception as e:
        raise ConnectionError(
            f"Failed to fetch dataset '{dataset_name}' from HuggingFace: {e}"
        ) from e

    print(f"Dataset loaded. Writing to {output_file}...")

    # Write data to JSONL
    # We iterate through the streaming dataset
    written_count = 0
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in dataset:
                # Ensure the item is serializable
                # The SWE-Explore dataset typically has fields like 'problem', 'id', etc.
                # We write the raw record as JSON
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')
                written_count += 1
                
                # Optional: progress indicator every 1000 items
                if written_count % 1000 == 0:
                    print(f"  Written {written_count} records...", end='\r')
        
        print(f"\nSuccessfully wrote {written_count} records to {output_file}.")
        
    except IOError as e:
        # Clean up partial file on write failure
        if output_file.exists():
            output_file.unlink()
        raise IOError(f"Failed to write output file {output_file}: {e}") from e

    return output_file

def main():
    """
    Main entry point for the download script.
    """
    print("--- T010: Robust Data Fetcher ---")
    
    # Get configuration
    config_summary = get_config_summary()
    print(f"Using config: {config_summary}")

    try:
        output_file = download_benchmark_dataset()
        print(f"Task T010 Complete. Output: {output_file}")
    except (ConnectionError, ImportError, IOError) as e:
        print(f"Task T010 Failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Task T010 Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
