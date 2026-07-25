import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

def is_valid_entry(entry: dict) -> bool:
    """
    Validate a single dataset entry for code translation tasks.
    
    An entry is valid if:
    1. It contains 'python_code' and 'javascript_code' keys
    2. Both values are non-empty strings
    3. Both values are actually string types (not None, list, dict, etc.)
    
    Args:
        entry: Dictionary representing a dataset row
        
    Returns:
        True if the entry is valid, False otherwise
    """
    if not isinstance(entry, dict):
        return False
        
    required_fields = ['python_code', 'javascript_code']
    
    # Check all required fields exist
    for field in required_fields:
        if field not in entry:
            logger.debug(f"Entry missing required field: {field}")
            return False
        
        value = entry[field]
        
        # Check type is string
        if not isinstance(value, str):
            logger.debug(f"Field '{field}' is not a string (type: {type(value).__name__})")
            return False
        
        # Check string is not empty or just whitespace
        if not value.strip():
            logger.debug(f"Field '{field}' is empty or whitespace-only")
            return False
            
    return True

def validate_and_filter_dataset(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    log_excluded: bool = True
) -> Tuple[pd.DataFrame, int]:
    """
    Validate and filter a dataset DataFrame, removing corrupted entries.
    
    This function:
    1. Iterates through all rows
    2. Validates each entry using is_valid_entry()
    3. Removes invalid entries
    4. Optionally logs details about excluded entries
    5. Optionally saves a log of excluded entries to disk
    
    Args:
        df: Input DataFrame containing the raw dataset
        output_path: Optional path to save a CSV log of excluded entries
        log_excluded: Whether to log excluded entries (default: True)
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded entries)
        
    Raises:
        ValueError: If input DataFrame is empty or None
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame cannot be None or empty")
        
    logger.info(f"Starting validation of {len(df)} entries")
    
    valid_mask = []
    excluded_entries = []
    
    for idx, row in df.iterrows():
        entry = row.to_dict()
        is_valid = is_valid_entry(entry)
        valid_mask.append(is_valid)
        
        if not is_valid and log_excluded:
            excluded_entries.append({
                'index': idx,
                'reason': 'Invalid entry structure',
                'python_code_preview': str(entry.get('python_code', ''))[:50] if entry.get('python_code') else 'N/A',
                'javascript_code_preview': str(entry.get('javascript_code', ''))[:50] if entry.get('javascript_code') else 'N/A'
            })
    
    # Filter the DataFrame
    valid_df = df[valid_mask].reset_index(drop=True)
    excluded_count = len(df) - len(valid_df)
    
    logger.info(f"Validation complete: {len(valid_df)} valid entries, {excluded_count} excluded")
    
    # Log excluded entries if requested
    if excluded_count > 0 and log_excluded:
        logger.warning(f"Excluded {excluded_count} corrupted entries")
        
        if output_path:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save excluded entries to CSV
            excluded_df = pd.DataFrame(excluded_entries)
            excluded_df.to_csv(output_path, index=False)
            logger.info(f"Saved excluded entries log to: {output_path}")
        
        # Log summary of exclusion reasons
        if excluded_entries:
            logger.info(f"Sample excluded entry: {excluded_entries[0]}")
    
    return valid_df, excluded_count

def main():
    """
    Main entry point for standalone execution of dataset validation.
    
    This function:
    1. Loads a raw dataset from data/raw/
    2. Validates and filters corrupted entries
    3. Saves the clean dataset to data/processed/
    4. Logs statistics about the filtering process
    """
    logger.info("Starting dataset validation process")
    
    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Find CSV files in raw directory
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        logger.error(f"No CSV files found in {raw_dir}")
        return
        
    for raw_file in csv_files:
        logger.info(f"Processing file: {raw_file}")
        
        try:
            # Load dataset
            df = pd.read_csv(raw_file)
            logger.info(f"Loaded {len(df)} entries from {raw_file.name}")
            
            # Validate and filter
            clean_df, excluded_count = validate_and_filter_dataset(
                df,
                output_path=processed_dir / f"{raw_file.stem}_excluded.csv"
            )
            
            # Save clean dataset
            output_file = processed_dir / f"{raw_file.stem}_clean.csv"
            clean_df.to_csv(output_file, index=False)
            logger.info(f"Saved clean dataset to {output_file}")
            logger.info(f"Retention rate: {len(clean_df)/len(df)*100:.2f}%")
            
        except Exception as e:
            logger.error(f"Error processing {raw_file}: {str(e)}", exc_info=True)
            
    logger.info("Dataset validation process completed")

if __name__ == "__main__":
    main()