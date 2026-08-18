"""
Provenance Filtering Logic.

Implements strict filtering rules for reaction mechanism data.
Ensures NO fallback to synthetic data or product-structure inferred labels.
"""
from typing import List, Dict, Any, Optional
import re

from src.utils.logging import log_provenance_mismatch, log_data_quality_issue, log_warning

# Valid provenance types for kinetic studies
VALID_PROVENANCE_TYPES = {
    'kinetic studies',
    'validated intermediates',
    'kinetic',
    'validated'
}

# Keywords that indicate product-structure inference (to be excluded)
EXCLUSION_KEYWORDS = [
    'product structure',
    'inferred from product',
    'product only',
    'thermodynamic',
    'equilibrium',
    'static'
]

def is_valid_provenance(provenance: str) -> bool:
    """
    Checks if a provenance string indicates a valid kinetic study.
    
    Args:
        provenance: The provenance string from the dataset.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(provenance, str):
        return False
    
    provenance_lower = provenance.lower().strip()
    
    # Check exact matches or substring matches for valid types
    for valid_type in VALID_PROVENANCE_TYPES:
        if valid_type in provenance_lower:
            return True
            
    return False

def should_exclude_row(row: Dict[str, Any]) -> bool:
    """
    Determines if a row should be excluded based on provenance.
    
    Logic:
    1. If provenance is missing, exclude (fail loudly or warn).
    2. If provenance contains exclusion keywords (e.g., 'product structure'), exclude.
    3. If provenance is not in valid set, exclude.
    
    Args:
        row: A dictionary representing a data row.
        
    Returns:
        bool: True if the row should be EXCLUDED.
    """
    provenance = row.get('provenance', None)
    
    if provenance is None:
        log_provenance_mismatch("Row missing 'provenance' field.")
        return True
    
    provenance_str = str(provenance).lower().strip()
    
    # Check for explicit exclusion keywords
    for keyword in EXCLUSION_KEYWORDS:
        if keyword in provenance_str:
            log_provenance_mismatch(f"Row excluded due to product-structure inference: {provenance}")
            return True
    
    # Check against valid set
    if not is_valid_provenance(provenance):
        log_provenance_mismatch(f"Row excluded: invalid provenance type '{provenance}'")
        return True
        
    return False

def filter_by_provenance(df: Any) -> Any:
    """
    Filters a DataFrame or list of rows based on provenance.
    
    Args:
        df: Pandas DataFrame or list of dicts.
        
    Returns:
        Filtered DataFrame or list.
    """
    if hasattr(df, 'apply'):
        # Pandas DataFrame
        mask = df.apply(should_exclude_row, axis=1)
        return df[~mask]
    else:
        # List of dicts
        return [row for row in df if not should_exclude_row(row)]

def validate_provenance_consistency(df: Any) -> Dict[str, int]:
    """
    Validates the consistency of provenance fields in a dataset.
    
    Returns:
        Dict with counts of valid vs invalid entries.
    """
    if hasattr(df, 'apply'):
        mask = df.apply(should_exclude_row, axis=1)
        return {
            'valid': int((~mask).sum()),
            'invalid': int(mask.sum()),
            'total': len(df)
        }
    return {'valid': 0, 'invalid': 0, 'total': 0}
