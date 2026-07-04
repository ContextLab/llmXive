"""
Data loading and verification module for the Cognitive Load Optimization project.

This module handles fetching public datasets (ASSISTments, OULAD) from HuggingFace,
verifying the presence of required interaction features, and saving processed data.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_directories() -> Dict[str, Path]:
    """
    Ensure all required data directories exist.

    Returns:
        Dict mapping directory names to Path objects.
    """
    base_dirs = {
        'raw': Path('data/raw'),
        'processed': Path('data/processed'),
        'explanation_tiers': Path('data/explanation_tiers'),
        'simulation_results': Path('data/simulation_results')
    }

    for name, path in base_dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {path}")

    return base_dirs


def load_assistments_dataset() -> Optional[pd.DataFrame]:
    """
    Load the ASSISTments 2017 dataset from HuggingFace.

    Returns:
        DataFrame with interaction data, or None if loading fails.
    """
    try:
        # Correct dataset identifier for ASSISTments 2017
        dataset = load_dataset("assistments/2017")
        logger.info("Successfully loaded ASSISTments 2017 dataset")

        # The dataset is usually split into train/test or just 'train'
        if 'train' in dataset:
            df = dataset['train'].to_pandas()
        elif 'test' in dataset:
            df = dataset['test'].to_pandas()
        else:
            # Fallback: try to get the first split
            first_split = list(dataset.keys())[0]
            df = dataset[first_split].to_pandas()

        logger.info(f"ASSISTments dataset shape: {df.shape}")
        logger.info(f"ASSISTments columns: {list(df.columns)}")

        return df
    except Exception as e:
        logger.error(f"Failed to load ASSISTments dataset: {e}")
        return None


def load_oulad_dataset() -> Optional[pd.DataFrame]:
    """
    Load the OULAD (Open University Learning Analytics Dataset) from HuggingFace.

    Returns:
        DataFrame with interaction data, or None if loading fails.
    """
    try:
        # Correct dataset identifier for OULAD
        dataset = load_dataset("openlearning/openlearning")
        logger.info("Successfully loaded OULAD dataset")

        # OULAD typically has a 'train' split
        if 'train' in dataset:
            df = dataset['train'].to_pandas()
        else:
            # Fallback
            first_split = list(dataset.keys())[0]
            df = dataset[first_split].to_pandas()

        logger.info(f"OULAD dataset shape: {df.shape}")
        logger.info(f"OULAD columns: {list(df.columns)}")

        return df
    except Exception as e:
        logger.error(f"Failed to load OULAD dataset: {e}")
        return None


def verify_features(df: pd.DataFrame, dataset_name: str) -> bool:
    """
    Verify the presence of required interaction features in the dataset.

    Required features:
    - Timestamped responses (e.g., 'timestamp', 'date', 'start_time')
    - Error logs (e.g., 'is_correct', 'score', 'answer')
    - Hint requests (e.g., 'num_hints', 'hint_count')
    - Interaction features (e.g., 'step_id', 'problem_id', 'course_id')

    Args:
        df: DataFrame to verify.
        dataset_name: Name of the dataset for logging purposes.

    Returns:
        True if all required features are present, False otherwise.
    """
    logger.info(f"Verifying features for {dataset_name}...")

    # Define required feature categories with possible column names
    required_features = {
        'timestamp': ['timestamp', 'date', 'start_time', 'time', 'datetime'],
        'error_log': ['is_correct', 'score', 'answer', 'correct'],
        'hint_request': ['num_hints', 'hint_count', 'hints', 'num_hints_given'],
        'interaction': ['step_id', 'problem_id', 'course_id', 'question_id']
    }

    found_features = {}
    missing_features = []

    for category, possible_names in required_features.items():
        found = False
        for name in possible_names:
            if name in df.columns:
                found = True
                found_features[category] = name
                break

        if found:
            logger.info(f"  Found {category}: {found_features[category]}")
        else:
            missing_features.append(category)
            logger.warning(f"  Missing {category} (tried: {possible_names})")

    if missing_features:
        logger.error(f"{dataset_name} is missing required feature categories: {missing_features}")
        return False

    logger.info(f"{dataset_name} feature verification PASSED")
    return True


def save_dataset(df: pd.DataFrame, filename: str, directory: Path) -> Path:
    """
    Save a DataFrame to a CSV file in the specified directory.

    Args:
        df: DataFrame to save.
        filename: Name of the output file.
        directory: Directory to save the file in.

    Returns:
        Path to the saved file.
    """
    output_path = directory / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved dataset to {output_path}")
    return output_path


def load_and_verify_datasets() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load both ASSISTments and OULAD datasets and verify their features.

    Returns:
        Tuple of (assistments_df, oulad_df). Either can be None if loading failed.
    """
    # Ensure directories exist
    dirs = ensure_directories()

    # Load ASSISTments
    assistments_df = load_assistments_dataset()
    if assistments_df is not None:
        if verify_features(assistments_df, "ASSISTments"):
            save_dataset(assistments_df, 'assistments_raw.csv', dirs['raw'])
        else:
            logger.warning("ASSISTments dataset missing required features. Skipping save.")
            assistments_df = None
    else:
        logger.warning("Failed to load ASSISTments dataset.")

    # Load OULAD
    oulad_df = load_oulad_dataset()
    if oulad_df is not None:
        if verify_features(oulad_df, "OULAD"):
            save_dataset(oulad_df, 'oulad_raw.csv', dirs['raw'])
        else:
            logger.warning("OULAD dataset missing required features. Skipping save.")
            oulad_df = None
    else:
        logger.warning("Failed to load OULAD dataset.")

    return assistments_df, oulad_df


def validate_golden_set() -> bool:
    """
    Check for the presence of the Golden Set file with required columns.

    The Golden Set must be at data/processed/golden_set.csv and contain
    either 'expert_load_score' or 'self_report_load' columns.

    Returns:
        True if Golden Set is valid, False otherwise.
    """
    golden_set_path = Path('data/processed/golden_set.csv')

    if not golden_set_path.exists():
        logger.error("Golden Set file not found at data/processed/golden_set.csv")
        return False

    try:
        df = pd.read_csv(golden_set_path)
        logger.info(f"Golden Set loaded with shape: {df.shape}")

        required_cols = ['expert_load_score', 'self_report_load']
        has_valid_col = any(col in df.columns for col in required_cols)

        if not has_valid_col:
            logger.error(f"Golden Set missing required columns. Found: {list(df.columns)}")
            return False

        logger.info("Golden Set validation PASSED")
        return True
    except Exception as e:
        logger.error(f"Error validating Golden Set: {e}")
        return False


def main():
    """
    Main entry point for data loading and verification.
    """
    logger.info("Starting data loading and verification process...")

    # Load and verify datasets
    assistments_df, oulad_df = load_and_verify_datasets()

    # Validate Golden Set
    golden_set_valid = validate_golden_set()

    if not golden_set_valid:
        logger.error("Golden Set validation failed. The pipeline cannot proceed without a valid Golden Set.")
        # Note: T005 will handle the specific exit logic for missing Golden Set
        # Here we just log the error for now.

    # Summary
    logger.info("Data loading summary:")
    logger.info(f"  ASSISTments: {'Loaded' if assistments_df is not None else 'Failed'}")
    logger.info(f"  OULAD: {'Loaded' if oulad_df is not None else 'Failed'}")
    logger.info(f"  Golden Set: {'Valid' if golden_set_valid else 'Invalid/Missing'}")

    return assistments_df, oulad_df, golden_set_valid


if __name__ == "__main__":
    main()
