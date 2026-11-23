"""
Preprocessing utilities for embedding generation.
Handles edge cases: zero-variance columns, missing image/text fields.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)


def detect_zero_variance_columns(df: Any) -> List[str]:
    """
    Detect columns with zero variance (constant values).
    
    Args:
        df: Pandas DataFrame or similar object with numeric columns
        
    Returns:
        List of column names with zero variance
    """
    zero_var_cols = []
    
    if df is None:
        log_warning("DataFrame is None, skipping zero variance detection")
        return zero_var_cols
        
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        try:
            unique_vals = df[col].nunique()
            if unique_vals <= 1:
                zero_var_cols.append(col)
                log_warning(f"Column '{col}' has zero variance (constant value)")
        except Exception as e:
            log_error(f"Error checking variance for column '{col}': {e}")
            
    return zero_var_cols


def detect_missing_fields(row: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Detect missing required fields in a dataset row.
    
    Args:
        row: Dictionary representing a data row
        required_fields: List of field names that must be present
        
    Returns:
        List of missing field names
    """
    missing = []
    for field in required_fields:
        if field not in row or row[field] is None:
            missing.append(field)
            
    return missing


def handle_zero_variance_columns(
    df: Any, 
    strategy: str = 'drop',
    constant_value: Optional[float] = None
) -> Tuple[Any, List[str]]:
    """
    Handle zero-variance columns by either dropping them or imputing constant values.
    
    Args:
        df: Pandas DataFrame
        strategy: 'drop' to remove columns, 'impute' to fill with constant
        constant_value: Value to use for imputation (default: mean of column)
        
    Returns:
        Tuple of (processed DataFrame, list of handled column names)
    """
    if df is None:
        log_warning("DataFrame is None, cannot handle zero variance")
        return df, []
        
    zero_var_cols = detect_zero_variance_columns(df)
    
    if not zero_var_cols:
        return df, []
        
    handled_cols = []
    
    if strategy == 'drop':
        log_info(f"Dropping {len(zero_var_cols)} zero-variance columns: {zero_var_cols}")
        df_processed = df.drop(columns=zero_var_cols)
        handled_cols = zero_var_cols
        
    elif strategy == 'impute':
        log_info(f"Imputing {len(zero_var_cols)} zero-variance columns")
        df_processed = df.copy()
        for col in zero_var_cols:
            if constant_value is not None:
                df_processed[col] = constant_value
            else:
                # Use mean if no constant specified (should be same as all values)
                df_processed[col] = df[col].mean()
            handled_cols.append(col)
    else:
        log_error(f"Unknown strategy '{strategy}' for zero variance handling")
        return df, []
        
    return df_processed, handled_cols


def handle_missing_fields(
    row: Dict[str, Any],
    required_fields: List[str],
    strategy: str = 'skip',
    impute_value: Optional[Any] = None
) -> Tuple[Dict[str, Any], bool]:
    """
    Handle missing required fields in a dataset row.
    
    Args:
        row: Dictionary representing a data row
        required_fields: List of required field names
        strategy: 'skip' to mark row for skipping, 'impute' to fill missing
        impute_value: Value to use for imputation
        
    Returns:
        Tuple of (processed row, should_skip flag)
    """
    missing = detect_missing_fields(row, required_fields)
    
    if not missing:
        return row, False
        
    if strategy == 'skip':
        log_warning(f"Row missing required fields: {missing}. Skipping row.")
        return row, True
        
    elif strategy == 'impute':
        log_info(f"Imputing missing fields: {missing}")
        row_processed = row.copy()
        for field in missing:
            if impute_value is not None:
                row_processed[field] = impute_value
            else:
                # Use None or empty string as fallback
                row_processed[field] = ""
        return row_processed, False
        
    else:
        log_error(f"Unknown strategy '{strategy}' for missing field handling")
        return row, True


def validate_dataset_fields(
    dataset: Dict[str, Any],
    required_fields: List[str]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that a dataset has all required fields and no zero-variance numeric columns.
    
    Args:
        dataset: Dictionary containing dataset data
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, details_dict)
    """
    details = {
        'missing_fields': [],
        'zero_variance_cols': [],
        'warnings': []
    }
    
    # Check required fields
    for field in required_fields:
        if field not in dataset or dataset[field] is None:
            details['missing_fields'].append(field)
            details['warnings'].append(f"Missing required field: {field}")
            
    # Check for zero variance in numeric columns if DataFrame exists
    if 'data' in dataset and dataset['data'] is not None:
        df = dataset['data']
        zero_var_cols = detect_zero_variance_columns(df)
        details['zero_variance_cols'] = zero_var_cols
        if zero_var_cols:
            details['warnings'].append(
                f"Found {len(zero_var_cols)} zero-variance columns"
            )
            
    is_valid = len(details['missing_fields']) == 0
    
    if details['warnings']:
        log_warning(f"Dataset validation warnings: {details['warnings']}")
        
    return is_valid, details


def preprocess_dataset_for_embedding(
    dataset: Dict[str, Any],
    required_fields: List[str],
    zero_var_strategy: str = 'drop',
    missing_field_strategy: str = 'skip'
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Preprocess a dataset for embedding generation, handling edge cases.
    
    Args:
        dataset: Dictionary containing dataset data
        required_fields: List of required field names (e.g., ['image', 'text'])
        zero_var_strategy: Strategy for zero-variance columns
        missing_field_strategy: Strategy for missing fields
        
    Returns:
        Tuple of (processed_dataset_or_None, processing_details)
    """
    details = {
        'original_fields': list(dataset.keys()) if isinstance(dataset, dict) else [],
        'handled_zero_variance': [],
        'skipped_rows': 0,
        'imputed_fields': [],
        'warnings': []
    }
    
    # Validate dataset
    is_valid, validation_details = validate_dataset_fields(dataset, required_fields)
    details['validation'] = validation_details
    
    if not is_valid and missing_field_strategy == 'skip':
        log_error("Dataset missing required fields and strategy is 'skip'. Cannot process.")
        return None, details
        
    # Handle missing fields if needed
    if not is_valid and missing_field_strategy == 'impute':
        # For row-by-row processing, this would be handled during iteration
        # For bulk data, we assume the data loader already filtered
        log_info("Missing fields will be handled during row processing")
        
    # Handle zero variance columns if DataFrame exists
    if 'data' in dataset and dataset['data'] is not None:
        df = dataset['data']
        df_processed, handled_cols = handle_zero_variance_columns(
            df, 
            strategy=zero_var_strategy
        )
        dataset['data'] = df_processed
        details['handled_zero_variance'] = handled_cols
        
    return dataset, details
