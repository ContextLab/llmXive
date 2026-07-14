"""
Download the SWE-Explore benchmark dataset from HuggingFace.

This script fetches 'bench.final.public.jsonl' from the
'princeton-nlp/SWE-bench' dataset repository on HuggingFace and saves it
to the project's data/raw directory as defined in config.py.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config_summary
from datasets import load_dataset


def download_benchmark_dataset(output_dir: Path) -> None:
    """
    Fetch the SWE-Explore benchmark dataset from HuggingFace and save to disk.

    Args:
        output_dir: Directory where the dataset file will be saved.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "bench.final.public.jsonl"

    print(f"Loading dataset 'princeton-nlp/SWE-bench' from HuggingFace...")
    
    try:
        # Load the specific dataset split
        # The SWE-bench dataset contains the 'bench.final.public' split
        dataset = load_dataset("princeton-nlp/SWE-bench", split="test")
        
        if len(dataset) == 0:
            raise ValueError("Dataset loaded but contains no records.")

        print(f"Dataset loaded: {len(dataset)} records.")
        print(f"Saving to {output_file}...")

        # Write as JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for record in dataset:
                # Ensure the record is JSON serializable
                # Some fields might be complex types, convert to string if needed
                json_record = {}
                for k, v in record.items():
                    if isinstance(v, (list, dict, str, int, float, bool, type(None))):
                        json_record[k] = v
                    else:
                        json_record[k] = str(v)
                f.write(json.dumps(json_record, ensure_ascii=False) + "\n")

        print(f"Successfully saved {len(dataset)} records to {output_file}")
        
        # Verify file size
        file_size = output_file.stat().st_size
        print(f"Output file size: {file_size / (1024*1024):.2f} MB")

    except Exception as e:
        print(f"Error downloading dataset: {e}")
        raise


def main() -> None:
    """Main entry point for the download script."""
    config = get_config_summary()
    raw_data_dir = Path(config["paths"]["data_raw"])
    
    print(f"Configuration loaded. Data root: {config['paths']['data_root']}")
    print(f"Target directory: {raw_data_dir}")
    
    download_benchmark_dataset(raw_data_dir)


if __name__ == "__main__":
    main()
