"""
Data loading module for the Musical Training Connectivity project.
Handles loading of real data (Analysis Mode) or synthetic data (Verification Mode).
"""

import os
import pandas as pd
from typing import Optional

# Import from existing API surface
from utils.logging import get_logger
from data.models import Subject, create_subjects_from_dataframe
from data.synthetic_generator import generate_synthetic_dataset

logger = get_logger(__name__)


class DataAccessError(Exception):
    """Raised when data access fails due to missing sources or invalid paths."""
    pass


def load_data(path: str, mode: str) -> pd.DataFrame:
    """
    Load data based on the specified mode.

    Args:
        path (str): Path to the data file or directory.
        mode (str): 'analysis' for real data, 'verification' for synthetic data.

    Returns:
        pd.DataFrame: Loaded and validated dataset.

    Raises:
        DataAccessError: If real data is required but missing or invalid.
        ValueError: If data does not meet minimum subject count requirements.
    """
    logger.info(f"Loading data in mode: {mode} from path: {path}")

    df: Optional[pd.DataFrame] = None

    if mode == 'analysis':
        # Attempt to load real data
        if not os.path.exists(path):
            raise DataAccessError(
                f"Data Source Missing: Real data required for Analysis Mode. "
                f"Path not found: {path}"
            )

        try:
            # Determine file type and load
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            elif path.endswith('.parquet'):
                df = pd.read_parquet(path)
            elif path.endswith('.npy'):
                # Assuming a structured array or dict of arrays
                import numpy as np
                data = np.load(path, allow_pickle=True).item()
                df = pd.DataFrame(data)
            else:
                raise DataAccessError(
                    f"Unsupported file format for Analysis Mode: {path}. "
                    "Supported formats: .csv, .parquet, .npy"
                )

            logger.info(f"Successfully loaded real data from {path}. Shape: {df.shape}")

        except Exception as e:
            raise DataAccessError(f"Failed to load real data from {path}: {str(e)}") from e

    elif mode == 'verification':
        # Generate synthetic data for verification
        logger.info("Generating synthetic dataset for verification mode.")
        try:
            # Generate synthetic data using the existing generator
            # We pass the path as a seed or base directory if needed, 
            # but primarily rely on the generator's internal logic.
            df = generate_synthetic_dataset(seed=42, n_subjects=200)
            logger.info(f"Successfully generated synthetic data. Shape: {df.shape}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate synthetic data: {str(e)}") from e
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'analysis' or 'verification'.")

    # Mandatory Check: Minimum subject count per group
    # This check applies to BOTH synthetic and real data sources.
    # Required for US-1 Acceptance Scenario 1.
    musician_count = len(df[df['group'] == 'musician'])
    non_musician_count = len(df[df['group'] == 'non_musician'])

    logger.info(f"Subject counts - Musician: {musician_count}, Non-musician: {non_musician_count}")

    if musician_count < 50 or non_musician_count < 50:
        raise ValueError(
            f"Insufficient Data for Power: <50 subjects per group. "
            f"Found {musician_count} musicians and {non_musician_count} non-musicians."
        )

    logger.info("Data validation passed: Minimum subject count requirements met.")
    return df