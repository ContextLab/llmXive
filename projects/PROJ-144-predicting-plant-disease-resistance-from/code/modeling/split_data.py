import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Import constants from the project's constants module
from utils.constants import (
    DATA_PROCESSED_DIR,
    RESULTS_DIR,
    HOLD_OUT_FRACTION,
    RANDOM_STATE
)
from utils.io import ensure_dirs, log_pipeline_status

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data():
    """
    Load the batch corrected matrix and harmonized labels.
    """
    matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    labels_path = os.path.join(DATA_PROCESSED_DIR, "labels.csv")

    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Input file not found: {matrix_path}. Run T017a first.")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Input file not found: {labels_path}. Run T017a first.")

    logger.info(f"Loading batch corrected matrix from {matrix_path}")
    X = pd.read_csv(matrix_path, index_col=0)

    logger.info(f"Loading labels from {labels_path}")
    y = pd.read_csv(labels_path, index_col=0)

    # Ensure alignment
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    # Identify the binary label column
    label_col = None
    possible_cols = ['binary_label', 'resistance_score', 'phenotype']
    for col in possible_cols:
        if col in y.columns:
            label_col = col
            break
    
    if label_col is None:
        raise ValueError(f"Could not find binary label column in {labels_path}. Expected one of {possible_cols}")

    y_binary = y[label_col]

    return X, y_binary

def split_data(X, y_binary):
    """
    Split data based on sample count N.
    If N >= 50: Stratified hold-out split.
    If N < 50: Learning curve configuration (no hold-out, prepare fractions).
    """
    N = len(X)
    logger.info(f"Total samples N = {N}")

    output_dir = DATA_PROCESSED_DIR
    ensure_dirs(output_dir)

    if N >= 50:
        logger.info(f"N >= 50. Performing stratified hold-out split (fraction={HOLD_OUT_FRACTION}).")
        
        train_indices, holdout_indices = train_test_split(
            X.index.tolist(),
            test_size=HOLD_OUT_FRACTION,
            stratify=y_binary,
            random_state=RANDOM_STATE
        )

        output_data = {
            "train_indices": train_indices,
            "holdout_indices": holdout_indices,
            "n_train": len(train_indices),
            "n_holdout": len(holdout_indices),
            "n_total": N,
            "method": "stratified_holdout"
        }
        
        output_path = os.path.join(output_dir, "split_indices.json")
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved split indices to {output_path}")
        return output_path

    else:
        logger.warning(f"N < 50 ({N}). Mandatory Learning Curve Analysis mode. Skipping hold-out set.")
        
        # Define subsample fractions for learning curve
        # Typically: 0.1, 0.2, 0.4, 0.6, 0.8, 1.0 or similar steps
        # Ensure we have at least a few points and include 1.0
        fractions = [0.1, 0.25, 0.5, 0.75, 1.0]
        
        output_data = {
            "fractions": fractions,
            "n_total": N,
            "method": "learning_curve_subsample",
            "note": "Hold-out set skipped due to small sample size (N < 50)."
        }

        output_path = os.path.join(output_dir, "learning_curve_config.json")
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved learning curve config to {output_path}")
        return output_path

def main():
    """
    Main entry point for T020a: Data Splitting & Learning Curve Setup.
    """
    try:
        ensure_dirs(DATA_PROCESSED_DIR)
        
        X, y_binary = load_processed_data()
        output_file = split_data(X, y_binary)
        
        log_pipeline_status(
            step="T020a_Data_Splitting",
            status="success",
            details={"output_file": output_file},
            logger=logger
        )
        
        logger.info("T020a completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data unavailable: {e}")
        log_pipeline_status(
            step="T020a_Data_Splitting",
            status="failed",
            details={"error": str(e)},
            logger=logger
        )
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T020a: {e}")
        log_pipeline_status(
            step="T020a_Data_Splitting",
            status="failed",
            details={"error": str(e)},
            logger=logger
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
