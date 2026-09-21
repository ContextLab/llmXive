import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

def is_valid_entry(entry: dict) -> bool:
    """
    Validate a single dataset entry to ensure it contains valid code.
    
    Checks:
    1. 'python_code' and 'javascript_code' keys exist
    2. Both values are non-empty strings
    3. Neither value is None, NaN, or non-string type
    
    Args:
        entry: A dictionary representing a row from the dataset
      
    Returns:
        True if the entry is valid, False otherwise
    """
    required_fields = ['python_code', 'javascript_code']
    
    # Check if all required fields exist
    if not all(field in entry for field in required_fields):
        return False
      
    python_code = entry['python_code']
    js_code = entry['javascript_code']
    
    # Check for None or NaN
    if pd.isna(python_code) or pd.isna(js_code):
        return False
      
    # Check if types are string
    if not isinstance(python_code, str) or not isinstance(js_code, str):
        return False
    
    # Check if strings are empty
    if not python_code.strip() or not js_code.strip():
        return False
    
    return True

def validate_and_filter_dataset(df: pd.DataFrame, source_path: Optional[Path] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate and filter the dataset, excluding corrupted entries.
    
    This function applies strict validation rules to the dataset:
    - Removes entries with missing required columns
    - Removes entries where code fields are not strings
    - Removes entries with empty code strings
    - Logs detailed information about excluded entries for debugging
    
    Args:
        df: The pandas DataFrame containing the dataset
        source_path: Optional path to the source file for logging reference
      
    Returns:
        Tuple of (filtered DataFrame, list of excluded entry indices/reasons)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. No validation performed.")
        return df, []
    
    logger.info(f"Starting validation of {len(df)} entries from {source_path or 'dataset'}")
    
    excluded_indices = []
    exclusion_reasons = []
    
    # Apply validation row by row
    valid_mask = df.apply(is_valid_entry, axis=1)
    
    excluded_indices = df[~valid_mask].index.tolist()
    excluded_entries = df[~valid_mask]
    
    # Log reasons for exclusion (sample)
    if len(excluded_entries) > 0:
        logger.warning(f"Found {len(excluded_indices)} invalid entries")
        
        # Count specific reasons
        reason_counts = {
            'missing_fields': 0,
            'non_string_type': 0,
            'empty_string': 0,
            'nan_value': 0
        }
        
        for idx, row in excluded_entries.iterrows():
            reason = "unknown"
            if not all(field in row for field in ['python_code', 'javascript_code']):
                reason = "missing_fields"
            elif not isinstance(row.get('python_code'), str) or not isinstance(row.get('javascript_code'), str):
                reason = "non_string_type"
            elif pd.isna(row.get('python_code')) or pd.isna(row.get('javascript_code')):
                reason = "nan_value"
            elif not str(row.get('python_code', '')).strip() or not str(row.get('javascript_code', '')).strip():
                reason = "empty_string"
            
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        for reason, count in reason_counts.items():
            if count > 0:
                logger.info(f"  - {reason}: {count} entries")
    
    filtered_df = df[valid_mask].reset_index(drop=True)
    
    logger.info(f"Validation complete: {len(filtered_df)} valid entries retained, {len(excluded_indices)} excluded")
    
    return filtered_df, excluded_indices

def main():
    """
    Main entry point for running dataset validation.
    
    This function is designed to be called from the preprocessing pipeline
    to ensure data quality before further processing.
    """
    logger.info("Dataset validation module initialized")
    # This module is designed to be imported and used by other components
    # in the ingestion pipeline (e.g., preprocess_corpus.py)
    return True

if __name__ == "__main__":
    main()
