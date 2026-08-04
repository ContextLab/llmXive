"""
Module to save raw p-values to results/p_values/raw_p_values.csv.
This module depends on the output of the permutation test (null distributions)
and the p-value calculation logic in p_values.py.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional

from config import RESULTS_DIR
from p_values import process_null_distributions

logger = logging.getLogger(__name__)

RAW_P_VALUES_FILE = os.path.join(RESULTS_DIR, "p_values", "raw_p_values.csv")

def ensure_p_values_dir():
    """Ensure the p_values directory exists."""
    p_values_dir = os.path.dirname(RAW_P_VALUES_FILE)
    if not os.path.exists(p_values_dir):
        os.makedirs(p_values_dir)
        logger.info(f"Created directory: {p_values_dir}")

def save_raw_p_values(p_values_data: List[Dict[str, Any]]):
    """
    Save raw p-values to a CSV file.

    Args:
        p_values_data: List of dictionaries containing query_id, metric, and raw_p_value.
    """
    ensure_p_values_dir()

    if not p_values_data:
        logger.warning("No p-values data to save.")
        return

    logger.info(f"Saving {len(p_values_data)} raw p-values to {RAW_P_VALUES_FILE}")

    with open(RAW_P_VALUES_FILE, 'w', newline='') as csvfile:
        fieldnames = ['query_id', 'metric', 'raw_p_value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in p_values_data:
            writer.writerow(row)

    logger.info(f"Successfully saved raw p-values to {RAW_P_VALUES_FILE}")

def run_p_values_saving():
    """
    Main entry point to load null distributions, calculate p-values, and save them.
    This function orchestrates the process of generating and saving raw p-values.
    """
    logger.info("Starting raw p-values generation and saving process.")

    # Process null distributions to get p-values
    # This assumes null distributions have been saved by the permutation module
    # and are located in RESULTS_DIR/null_distributions/
    p_values_list = process_null_distributions()

    if not p_values_list:
        logger.error("No p-values were calculated. Check if null distributions exist.")
        return

    # Save the calculated p-values
    save_raw_p_values(p_values_list)

    logger.info("Raw p-values generation and saving completed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_p_values_saving()