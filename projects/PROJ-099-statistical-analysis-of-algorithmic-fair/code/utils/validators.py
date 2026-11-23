import hashlib
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pandas as pd
from utils.logging_utils import log_warning

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(calculated: str, expected: str) -> bool:
    """
    Verify if a calculated checksum matches an expected checksum.
    
    Args:
        calculated: The calculated SHA-256 hash.
        expected: The expected SHA-256 hash.
        
    Returns:
        True if they match, False otherwise.
    """
    return calculated.lower() == expected.lower()

def get_required_columns() -> List[str]:
    """
    Get the list of required columns for fairness analysis.
    
    Returns:
        List of required column names.
    """
    return [
        'protected_attribute',
        'outcome',
        'prediction'
    ]

def validate_variable_presence(df: pd.DataFrame, 
                               protected_attr_col: str, 
                               outcome_col: str, 
                               prediction_col: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate that required variables are present in the dataset.
    
    Args:
        df: The pandas DataFrame to validate.
        protected_attr_col: Name of the protected attribute column.
        outcome_col: Name of the outcome column.
        prediction_col: Name of the prediction column (optional).
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    missing = []
    cols_to_check = [protected_attr_col, outcome_col]
    if prediction_col:
        cols_to_check.append(prediction_col)
        
    for col in cols_to_check:
        if col not in df.columns:
            missing.append(col)
            
    is_valid = len(missing) == 0
    if not is_valid:
        log_warning(f"Missing required columns: {missing}")
        
    return is_valid, missing
