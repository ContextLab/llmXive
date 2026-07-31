"""
T021: Output descriptors to data/processed/descriptors.csv linked to original sample IDs.

This script reads the processed EBSD data (from T015) and the calculated descriptors
(from T018/T019/T020) and writes a consolidated CSV file linking descriptors to
their original sample IDs.

Dependencies:
- code/data/preprocess.py (for loading cleaned data)
- code/features/descriptors.py (for descriptor calculation)
- code/utils/logging.py (for logging)
- code/config.py (for configuration)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging
from config import get_data_path, get_reductions, get_seed
from data.preprocess import load_ebsd_data, process_ebsd_dataset
from features.descriptors import calculate_descriptors
from features.mass_balance import validate_dataset_mass_balance

# Setup logging
logger = setup_logging(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the cleaned EBSD data from the processed directory.
    Expects data/processed/cleaned_ebsd.parquet as per T015.
    """
    data_path = get_data_path()
    processed_dir = Path(data_path) / "processed"
    input_file = processed_dir / "cleaned_ebsd.parquet"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found: {input_file}. "
            "Run T015 (data acquisition/preprocessing) first."
        )

    logger.info(f"Loading cleaned data from {input_file}")
    df = pd.read_parquet(input_file)

    # Ensure required columns exist
    required_cols = ['sample_id', 'material', 'reduction', 'phi1', 'Phi', 'phi2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in cleaned data: {missing_cols}")

    logger.info(f"Loaded {len(df)} rows from {input_file}")
    return df

def calculate_and_export_descriptors(
    df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Calculate descriptors for each sample and export to CSV.

    Args:
        df: Cleaned EBSD DataFrame with columns: sample_id, material, reduction, phi1, Phi, phi2
        output_path: Path to write the descriptors CSV

    Returns:
        DataFrame of descriptors
    """
    logger.info("Starting descriptor calculation and export")

    # Group by sample_id to calculate descriptors per sample
    sample_groups = df.groupby('sample_id')
    all_descriptors = []

    for sample_id, group in sample_groups:
        try:
            # Extract orientation data for this sample
            orientations = group[['phi1', 'Phi', 'phi2']].values

            # Get sample metadata
            material = group['material'].iloc[0]
            reduction = group['reduction'].iloc[0]

            # Calculate descriptors
            desc_dict = calculate_descriptors(
                orientations=orientations,
                material=material,
                reduction=reduction
            )

            # Add sample ID and metadata
            desc_dict['sample_id'] = sample_id
            desc_dict['material'] = material
            desc_dict['reduction'] = reduction
            desc_dict['num_points'] = len(group)

            all_descriptors.append(desc_dict)

        except Exception as e:
            logger.error(f"Error calculating descriptors for sample {sample_id}: {e}")
            # Continue processing other samples
            continue

    if not all_descriptors:
        raise RuntimeError("No descriptors were calculated. Check input data and descriptor logic.")

    # Create DataFrame
    descriptors_df = pd.DataFrame(all_descriptors)

    # Validate mass balance across the dataset
    logger.info("Validating mass balance across dataset")
    try:
        validate_dataset_mass_balance(descriptors_df)
        logger.info("Mass balance validation passed")
    except Exception as e:
        logger.warning(f"Mass balance validation warning: {e}")

    # Sort by sample_id for consistent output
    descriptors_df = descriptors_df.sort_values('sample_id')

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptors_df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(descriptors_df)} samples to {output_path}")

    return descriptors_df

def main():
    """Main entry point for T021."""
    logger.info("Starting T021: Export descriptors to CSV")

    # Get paths from config
    data_path = get_data_path()
    output_file = Path(data_path) / "processed" / "descriptors.csv"

    # Load processed data
    df = load_processed_data()

    # Calculate and export descriptors
    descriptors_df = calculate_and_export_descriptors(df, output_file)

    # Print summary
    logger.info("T021 completed successfully")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Total samples: {len(descriptors_df)}")
    logger.info(f"Columns: {list(descriptors_df.columns)}")

    return output_file

if __name__ == "__main__":
    main()