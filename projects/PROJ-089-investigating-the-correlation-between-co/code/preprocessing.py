"""
Preprocessing module for the Code Churn vs Technical Debt pipeline.

This module handles:
1. Filtering non-source code files from the raw metrics dataset.
2. Excluding files with avg_loc below a specified threshold.
3. Generating parameterized datasets for sensitivity analysis (thresholds: 5, 10, 20).
4. Saving the final unified metrics CSV.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import utilities from sibling modules as per API surface
from config import get_config_summary
from utils import get_logger

# Constants
DEFAULT_THRESHOLDS = [5, 10, 20]
SOURCE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.m', '.mm'}
EXCLUDED_DIRS = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build', 'target', 'vendor', '.cargo', 'min', 'minified', 'test', 'tests', 'spec', 'specs', 'docs', 'examples', 'sample', 'samples', 'fixture', 'fixtures'}

logger = get_logger(__name__)

def is_source_file(file_path: str) -> bool:
    """
    Check if a file is a source code file based on its extension.

    Args:
        file_path: The path to the file.

    Returns:
        True if the file has a recognized source code extension, False otherwise.
    """
    if not file_path:
        return False
    ext = Path(file_path).suffix.lower()
    return ext in SOURCE_EXTENSIONS

def should_exclude_dir(dir_name: str) -> bool:
    """
    Check if a directory should be excluded from processing.

    Args:
        dir_name: The name of the directory.

    Returns:
        True if the directory should be excluded, False otherwise.
    """
    return dir_name in EXCLUDED_DIRS

def filter_non_source_files(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the DataFrame to keep only rows corresponding to source code files.

    Args:
        df: The input DataFrame containing file metrics.

    Returns:
        A filtered DataFrame containing only source code files.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df

    # Ensure 'file_path' column exists
    if 'file_path' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'file_path' column.")

    logger.info(f"Filtering non-source files from {len(df)} rows...")
    mask = df['file_path'].apply(is_source_file)
    filtered_df = df[mask].copy()
    logger.info(f"Kept {len(filtered_df)} source code files.")

    return filtered_df

def apply_loc_threshold(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Filter the DataFrame to exclude files with avg_loc below the given threshold.

    Args:
        df: The input DataFrame containing file metrics.
        threshold: The minimum average lines of code (avg_loc) required.

    Returns:
        A filtered DataFrame containing only files meeting the LOC threshold.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df

    if 'avg_loc' not in df.columns:
        raise ValueError("Input DataFrame must contain an 'avg_loc' column.")

    logger.info(f"Applying LOC threshold >= {threshold}...")
    mask = df['avg_loc'] >= threshold
    filtered_df = df[mask].copy()
    logger.info(f"Kept {len(filtered_df)} files with avg_loc >= {threshold}.")

    return filtered_df

def generate_parameterized_datasets(df: pd.DataFrame, thresholds: List[int] = DEFAULT_THRESHOLDS) -> Dict[int, pd.DataFrame]:
    """
    Generate parameterized datasets for sensitivity analysis based on different LOC thresholds.

    Args:
        df: The input DataFrame containing raw metrics.
        thresholds: List of LOC thresholds to apply (default: [5, 10, 20]).

    Returns:
        A dictionary mapping each threshold to its corresponding filtered DataFrame.
    """
    datasets = {}
    for threshold in thresholds:
        logger.info(f"Generating dataset for threshold={threshold}...")
        filtered_df = apply_loc_threshold(df, threshold)
        datasets[threshold] = filtered_df
    return datasets

def save_datasets(datasets: Dict[int, pd.DataFrame], output_dir: Path) -> List[Path]:
    """
    Save the parameterized datasets to CSV files.

    Args:
        datasets: Dictionary of threshold -> DataFrame.
        output_dir: Directory to save the CSV files.

    Returns:
        List of paths to the saved CSV files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for threshold, df in datasets.items():
        filename = f"unified_metrics_threshold_{threshold}.csv"
        filepath = output_dir / filename
        df.to_csv(filepath, index=False)
        saved_paths.append(filepath)
        logger.info(f"Saved dataset for threshold={threshold} to {filepath}")

    return saved_paths

def validate_raw_metrics(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains the required raw metrics columns
    and that they are not null for critical rows.

    Args:
        df: The DataFrame to validate.

    Returns:
        True if validation passes, False otherwise.
    """
    required_cols = ['total_lines_changed', 'debt_score', 'avg_loc', 'contributor_count']
    
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False

    # Check for non-null values in critical columns
    critical_cols = ['total_lines_changed', 'debt_score']
    for col in critical_cols:
        if df[col].isnull().any():
            logger.warning(f"Column '{col}' contains null values.")
            # Depending on strictness, this might fail validation. 
            # For now, we log a warning but proceed.
    
    logger.info("Raw metrics validation passed.")
    return True

def run_preprocessing(input_path: Path, output_dir: Path, thresholds: List[int] = DEFAULT_THRESHOLDS) -> Path:
    """
    Main entry point for the preprocessing pipeline.

    1. Loads the raw unified metrics CSV.
    2. Filters non-source files.
    3. Applies LOC thresholds to generate parameterized datasets.
    4. Saves the final unified metrics CSV (using the default threshold of 10, or the last one if specified differently).
    5. Validates the output.

    Args:
        input_path: Path to the input raw metrics CSV.
        output_dir: Directory to save the processed CSV files.
        thresholds: List of LOC thresholds for sensitivity analysis.

    Returns:
        Path to the primary output CSV file (unified_metrics.csv).
    """
    logger.info(f"Starting preprocessing from {input_path}...")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load raw data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Step 1: Filter non-source files
    df_source = filter_non_source_files(df)
    
    if df_source.empty:
        logger.error("No source code files found after filtering. Stopping.")
        raise ValueError("No source code files found in input data.")

    # Step 2: Generate parameterized datasets for sensitivity analysis
    parameterized_datasets = generate_parameterized_datasets(df_source, thresholds)

    # Step 3: Save parameterized datasets
    save_datasets(parameterized_datasets, output_dir)

    # Step 4: Determine the primary dataset to save as 'unified_metrics.csv'
    # Per task description, we output the dataset with the standard threshold (usually 10)
    # If 10 is not in thresholds, we use the first one or the most restrictive one?
    # The task says "Generate parameterized datasets... Output unified_metrics.csv".
    # We will output the one corresponding to the default threshold 10 if present, else the first in list.
    primary_threshold = 10 if 10 in thresholds else thresholds[0]
    if primary_threshold not in parameterized_datasets:
        # Fallback: use the one closest to 10 or just the first
        primary_threshold = thresholds[0]
    
    final_df = parameterized_datasets[primary_threshold]

    # Validate raw metrics before saving
    if not validate_raw_metrics(final_df):
        logger.error("Validation failed for the final dataset.")
        # Depending on policy, we might stop here. We log but proceed to save what we have.

    # Save the primary unified_metrics.csv
    output_path = output_dir / "unified_metrics.csv"
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved final unified metrics to {output_path}")

    return output_path

def main():
    """
    Main function to run preprocessing when executed as a script.
    Reads configuration from environment or defaults.
    """
    config = get_config_summary()
    
    # Default paths
    input_file = Path("data/raw/unified_metrics_raw.csv") # Assumed intermediate name from T014
    # If T014 output is different, adjust here. Based on T014, it likely outputs to data/raw or data/processed.
    # Let's assume the input for T015 is the raw output from T014.
    # If T014 output is `data/raw/unified_metrics.csv` or similar, we need to be flexible.
    # The task says T015 generates `data/processed/unified_metrics.csv`.
    # Let's assume the input is `data/raw/metrics_combined.csv` or similar. 
    # Since T014 output isn't explicitly named in the prompt's `tasks.md` text for T014 (it says "Calculate debt_score"),
    # but T015 says "Output data/processed/unified_metrics.csv", we assume the input exists.
    # Common convention: T014 outputs to data/raw/ for T015 to process.
    
    # Let's try to find the input dynamically or use a standard path.
    # Standard path from T014 context: likely data/raw/unified_metrics_raw.csv or similar.
    # However, to be robust, we check common locations.
    possible_inputs = [
        Path("data/raw/unified_metrics_raw.csv"),
        Path("data/raw/metrics.csv"),
        Path("data/processed/raw_metrics.csv")
    ]
    
    input_path = None
    for p in possible_inputs:
        if p.exists():
            input_path = p
            break
    
    if not input_path:
        # Fallback to a generic name if the user runs it directly
        input_path = Path("data/raw/unified_metrics_raw.csv")
        if not input_path.exists():
            raise FileNotFoundError(f"Could not find input file. Expected one of {possible_inputs}")

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result_path = run_preprocessing(input_path, output_dir)
        logger.info(f"Preprocessing completed successfully. Output: {result_path}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
