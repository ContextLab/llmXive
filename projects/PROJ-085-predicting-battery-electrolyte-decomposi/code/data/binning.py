"""
Bin assignment logic for decomposition energy analysis.

This module implements the stratification logic to split data into 'Low' and 'High'
voltage bins based on the potential (phi) values.

Deviation Note: The spec's '3-5V' range requirement is explicitly mapped to the
available 4V data point due to data constraints.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import pandas as pd
import numpy as np

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging_config import get_logger
from config import get_data_dir, get_output_dir

logger = get_logger(__name__)

# Constants for binning
# Low voltage: 0V to 2V (inclusive)
# High voltage: 4V (representing the 3-5V range per deviation note)
LOW_VOLTAGE_THRESHOLD = 2.0  # V
HIGH_VOLTAGE_TARGET = 4.0    # V

def load_processed_features() -> pd.DataFrame:
    """
    Load the processed feature matrix from data/processed/electrolyte_features.csv.

    Returns:
        pd.DataFrame: The feature matrix with at least 'molecule_id', 'potential_v',
                      and calculated target columns.

    Raises:
        FileNotFoundError: If the processed features file does not exist.
    """
    data_dir = get_data_dir()
    input_path = data_dir / "processed" / "electrolyte_features.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed features file not found at {input_path}. "
            "Please ensure T018 (split_data) has been run successfully."
        )

    logger.info(f"Loading processed features from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['molecule_id', 'potential_v']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Input file missing required columns: {missing_cols}. "
            f"Found: {list(df.columns)}"
        )

    return df

def assign_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign 'Low' or 'High' bin labels based on potential_v.

    Logic:
    - 'Low': potential_v <= LOW_VOLTAGE_THRESHOLD (0V, 2V)
    - 'High': potential_v == HIGH_VOLTAGE_TARGET (4V)
    
    Deviation Note: The spec's '3-5V' range is mapped to the single 4V data point.
    Any potential not matching Low or High criteria will be flagged as 'Unknown'.

    Args:
        df (pd.DataFrame): Input dataframe with 'potential_v' column.

    Returns:
        pd.DataFrame: DataFrame with an added 'bin' column.
    """
    def classify_potential(phi: float) -> str:
        if pd.isna(phi):
            return 'Unknown'
        if phi <= LOW_VOLTAGE_THRESHOLD:
            return 'Low'
        elif abs(phi - HIGH_VOLTAGE_TARGET) < 1e-6: # Floating point safe comparison
            return 'High'
        else:
            return 'Unknown'

    logger.info(f"Assigning bins: Low (<= {LOW_VOLTAGE_THRESHOLD}V), High (~{HIGH_VOLTAGE_TARGET}V)")
    
    df['bin'] = df['potential_v'].apply(classify_potential)
    
    # Log distribution
    bin_counts = df['bin'].value_counts()
    logger.info(f"Bin distribution:\n{bin_counts}")
    
    unknown_count = len(df[df['bin'] == 'Unknown'])
    if unknown_count > 0:
        logger.warning(f"Found {unknown_count} rows with 'Unknown' bin status (potential not in expected ranges).")

    return df

def save_bins(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the bin assignments to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame containing the 'bin' column.
        output_path (Optional[Path]): Path to save the CSV. If None, uses default path.

    Returns:
        Path: The path where the file was saved.
    """
    if output_path is None:
        output_dir = get_output_dir()
        output_path = output_dir / "processed" / "bins.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Select relevant columns for output
    output_cols = ['molecule_id', 'potential_v', 'bin']
    # Check if all columns exist, if not just use what's available + bin
    available_cols = [c for c in output_cols if c in df.columns]
    if 'bin' not in available_cols:
        available_cols.append('bin')
        
    df[available_cols].to_csv(output_path, index=False)
    logger.info(f"Saved bin assignments to {output_path}")
    
    return output_path

def run_binning_pipeline() -> Tuple[pd.DataFrame, Path]:
    """
    Main entry point for the binning pipeline.

    1. Loads processed features.
    2. Assigns bins based on potential.
    3. Saves the result.

    Returns:
        Tuple[pd.DataFrame, Path]: The bin-assigned dataframe and the output path.
    """
    try:
        df = load_processed_features()
        df_binned = assign_bins(df)
        output_path = save_bins(df_binned)
        return df_binned, output_path
    except Exception as e:
        logger.error(f"Binning pipeline failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting Binning Pipeline (T019)...")
    df_result, path_result = run_binning_pipeline()
    print(f"Pipeline completed. Output saved to: {path_result}")
    print(f"Sample bin assignments:\n{df_result[['molecule_id', 'potential_v', 'bin']].head()}")
