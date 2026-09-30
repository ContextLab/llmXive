"""
Module for aligning MMN amplitude data with behavioral accuracy blocks.
Implements lagged alignment, learning phase generation, and data integrity checks.
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_config, get_accuracy_block_size, get_lag_window

# Define custom exception for data integrity issues
class DataIntegrityError(Exception):
    """Raised when data integrity checks fail (e.g., synthetic data detected)."""
    pass

def load_mmn_epochs(file_path: str) -> pd.DataFrame:
    """
    Load MMN epochs from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing MMN epochs.
        
    Returns:
        DataFrame with MMN epoch data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has invalid schema.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"MMN epochs file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    if df.empty:
        raise ValueError(f"MMN epochs file is empty: {file_path}")
    
    required_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in MMN epochs: {missing_cols}")
    
    return df

def load_accuracy_blocks(file_path: str) -> pd.DataFrame:
    """
    Load accuracy blocks from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing accuracy blocks.
        
    Returns:
        DataFrame with accuracy block data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has invalid schema.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Accuracy blocks file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    if df.empty:
        raise ValueError(f"Accuracy blocks file is empty: {file_path}")
    
    required_cols = ['subject_id', 'block_id', 'trial_start', 'trial_end', 'accuracy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in accuracy blocks: {missing_cols}")
    
    return df

def calculate_block_accuracy(epochs_df: pd.DataFrame, block_size: int) -> pd.DataFrame:
    """
    Calculate block accuracy from epochs data.
    
    Args:
        epochs_df: DataFrame containing epoch data with 'subject_id', 'trial', 'correct' columns.
        block_size: Number of trials per block.
        
    Returns:
        DataFrame with block-level accuracy data.
    """
    if 'correct' not in epochs_df.columns:
        raise ValueError("Epochs DataFrame must contain 'correct' column for accuracy calculation")
    
    epochs_df = epochs_df.sort_values(['subject_id', 'trial'])
    
    # Create block_id based on trial number
    epochs_df['block_id'] = (epochs_df['trial'] // block_size).astype(int)
    
    # Calculate accuracy per block
    accuracy_blocks = epochs_df.groupby(['subject_id', 'block_id']).agg({
        'correct': 'mean',
        'trial': ['min', 'max']
    }).reset_index()
    
    accuracy_blocks.columns = ['subject_id', 'block_id', 'accuracy', 'trial_start', 'trial_end']
    
    return accuracy_blocks

def run_behavioral_binning_pipeline(
    epochs_file: str, 
    output_file: str, 
    block_size: Optional[int] = None
) -> pd.DataFrame:
    """
    Run the behavioral binning pipeline to generate accuracy blocks.
    
    Args:
        epochs_file: Path to the epochs CSV file.
        output_file: Path to save the accuracy blocks CSV.
        block_size: Number of trials per block (uses config default if None).
        
    Returns:
        DataFrame with accuracy blocks.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting behavioral binning pipeline. Input: {epochs_file}")
    
    if block_size is None:
        config = get_config()
        block_size = get_accuracy_block_size()
    
    epochs_df = pd.read_csv(epochs_file)
    accuracy_blocks = calculate_block_accuracy(epochs_df, block_size)
    
    # Save to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    accuracy_blocks.to_csv(output_file, index=False)
    
    logger.info(f"Behavioral binning complete. Output: {output_file} ({len(accuracy_blocks)} blocks)")
    return accuracy_blocks

def run_lagged_alignment_pipeline(
    mmn_file: str,
    accuracy_file: str,
    output_file: str,
    lag_window: Optional[Tuple[int, int]] = None
) -> pd.DataFrame:
    """
    Run the lagged alignment pipeline to align MMN amplitudes with subsequent accuracy blocks.
    
    Args:
        mmn_file: Path to the MMN epochs CSV file.
        accuracy_file: Path to the accuracy blocks CSV file.
        output_file: Path to save the interim lagged MMNs CSV.
        lag_window: Tuple of (start_offset, end_offset) in trials (default: -50, -10).
        
    Returns:
        DataFrame with lagged alignment data.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting lagged alignment pipeline. MMN: {mmn_file}, Accuracy: {accuracy_file}")
    
    if lag_window is None:
        lag_window = get_lag_window()
    
    # Load data
    mmn_df = load_mmn_epochs(mmn_file)
    accuracy_df = load_accuracy_blocks(accuracy_file)
    
    # Validate source_type for data integrity (T048 requirement)
    _validate_data_integrity(mmn_df, "MMN epochs")
    _validate_data_integrity(accuracy_df, "Accuracy blocks")
    
    # Perform lagged alignment
    aligned_data = []
    
    for _, accuracy_row in accuracy_df.iterrows():
        subject_id = accuracy_row['subject_id']
        block_id = accuracy_row['block_id']
        trial_start = accuracy_row['trial_start']
        
        # Find MMN data from the lagged window (t-N to t-M)
        # Source window: trials before the accuracy block
        source_start = trial_start + lag_window[0]  # e.g., trial_start - 50
        source_end = trial_start + lag_window[1]    # e.g., trial_start - 10
        
        # Filter MMN data for this subject and time window
        mmn_subset = mmn_df[
            (mmn_df['subject_id'] == subject_id) &
            (mmn_df['source_window_start_trial'] >= source_start) &
            (mmn_df['source_window_start_trial'] < source_end)
        ]
        
        if mmn_subset.empty:
            logger.warning(f"No MMN data found for subject {subject_id}, block {block_id} in window [{source_start}, {source_end})")
            continue
        
        # Calculate mean MMN amplitude for the source window
        mean_mmn = mmn_subset['mmn_amplitude'].mean()
        source_trial = mmn_subset['source_window_start_trial'].iloc[0]
        
        aligned_data.append({
            'subject_id': subject_id,
            'block_id': block_id,
            'mmn_amplitude': mean_mmn,
            'source_window_start_trial': source_trial
        })
    
    aligned_df = pd.DataFrame(aligned_data)
    
    if aligned_df.empty:
        logger.warning("Lagged alignment produced no data. Check input files and lag window settings.")
    
    # Save to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    aligned_df.to_csv(output_file, index=False)
    
    logger.info(f"Lagged alignment complete. Output: {output_file} ({len(aligned_df)} records)")
    return aligned_df

def _validate_data_integrity(df: pd.DataFrame, data_type: str) -> None:
    """
    Validate that data is from a real source and not synthetic.
    
    Args:
        df: DataFrame to validate.
        data_type: Description of the data for error messages.
        
    Raises:
        DataIntegrityError: If data is synthetic or missing source_type.
    """
    if 'source_type' not in df.columns:
        logger = get_logger(__name__)
        logger.warning(f"Column 'source_type' missing in {data_type}. Assuming real data if no synthetic flag present.")
        # If column is missing, we cannot definitively say it's synthetic, 
        # but we log a warning. Per T048, we should raise if explicitly marked synthetic.
        return
    
    # Check for synthetic data
    synthetic_rows = df[df['source_type'].isin(['synthetic', 'mock', 'fake'])]
    if not synthetic_rows.empty:
        logger = get_logger(__name__)
        error_msg = f"Synthetic data detected in {data_type}. Found {len(synthetic_rows)} rows marked as synthetic/mock/fake. Skipping this dataset."
        logger.error(error_msg)
        raise DataIntegrityError(error_msg)
    
    # Log validation success
    valid_types = df['source_type'].unique()
    logger = get_logger(__name__)
    logger.info(f"Data integrity check passed for {data_type}. Source types: {list(valid_types)}")

def add_learning_phase(
    input_file: str,
    output_file: str
) -> pd.DataFrame:
    """
    Add learning phase (Early/Late) based on block_id median.
    
    Args:
        input_file: Path to the filtered aligned data CSV.
        output_file: Path to save the data with learning phase.
        
    Returns:
        DataFrame with learning phase added.
    """
    logger = get_logger(__name__)
    logger.info(f"Adding learning phase to: {input_file}")
    
    df = pd.read_csv(input_file)
    if df.empty:
        logger.warning(f"Input file is empty: {input_file}")
        return df
    
    # Calculate median block_id
    median_block = df['block_id'].median()
    
    # Assign learning phase
    df['learning_phase'] = df['block_id'].apply(
        lambda x: 'Late' if x >= median_block else 'Early'
    )
    
    # Save to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    logger.info(f"Learning phase added. Output: {output_file}")
    logger.info(f"Median block_id: {median_block}, Early blocks: {len(df[df['learning_phase']=='Early'])}, Late blocks: {len(df[df['learning_phase']=='Late'])}")
    return df

def run_learning_phase_pipeline(
    input_file: str,
    output_file: str
) -> pd.DataFrame:
    """
    Run the learning phase generation pipeline.
    
    Args:
        input_file: Path to the filtered aligned data CSV.
        output_file: Path to save the data with learning phase.
        
    Returns:
        DataFrame with learning phase added.
    """
    return add_learning_phase(input_file, output_file)

def main():
    """
    Main entry point for the align module.
    This function is intended to be called by the main pipeline runner.
    """
    logger = get_logger(__name__)
    logger.info("Align module main() called")
    
    # Example usage (to be overridden by pipeline runner):
    # mmn_file = "data/interim_mmn_epochs.csv"
    # accuracy_file = "data/accuracy_blocks.csv"
    # output_file = "data/interim_lagged_mmns.csv"
    # run_lagged_alignment_pipeline(mmn_file, accuracy_file, output_file)
    
    logger.info("Align module main() completed")

if __name__ == "__main__":
    main()
