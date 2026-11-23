import os
import sys
import logging
import time
from typing import Optional, Tuple

# Add parent to path to resolve imports relative to code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasets import load_dataset
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, get_logger
import pandas as pd
import psutil

def setup_script_logging():
    """Initialize logging for the download script."""
    logger = setup_logging("download_data")
    return logger

def download_qm9_subset(logger: logging.Logger, output_path: str, subset_size: int = 10000):
    """
    Stream QM9 from torch_geometric.datasets.QM9 (via HuggingFace datasets)
    to a local parquet file.

    We use the 'qm9' dataset from HuggingFace which mirrors the QM9 dataset.
    We stream it to avoid loading the full dataset into memory, select a subset,
    and save it as a parquet file.

    Args:
        logger: Logger instance.
        output_path: Path to save the parquet file.
        subset_size: Number of molecules to include in the subset.
    """
    logger.info(f"Starting QM9 download and streaming to {output_path}")
    logger.info(f"Target subset size: {subset_size} molecules")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Load QM9 dataset from HuggingFace.
        # Note: The 'qm9' dataset in HF is a direct mirror of the QM9 dataset.
        # We use streaming=True to avoid downloading the full dataset into memory.
        logger.info("Streaming QM9 dataset from HuggingFace...")
        dataset = load_dataset("qm9", split="train", streaming=True)

        logger.info("Collecting subset...")
        count = 0
        data_rows = []

        # Iterate through the dataset and collect 'subset_size' rows
        for item in dataset:
            if count >= subset_size:
                break

            # QM9 dataset structure in HF typically includes:
            # 'smiles', 'target' (list of properties), 'mol' (rdkit mol object if available, but usually we reconstruct)
            # We specifically need SMILES and potentially the target properties.
            # The HF 'qm9' dataset has a 'smiles' column and 'target' column (list of floats).
            # We will store SMILES and the target properties.

            smiles = item.get('smiles')
            if not smiles:
                logger.warning(f"Skipping row {count}: missing SMILES")
                continue

            # Extract target properties (DFT calculations)
            # The 'target' column usually contains 19 properties.
            # We'll store them as separate columns or a JSON string if needed.
            # For simplicity in this subset, we'll store the first few relevant ones or all.
            # Let's assume we want the full target vector for now.
            targets = item.get('target', [])

            # Construct a dictionary for the row
            row = {'smiles': smiles, 'target': targets}
            data_rows.append(row)
            count += 1

            if count % 1000 == 0:
                logger.info(f"Collected {count} molecules...")

        if count == 0:
            raise RuntimeError("Failed to retrieve any molecules from the QM9 dataset.")

        logger.info(f"Successfully collected {count} molecules.")

        # Convert to DataFrame
        df = pd.DataFrame(data_rows)

        # Save to parquet
        logger.info(f"Writing {count} rows to {output_path}")
        df.to_parquet(output_path, index=False)

        logger.info("Download and save completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during QM9 download/streaming: {e}", exc_info=True)
        raise

def main():
    """Main entry point for the QM9 download script."""
    logger = setup_script_logging()
    config = get_config()

    # Define output path based on config or default
    # The task specifies: data/raw/qm9_subset.parquet
    output_path = os.path.join(config.get('data_dir', 'data'), 'raw', 'qm9_subset.parquet')
    
    # Ensure directories exist
    ensure_directories(config)

    # Default subset size (can be overridden by config if needed)
    subset_size = config.get('qm9_subset_size', 10000)

    try:
        success = download_qm9_subset(logger, output_path, subset_size)
        if success:
            logger.info(f"QM9 subset successfully saved to {output_path}")
            # Log the event
            log_metric("qm9_download", "success", {"output_path": output_path, "count": subset_size})
        else:
            logger.error("QM9 download failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
