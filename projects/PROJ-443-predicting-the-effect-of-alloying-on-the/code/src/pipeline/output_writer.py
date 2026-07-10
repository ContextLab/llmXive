"""
Output writer for the HEA Elastic Modulus prediction pipeline.
Handles writing the final processed dataset and source metadata.
"""
import os
import sys
import logging
import pandas as pd
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from utils.logging_config import get_logger
from utils.seeds import get_seed

logger = get_logger(__name__)


def write_processed_features(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the processed feature DataFrame to a CSV file.
    
    Args:
        df: The processed DataFrame containing features and targets.
        output_path: Path to the output CSV file.
    
    Raises:
        IOError: If the file cannot be written.
    """
    if df is None or df.empty:
        logger.error("Cannot write empty DataFrame to output.")
        raise ValueError("Input DataFrame is empty.")

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote processed features to {output_path}")
        logger.info(f"Shape: {df.shape}, Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to write features to {output_path}: {e}")
        raise


def write_source_metadata(
    run_metadata: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write the source metadata to a YAML file.
    
    This function implements FR-009 by recording provenance information
    including API versions, query parameters, and timestamps.
    
    Args:
        run_metadata: Dictionary containing run metadata.
        output_path: Path to the output YAML file.
    
    Raises:
        IOError: If the file cannot be written.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Add standard metadata fields if missing
    if "timestamp" not in run_metadata:
        run_metadata["timestamp"] = datetime.utcnow().isoformat()
    
    if "seed" not in run_metadata:
        run_metadata["seed"] = get_seed()

    try:
        with open(output_path, 'w') as f:
            yaml.dump(run_metadata, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully wrote source metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write metadata to {output_path}: {e}")
        raise


def main():
    """
    Main entry point for the output writer script.
    This is a utility script intended to be called by the main pipeline.
    """
    logger.info("Output Writer module loaded. Use write_processed_features and write_source_metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
