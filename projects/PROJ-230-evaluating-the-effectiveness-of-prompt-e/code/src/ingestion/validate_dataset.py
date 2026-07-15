"""
Validation logic for the cached dataset to exclude corrupted entries.

This module implements the filtering logic required to clean the raw dataset
downloaded in T013. It ensures that only entries with valid string types for
both 'python_code' and 'javascript_code' are retained, and that neither field
is missing or empty.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional

# Import the logger utility defined in T008
from src.utils.logging import get_logger

# Configure logger for this module
logger = get_logger(__name__)


def is_valid_entry(row: pd.Series) -> bool:
    """
    Check if a single row in the dataset is valid.
    
    A valid entry must:
    1. Have 'python_code' and 'javascript_code' columns present.
    2. Have both columns as non-empty strings.
    3. Not be NaN or None.
    
    Args:
        row: A pandas Series representing a single dataset entry.
        
    Returns:
        True if the entry is valid, False otherwise.
    """
    required_cols = ['python_code', 'javascript_code']
    
    # Check if required columns exist
    if not all(col in row.index for col in required_cols):
        return False
        
    python_code = row['python_code']
    js_code = row['javascript_code']
    
    # Check for NaN, None, or non-string types
    if pd.isna(python_code) or pd.isna(js_code):
        return False
        
    if not isinstance(python_code, str) or not isinstance(js_code, str):
        return False
        
    # Check for empty strings (after stripping whitespace)
    if not python_code.strip() or not js_code.strip():
        return False
        
    return True


def validate_and_filter_dataset(
    input_path: Path,
    output_path: Path,
    log_corrupted: bool = True
) -> Tuple[int, int, List[dict]]:
    """
    Load a dataset CSV, filter out corrupted entries, and save the result.
    
    This function implements the core validation logic for T013b. It reads
    the raw cached dataset, applies strict type and content checks, logs
    statistics about excluded entries, and writes the clean dataset to disk.
    
    Args:
        input_path: Path to the raw input CSV (from data/raw/).
        output_path: Path where the cleaned CSV will be saved.
        log_corrupted: If True, log details of the first 10 corrupted entries.
        
    Returns:
        A tuple containing:
            - total_rows: Total number of rows in the input file.
            - valid_rows: Number of rows that passed validation.
            - error_samples: List of dictionaries describing the first 10 errors.
    """
    logger.info(f"Starting validation for dataset: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Load the dataset
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        raise
        
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows from {input_path}")
    
    # Apply validation
    valid_mask = df.apply(is_valid_entry, axis=1)
    valid_count = valid_mask.sum()
    invalid_count = total_rows - valid_count
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} excluded.")
    
    # Log details of corrupted entries if requested
    if log_corrupted and invalid_count > 0:
        invalid_indices = df[~valid_mask].index[:10].tolist()
        error_samples = []
        
        for idx in invalid_indices:
            row = df.loc[idx]
            reason = []
            
            if 'python_code' not in row.index:
                reason.append("missing python_code column")
            elif pd.isna(row['python_code']) or not isinstance(row['python_code'], str):
                reason.append("invalid python_code type or NaN")
            elif not str(row['python_code']).strip():
                reason.append("empty python_code")
                
            if 'javascript_code' not in row.index:
                reason.append("missing javascript_code column")
            elif pd.isna(row['javascript_code']) or not isinstance(row['javascript_code'], str):
                reason.append("invalid javascript_code type or NaN")
            elif not str(row['javascript_code']).strip():
                reason.append("empty javascript_code")
                
            error_samples.append({
                "index": int(idx),
                "reasons": "; ".join(reason)
            })
            
        for sample in error_samples:
            logger.warning(f"Corrupted entry at index {sample['index']}: {sample['reasons']}")
            
        logger.info(f"Logged first {len(error_samples)} corrupted entries.")
        
    # Filter the dataframe
    df_clean = df[valid_mask].reset_index(drop=True)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the cleaned dataset
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Cleaned dataset saved to: {output_path}")
    
    return total_rows, valid_count, error_samples


def main():
    """
    Entry point for running validation on the default raw dataset path.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # Look for the most recent raw dataset file
    raw_files = list(raw_dir.glob("*.csv"))
    if not raw_files:
        logger.error("No CSV files found in data/raw/. Run download_datasets.py first.")
        return
        
    # Assume the latest file is the one we want to process
    latest_raw = max(raw_files, key=lambda p: p.stat().st_mtime)
    output_file = processed_dir / "corpus_cleaned.csv"
    
    logger.info(f"Processing {latest_raw} -> {output_file}")
    
    try:
        total, valid, _ = validate_and_filter_dataset(latest_raw, output_file)
        logger.info(f"Successfully processed {valid}/{total} rows.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()