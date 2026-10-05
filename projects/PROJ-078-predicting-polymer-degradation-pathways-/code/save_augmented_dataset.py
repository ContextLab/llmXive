import os
import sys
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import from existing API surface
from utils import get_project_paths, get_logger, setup_logging

logger = setup_logging("save_augmented_dataset")

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Save the augmented dataset to the final location."""
    import argparse

    parser = argparse.ArgumentParser(description="Save augmented dataset")
    parser.add_argument("--input", type=str, required=True, help="Input augmented parquet file")
    parser.add_argument("--output", type=str, required=True, help="Output final parquet file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading augmented dataset from {args.input}")
    df = pd.read_parquet(args.input)

    logger.info(f"Saving final dataset to {args.output}")
    df.to_parquet(args.output, index=False)

    checksum = compute_file_checksum(args.output)

    results = {
        "record_count": len(df),
        "output_path": args.output,
        "checksum": checksum
    }

    logger.info(f"Dataset saved successfully: {results}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()