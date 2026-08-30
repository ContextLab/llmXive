"""
Script to download the LoCoMo benchmark dataset from HuggingFace.

This script implements Task T011a:
- Calls load_locomo_strict() to fetch the dataset.
- Validates the schema (columns: question, context, answer).
- Saves the output to data/raw/locomo.jsonl.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_locomo_strict, ensure_output_dirs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for downloading the LoCoMo benchmark.
    """
    output_dir = Path("data/raw")
    output_file = output_dir / "locomo.jsonl"

    logger.info(f"Ensuring output directory exists: {output_dir}")
    ensure_output_dirs([output_dir])

    logger.info("Loading LoCoMo dataset strictly (no synthetic fallback)...")
    try:
        dataset = load_locomo_strict()
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Convert dataset to list of dicts for easier handling
    # The dataset object from datasets library usually supports iteration
    logger.info(f"Dataset loaded. Number of rows: {len(dataset)}")

    # Validate schema
    required_columns = {"question", "context", "answer"}
    if hasattr(dataset, "column_names"):
        actual_columns = set(dataset.column_names)
    else:
        # Fallback if it's a list of dicts
        if len(dataset) > 0:
            actual_columns = set(dataset[0].keys())
        else:
            actual_columns = set()

    missing_columns = required_columns - actual_columns
    if missing_columns:
        error_msg = f"Dataset schema mismatch. Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Schema validation passed. Found columns: {actual_columns}")

    # Write to JSONL
    logger.info(f"Writing {len(dataset)} rows to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        for idx, item in enumerate(dataset):
            # Ensure we only write the required columns to keep the file clean
            row = {
                "question": item.get("question", ""),
                "context": item.get("context", ""),
                "answer": item.get("answer", "")
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if idx % 100 == 0:
                logger.info(f"  Processed {idx}/{len(dataset)} rows...")

    logger.info(f"Successfully downloaded and saved LoCoMo benchmark to {output_file}")
    return output_file

if __name__ == "__main__":
    main()
