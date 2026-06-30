"""
T045: Implement conditional bootstrap reduction logic.

This script implements the logic to reduce bootstrap iterations to 500
if the dataset size exceeds 5000 rows, while preserving the minimum
iterations required by Constitution Principle VI (default 1000 for smaller datasets).

It reads the existing bootstrap analysis configuration, applies the conditional
logic, and updates the configuration or logs the applied strategy.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

import numpy as np

# Import existing utilities and config
from utils import setup_logging, pin_random_seed
from config import get_config

# Constants
DEFAULT_BOOTSTRAP_ITERATIONS = 1000
LARGE_DATASET_THRESHOLD = 5000
REDUCED_BOOTSTRAP_ITERATIONS = 500
MIN_BOOTSTRAP_ITERATIONS = 100  # Constitution Principle VI minimum

# Paths
PROCESSED_DIR = "data/processed"
CONFIG_PATH = "config/bootstrap_config.json"

def determine_bootstrap_iterations(dataset_size: int, requested_iterations: Optional[int] = None) -> int:
    """
    Determine the number of bootstrap iterations based on dataset size.

    Logic:
    1. If dataset_size > 5000, use 500 iterations (reduced for performance).
    2. If dataset_size <= 5000, use requested_iterations or default (1000).
    3. Ensure the result is never below the Constitution Principle VI minimum (100).

    Args:
        dataset_size (int): Number of rows in the dataset.
        requested_iterations (Optional[int]): User-specified iterations from config/env.

    Returns:
        int: The final number of iterations to use.
    """
    # Start with the requested or default value
    base_iterations = requested_iterations if requested_iterations is not None else DEFAULT_BOOTSTRAP_ITERATIONS

    # Apply the conditional reduction logic
    if dataset_size > LARGE_DATASET_THRESHOLD:
        final_iterations = REDUCED_BOOTSTRAP_ITERATIONS
        reason = f"Dataset size ({dataset_size}) > {LARGE_DATASET_THRESHOLD}. Reducing to {REDUCED_BOOTSTRAP_ITERATIONS}."
    else:
        final_iterations = base_iterations
        reason = f"Dataset size ({dataset_size}) <= {LARGE_DATASET_THRESHOLD}. Using requested/default ({base_iterations})."

    # Enforce Constitution Principle VI minimum
    if final_iterations < MIN_BOOTSTRAP_ITERATIONS:
        logging.warning(
            f"Calculated iterations ({final_iterations}) below Constitution Principle VI minimum "
            f"({MIN_BOOTSTRAP_ITERATIONS}). Raising to minimum."
        )
        final_iterations = MIN_BOOTSTRAP_ITERATIONS
        reason += f" Raised to minimum {MIN_BOOTSTRAP_ITERATIONS}."

    logging.info(f"Bootstrap iteration decision: {reason}")
    return final_iterations

def load_dataset_size_from_metrics(metrics_path: str) -> int:
    """
    Load a dataset size from a metrics JSON file.
    Expects the file to contain a 'dataset_size' or 'n_rows' field.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    with open(metrics_path, 'r') as f:
        data = json.load(f)

    size = data.get('dataset_size') or data.get('n_rows')
    if size is None:
        # Fallback: try to infer from other fields if possible, or raise
        raise ValueError(f"Could not find 'dataset_size' or 'n_rows' in {metrics_path}")

    return int(size)

def run_bootstrap_reduction_check():
    """
    Main execution function for T045.
    Iterates through processed metrics files to determine and log bootstrap iterations.
    """
    setup_logging("INFO")
    pin_random_seed(get_config().RANDOM_SEED)

    logging.info("Starting T045: Conditional Bootstrap Reduction Logic Check")

    # Ensure processed directory exists
    if not os.path.exists(PROCESSED_DIR):
        logging.warning(f"Directory {PROCESSED_DIR} does not exist. No metrics to check.")
        return

    # Find all JSON metrics files (excluding specific large reports if needed)
    metrics_files = [
        f for f in os.listdir(PROCESSED_DIR)
        if f.endswith('.json') and not f.startswith('null_')
    ]

    if not metrics_files:
        logging.info("No metrics files found in data/processed.")
        return

    results = []

    for filename in metrics_files:
        filepath = os.path.join(PROCESSED_DIR, filename)
        try:
            dataset_size = load_dataset_size_from_metrics(filepath)
            # Check config for any override, else use default
            config = get_config()
            requested_iters = getattr(config, 'BOOTSTRAP_ITERATIONS', None)
            
            # If config is an int, use it; if it's a string, try to parse
            if isinstance(requested_iters, str):
                try:
                    requested_iters = int(requested_iters)
                except ValueError:
                    requested_iters = None
            elif not isinstance(requested_iters, int):
                requested_iters = None

            final_iters = determine_bootstrap_iterations(dataset_size, requested_iters)
            
            results.append({
                "file": filename,
                "dataset_size": dataset_size,
                "requested_iterations": requested_iters,
                "final_iterations": final_iters,
                "reduction_applied": final_iters < (requested_iters or DEFAULT_BOOTSTRAP_ITERATIONS)
            })

        except (FileNotFoundError, ValueError) as e:
            logging.warning(f"Skipping {filename}: {e}")
            continue

    # Summary
    logging.info(f"Processed {len(results)} metrics files.")
    reduced_count = sum(1 for r in results if r['reduction_applied'])
    if reduced_count > 0:
        logging.info(f"Bootstrap reduction applied to {reduced_count} datasets.")
    else:
        logging.info("No bootstrap reductions necessary for current datasets.")

    # Save a log of the decisions
    output_path = os.path.join(PROCESSED_DIR, 'bootstrap_reduction_log.json')
    with open(output_path, 'w') as f:
        json.dump({
            "timestamp": str(__import__('datetime').datetime.now()),
            "threshold": LARGE_DATASET_THRESHOLD,
            "reduced_value": REDUCED_BOOTSTRAP_ITERATIONS,
            "min_value": MIN_BOOTSTRAP_ITERATIONS,
            "decisions": results
        }, f, indent=2)
    
    logging.info(f"Bootstrap reduction decisions saved to {output_path}")

def main():
    """Entry point."""
    run_bootstrap_reduction_check()

if __name__ == "__main__":
    main()