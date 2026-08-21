"""
Module to save raw p-values generated from permutation tests.
Handles the final step of User Story 1: saving p-values to CSV.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import from project config
try:
    from config import RESULTS_DIR, ensure_dirs
except ImportError:
    # Fallback for standalone execution if config is not in path
    from pathlib import Path
    RESULTS_DIR = Path("results")
    def ensure_dirs():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / "p_values").mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def ensure_p_values_dir():
    """Ensure the directory for raw p-values exists."""
    p_values_dir = RESULTS_DIR / "p_values"
    p_values_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured p-values directory exists: {p_values_dir}")
    return p_values_dir

def save_raw_p_values(p_values: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save raw p-values to a CSV file.

    Args:
        p_values: List of dictionaries containing query_id, metric, and p_value.
        output_path: Optional specific path to save to. Defaults to results/p_values/raw_p_values.csv.
    """
    if output_path is None:
        ensure_p_values_dir()
        output_path = RESULTS_DIR / "p_values" / "raw_p_values.csv"

    logger.info(f"Saving {len(p_values)} raw p-values to {output_path}")

    if not p_values:
        logger.warning("No p-values to save. Creating empty file with headers.")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'p_value'])
        return

    # Determine headers based on keys in the first item, or standard set
    headers = ['query_id', 'metric', 'p_value']
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(p_values)
        
        logger.info(f"Successfully saved raw p-values to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save p-values to {output_path}: {e}")
        raise

def run_p_values_saving(p_values: List[Dict[str, Any]]):
    """
    Entry point for saving p-values, typically called by main.py.
    """
    ensure_p_values_dir()
    output_path = RESULTS_DIR / "p_values" / "raw_p_values.csv"
    save_raw_p_values(p_values, output_path)
    return output_path
