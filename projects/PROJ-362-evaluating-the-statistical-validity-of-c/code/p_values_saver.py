import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

def ensure_p_values_dir() -> Path:
    """Ensure the p-values output directory exists."""
    p_values_dir = RESULTS_DIR / "p_values"
    ensure_dirs(p_values_dir)
    return p_values_dir

def save_raw_p_values(p_values: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save raw p-values to a CSV file.

    Args:
        p_values: List of dictionaries containing 'query_id', 'metric', 'raw_p'.
        output_path: Optional specific path to save the file. Defaults to RESULTS_DIR/p_values/raw_p_values.csv.

    Returns:
        The path to the saved CSV file.
    """
    if output_path is None:
        p_values_dir = ensure_p_values_dir()
        output_path = p_values_dir / "raw_p_values.csv"

    logger.info(f"Saving {len(p_values)} raw p-values to {output_path}")

    if not p_values:
        logger.warning("No p-values to save. Creating empty file with headers.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p'])
        return output_path

    # Determine columns based on the first item to ensure consistency
    # Expected keys: query_id, metric, raw_p
    fieldnames = ['query_id', 'metric', 'raw_p']

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in p_values:
            # Ensure we only write the expected columns
            filtered_row = {k: row.get(k) for k in fieldnames}
            writer.writerow(filtered_row)

    logger.info(f"Successfully saved raw p-values to {output_path}")
    return output_path

def run_p_values_saving(p_values: List[Dict[str, Any]]) -> Path:
    """
    Entry point for saving raw p-values.

    Args:
        p_values: List of dictionaries containing 'query_id', 'metric', 'raw_p'.

    Returns:
        The path to the saved CSV file.
    """
    return save_raw_p_values(p_values)