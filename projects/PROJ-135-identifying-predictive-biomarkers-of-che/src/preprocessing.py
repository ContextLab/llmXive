"""
Preprocessing module for biomarker discovery pipeline.
Handles data harmonization, normalization, batch correction, and data splitting.
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Local imports from project API surface
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, ensure_path_exists

# Setup logging
logger = logging.getLogger(__name__)

# Constants
STRATIFY_COLUMN = 'response_label'
RANDOM_STATE = 42
DISCOVERY_RATIO = 0.7  # 70% discovery, 30% training
TUMOR_TYPE_COLUMN = 'tumor_type'
SAMPLE_ID_COLUMN = 'sample_id'
RESPONSE_COLUMN = 'response_label'


def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load batch-corrected processed data from CSV.

    Args:
        input_path: Path to the input CSV file

    Returns:
        DataFrame with processed data

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = [SAMPLE_ID_COLUMN, TUMOR_TYPE_COLUMN, RESPONSE_COLUMN]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} samples from {input_path}")
    return df


def split_data_stratified(
    df: pd.DataFrame,
    tumor_type: str,
    discovery_ratio: float = DISCOVERY_RATIO,
    random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data for a specific tumor type into discovery and training sets
    with stratification on response_label to maintain class distribution.

    Args:
        df: Full dataset DataFrame
        tumor_type: The tumor type to split
        discovery_ratio: Ratio of data to use for discovery set (default 0.7)
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (discovery_set, training_set) DataFrames

    Raises:
        ValueError: If tumor type not found or insufficient samples
    """
    # Filter for specific tumor type
    tumor_df = df[df[TUMOR_TYPE_COLUMN] == tumor_type].copy()

    if len(tumor_df) == 0:
        raise ValueError(f"No samples found for tumor type: {tumor_type}")

    # Check for stratification column
    if RESPONSE_COLUMN not in tumor_df.columns:
        raise ValueError(f"Response column '{RESPONSE_COLUMN}' not found in data")

    # Check minimum samples for split
    min_samples_per_class = 2
    class_counts = tumor_df[RESPONSE_COLUMN].value_counts()
    if (class_counts < min_samples_per_class).any():
        logger.warning(
            f"Tumor type {tumor_type} has classes with <{min_samples_per_class} samples. "
            f"Class distribution: {class_counts.to_dict()}"
        )

    # Perform stratified split
    try:
        discovery_set, training_set = train_test_split(
            tumor_df,
            test_size=(1 - discovery_ratio),
            stratify=tumor_df[RESPONSE_COLUMN],
            random_state=random_state
        )
    except ValueError as e:
        # Handle case where stratification fails due to small sample size
        if "The least populated class in y has only 1 member" in str(e):
            logger.warning(
                f"Stratification failed for {tumor_type} due to small sample size. "
                f"Performing non-stratified split. Error: {e}"
            )
            # Fallback to non-stratified split
            indices = tumor_df.index.tolist()
            np.random.seed(random_state)
            np.random.shuffle(indices)
            split_idx = int(len(indices) * discovery_ratio)
            discovery_indices = indices[:split_idx]
            training_indices = indices[split_idx:]

            discovery_set = tumor_df.loc[discovery_indices].copy()
            training_set = tumor_df.loc[training_indices].copy()
        else:
            raise

    logger.info(
        f"Split {tumor_type}: Discovery={len(discovery_set)}, Training={len(training_set)}, "
        f"Discovery response distribution: {discovery_set[RESPONSE_COLUMN].value_counts().to_dict()}, "
        f"Training response distribution: {training_set[RESPONSE_COLUMN].value_counts().to_dict()}"
    )

    return discovery_set.reset_index(drop=True), training_set.reset_index(drop=True)


def process_tumor_type_split(
    df: pd.DataFrame,
    tumor_type: str,
    output_dir: str
) -> Tuple[str, str]:
    """
    Process a single tumor type: split into discovery and training sets,
    then save to CSV files.

    Args:
        df: Full dataset DataFrame
        tumor_type: The tumor type to process
        output_dir: Directory to save output files

    Returns:
        Tuple of (discovery_path, training_path)

    Raises:
        ValueError: If processing fails
    """
    # Split data
    discovery_set, training_set = split_data_stratified(df, tumor_type)

    # Generate output paths
    discovery_path = os.path.join(output_dir, f"{tumor_type}_discovery_set.csv")
    training_path = os.path.join(output_dir, f"{tumor_type}_training_set.csv")

    # Save to CSV
    discovery_set.to_csv(discovery_path, index=False)
    training_set.to_csv(training_path, index=False)

    logger.info(f"Saved discovery set to: {discovery_path}")
    logger.info(f"Saved training set to: {training_path}")

    return discovery_path, training_path


def run_data_splitting(
    input_dir: str,
    output_dir: str,
    tumor_types: Optional[List[str]] = None
) -> Dict[str, Dict[str, str]]:
    """
    Main function to split all tumor type datasets into discovery and training sets.

    Args:
        input_dir: Directory containing batch-corrected CSV files
        output_dir: Directory to save split datasets
        tumor_types: Optional list of tumor types to process (if None, processes all found)

    Returns:
        Dictionary mapping tumor types to their output file paths
    """
    ensure_path_exists(output_dir)

    # Find input files if tumor_types not specified
    if tumor_types is None:
        input_files = [f for f in os.listdir(input_dir) if f.endswith('_batch_corrected.csv')]
        tumor_types = [f.replace('_batch_corrected.csv', '') for f in input_files]

    if not tumor_types:
        raise ValueError("No tumor types found to process")

    # Load all data
    all_data = []
    for tumor_type in tumor_types:
        input_path = os.path.join(input_dir, f"{tumor_type}_batch_corrected.csv")
        if os.path.exists(input_path):
            try:
                df = load_processed_data(input_path)
                all_data.append(df)
                logger.info(f"Loaded data for {tumor_type}: {len(df)} samples")
            except Exception as e:
                logger.error(f"Failed to load data for {tumor_type}: {e}")
        else:
            logger.warning(f"Input file not found for {tumor_type}: {input_path}")

    if not all_data:
        raise ValueError("No valid data loaded for any tumor type")

    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined_df)} samples across {len(tumor_types)} tumor types")

    # Process each tumor type
    results = {}
    for tumor_type in tumor_types:
        try:
            discovery_path, training_path = process_tumor_type_split(
                combined_df, tumor_type, output_dir
            )
            results[tumor_type] = {
                'discovery_set': discovery_path,
                'training_set': training_path
            }
        except Exception as e:
            logger.error(f"Failed to split data for {tumor_type}: {e}")
            results[tumor_type] = {'error': str(e)}

    # Write summary
    summary_path = os.path.join(output_dir, 'split_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Split summary written to: {summary_path}")

    return results


def main():
    """
    Main entry point for data splitting task.
    """
    # Setup logging
    setup_logging(level=logging.INFO)

    try:
        # Get project root and directories
        project_root = get_project_root()
        input_dir = os.path.join(project_root, 'data', 'processed')
        output_dir = os.path.join(project_root, 'data', 'processed')

        # Ensure output directory exists
        ensure_directories([output_dir])

        logger.info("Starting data splitting task (T020)")
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")

        # Run splitting
        results = run_data_splitting(input_dir, output_dir)

        # Report results
        success_count = sum(1 for r in results.values() if 'error' not in r)
        logger.info(f"Completed splitting for {success_count}/{len(results)} tumor types")

        if success_count == len(results):
            logger.info("Data splitting completed successfully")
            sys.exit(0)
        else:
            logger.warning(f"Some tumor types failed to split: {len(results) - success_count}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Data splitting failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
