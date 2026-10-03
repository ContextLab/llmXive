"""
Schema definitions and validation utilities for pipeline CSV artifacts.
"""
from typing import List, Dict, Any, Tuple

# Schema definitions
FILTER_RESULTS_HEADERS = ["dataset_id", "shapiro_p", "sample_size", "included"]
DATASETS_HEADERS = ["dataset_id", "source_url", "sample_size", "num_variables", 
                    "continuous_variables", "checksum", "skewness", "kurtosis", "included"]
CHECKSUMS_HEADERS = ["dataset_id", "checksum"]
IMPUTATION_LOG_HEADERS = ["dataset_id", "variable", "imputation_method", "rate"]
EXCLUSIONS_HEADERS = ["dataset_id", "reason", "details"]

def get_filter_results_headers() -> List[str]:
    """Return the headers for filter_results.csv."""
    return FILTER_RESULTS_HEADERS

def get_datasets_headers() -> List[str]:
    """Return the headers for datasets.csv."""
    return DATASETS_HEADERS

def get_checksums_headers() -> List[str]:
    """Return the headers for checksums.csv."""
    return CHECKSUMS_HEADERS

def get_imputation_log_headers() -> List[str]:
    """Return the headers for imputation_log.csv."""
    return IMPUTATION_LOG_HEADERS

def get_exclusions_headers() -> List[str]:
    """Return the headers for exclusions.csv."""
    return EXCLUSIONS_HEADERS

def validate_filter_results_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a row in filter_results.csv.
    
    Expected columns: dataset_id (str), shapiro_p (float), sample_size (int), included (bool)
    """
    required_cols = set(FILTER_RESULTS_HEADERS)
    actual_cols = set(row.keys())
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        return False, f"Missing columns: {missing}"
    
    # Type checks
    try:
        float(row['shapiro_p'])
        int(row['sample_size'])
        bool(row['included'])
    except (ValueError, TypeError) as e:
        return False, f"Type validation failed: {str(e)}"
        
    return True, ""

def validate_imputation_log_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a row in imputation_log.csv."""
    required_cols = set(IMPUTATION_LOG_HEADERS)
    actual_cols = set(row.keys())
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        return False, f"Missing columns: {missing}"
    return True, ""

def validate_exclusions_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a row in exclusions.csv."""
    required_cols = set(EXCLUSIONS_HEADERS)
    actual_cols = set(row.keys())
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        return False, f"Missing columns: {missing}"
    return True, ""

def validate_datasets_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a row in datasets.csv."""
    required_cols = set(DATASETS_HEADERS)
    actual_cols = set(row.keys())
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        return False, f"Missing columns: {missing}"
    return True, ""