import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the project root is in the path to allow imports from src/lib
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

from src.lib.utils import get_logger

# Initialize logger
logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_gold_standard(output_dir: Optional[Path] = None) -> Path:
    """
    Fetch the verified public-domain dataset 'llmXive/arcane-gold-standard' from HuggingFace.
    Saves to data/gold_standard/human_annotations.json and computes SHA256.
    
    Constraints:
    - If fetch fails, raises RuntimeError.
    - Does NOT generate synthetic data.
    """
    if output_dir is None:
        output_dir = project_root / "data" / "gold_standard"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "human_annotations.json"

    logger.info(f"Attempting to fetch dataset 'llmXive/arcane-gold-standard'...")
    
    try:
        # Attempt to load the dataset from HuggingFace
        # We assume the dataset is a JSON format or can be converted to a dict/list
        dataset = load_dataset("llmXive/arcane-gold-standard", split="train")
        
        # Convert to list of dicts if it's a Dataset object
        if hasattr(dataset, 'to_pandas'):
            # If it's a pandas dataframe-like object
            data_list = dataset.to_dict()
            # Reconstruct list of dicts if needed, assuming standard HF structure
            # HF datasets usually iterate as dicts
            data_list = [dict(row) for row in dataset]
        else:
            # Fallback: iterate if it's already iterable
            data_list = [dict(row) for row in dataset]

        if not data_list:
            raise ValueError("Dataset loaded but contains no records.")

        # Write to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset saved to {output_file}")

        # Compute checksum
        checksum = compute_sha256(output_file)
        logger.info(f"SHA256 Checksum: {checksum}")

        # Optional: Write checksum to a sidecar file for T042b
        checksum_file = output_dir / "human_annotations.json.sha256"
        with open(checksum_file, 'w') as cf:
            cf.write(f"{checksum}  human_annotations.json\n")
        
        logger.info(f"Checksum saved to {checksum_file}")
        return output_file

    except Exception as e:
        # Fail loudly as per constraint
        raise RuntimeError(f"Gold Standard dataset not found. Cannot proceed with validation. Error: {e}")

def main():
    """CLI entry point."""
    logger.info("Starting Gold Standard Dataset download...")
    try:
        output_path = download_gold_standard()
        logger.info(f"Success: {output_path}")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
