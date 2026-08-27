"""
T023: Save feature matrix to data/processed/features_matrix.csv.

This script loads the computed features from the feature extraction pipeline
and saves them as a CSV file with dimensions (epochs × features).
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

from config import load_config, get_paths
from feature_extraction import run_extraction
from feature_validation import validate_features
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end

logger = get_pipeline_logger(__name__)


def save_feature_matrix(features: Dict[str, Any], output_path: Path) -> None:
    """
    Save the feature matrix to a CSV file.

    Args:
        features: Dictionary containing 'matrix' (np.ndarray), 'labels' (List[str]),
                  and 'epoch_ids' (List[str]).
        output_path: Path where the CSV file will be saved.
    """
    matrix = features['matrix']
    labels = features['labels']
    epoch_ids = features['epoch_ids']

    if matrix.shape[0] != len(epoch_ids):
        raise ValueError(
            f"Number of rows ({matrix.shape[0]}) does not match number of epoch IDs ({len(epoch_ids)})"
        )

    if matrix.shape[1] != len(labels):
        raise ValueError(
            f"Number of columns ({matrix.shape[1]}) does not match number of feature labels ({len(labels)})"
        )

    # Create DataFrame
    df = pd.DataFrame(matrix, columns=labels)
    df.insert(0, 'epoch_id', epoch_ids)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature matrix to {output_path}")
    logger.info(f"Dimensions: {df.shape[0]} epochs × {df.shape[1] - 1} features")


def main() -> None:
    """Main entry point for T023."""
    log_stage_start("T023 - Save Feature Matrix")

    config = load_config()
    paths = get_paths(config)
    output_path = paths['processed_dir'] / 'features_matrix.csv'

    logger.info(f"Output path: {output_path}")

    # Run feature extraction (which loads epochs and computes features)
    # This ensures we have the real features to save
    features = run_extraction(config)

    # Validate features before saving
    validation_result = validate_features(features)
    if not validation_result['valid']:
        logger.error(f"Feature validation failed: {validation_result['issues']}")
        raise RuntimeError("Feature validation failed. Aborting save.")

    # Save the feature matrix
    save_feature_matrix(features, output_path)

    log_stage_end("T023 - Save Feature Matrix")
    logger.info("T023 completed successfully")


if __name__ == '__main__':
    main()
