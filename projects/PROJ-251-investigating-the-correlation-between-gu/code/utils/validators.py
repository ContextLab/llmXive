"""
Schema validators for dataset, correlation, and model metrics.

This module provides validation functions to ensure data integrity
across the pipeline's output files.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

# Dataset Schema Requirements
DATASET_REQUIRED_COLUMNS = {
    'subject_id',
    'titer_baseline',
    'titer_post',
    'seroconversion',  # Boolean or 0/1
    'shannon_diversity'
}

# Correlation Results Schema Requirements
CORRELATION_REQUIRED_COLUMNS = {
    'taxon_id',
    'correlation_coefficient',
    'p_value_raw',
    'p_value_adj'
}

# Model Metrics Schema Requirements
MODEL_METRICS_REQUIRED_KEYS = {
    'accuracy',
    'precision',
    'recall',
    'f1_score',
    'confusion_matrix',
    'cv_folds',
    'feature_selection_method',
    'null_distribution_p_value'
}

# Model Metrics Schema Requirements (JSON structure)
MODEL_METRICS_REQUIRED_FIELDS = {
    'accuracy': (int, float),
    'precision': (int, float),
    'recall': (int, float),
    'f1_score': (int, float),
    'cv_folds': int,
    'feature_selection_method': str,
    'null_distribution_p_value': (int, float)
}

MODEL_METRICS_CONFUSION_MATRIX_SHAPE = (2, 2)

def validate_dataset_schema(df: pd.DataFrame, strict: bool = True) -> Dict[str, Any]:
    """
    Validate that a DataFrame conforms to the expected dataset schema.
    
    Args:
        df: DataFrame to validate
        strict: If True, raise ValueError on missing columns. If False, return 
               a report with missing columns.
    
    Returns:
        Dict with validation results:
            - valid: bool
            - missing_columns: List[str] (if any)
            - row_count: int
            - null_counts: Dict[str, int] (for required columns)
    
    Raises:
        ValueError: If strict=True and required columns are missing
    """
    if not isinstance(df, pd.DataFrame):
        if strict:
            raise ValueError("Input must be a pandas DataFrame")
        return {
            'valid': False,
            'error': 'Input must be a pandas DataFrame',
            'missing_columns': [],
            'row_count': 0,
            'null_counts': {}
        }
    
    missing_columns = []
    null_counts = {}
    
    for col in DATASET_REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
        else:
            null_counts[col] = int(df[col].isna().sum())
    
    if missing_columns:
        if strict:
            raise ValueError(f"Dataset missing required columns: {missing_columns}")
        return {
            'valid': False,
            'missing_columns': missing_columns,
            'row_count': len(df),
            'null_counts': null_counts
        }
    
    # Check for nulls in required columns
    has_nulls = any(count > 0 for count in null_counts.values())
    
    return {
        'valid': not has_nulls,
        'missing_columns': [],
        'row_count': len(df),
        'null_counts': null_counts,
        'warning': 'Contains null values in required columns' if has_nulls else None
    }

def validate_correlation_results_schema(df: pd.DataFrame, strict: bool = True) -> Dict[str, Any]:
    """
    Validate that correlation results DataFrame conforms to expected schema.
    
    Args:
        df: DataFrame to validate
        strict: If True, raise ValueError on missing columns.
    
    Returns:
        Dict with validation results.
    
    Raises:
        ValueError: If strict=True and required columns are missing or invalid.
    """
    if not isinstance(df, pd.DataFrame):
        if strict:
            raise ValueError("Input must be a pandas DataFrame")
        return {
            'valid': False,
            'error': 'Input must be a pandas DataFrame',
            'missing_columns': [],
            'row_count': 0
        }
    
    missing_columns = []
    
    for col in CORRELATION_REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        if strict:
            raise ValueError(f"Correlation results missing required columns: {missing_columns}")
        return {
            'valid': False,
            'missing_columns': missing_columns,
            'row_count': len(df)
        }
    
    # Validate p-value ranges
    invalid_pvalues = []
    for col in ['p_value_raw', 'p_value_adj']:
        if col in df.columns:
            if (df[col] < 0).any() or (df[col] > 1).any():
                invalid_pvalues.append(col)
    
    if invalid_pvalues:
        if strict:
            raise ValueError(f"P-values out of range [0, 1] in columns: {invalid_pvalues}")
        return {
            'valid': False,
            'missing_columns': [],
            'row_count': len(df),
            'warning': f'P-values out of range in: {invalid_pvalues}'
        }
    
    return {
        'valid': True,
        'missing_columns': [],
        'row_count': len(df)
    }

def validate_model_metrics_schema(metrics: Dict[str, Any], strict: bool = True) -> Dict[str, Any]:
    """
    Validate that model metrics dictionary conforms to expected schema.
    
    Args:
        metrics: Dictionary containing model metrics
        strict: If True, raise ValueError on missing/invalid fields.
    
    Returns:
        Dict with validation results.
    
    Raises:
        ValueError: If strict=True and validation fails.
    """
    if not isinstance(metrics, dict):
        if strict:
            raise ValueError("Input must be a dictionary")
        return {
            'valid': False,
            'error': 'Input must be a dictionary',
            'missing_fields': [],
            'invalid_fields': []
        }
    
    missing_fields = []
    invalid_fields = []
    
    # Check required top-level keys
    for key in MODEL_METRICS_REQUIRED_KEYS:
        if key not in metrics:
            missing_fields.append(key)
    
    # Validate field types and ranges
    for key, expected_types in MODEL_METRICS_REQUIRED_FIELDS.items():
        if key in metrics:
            value = metrics[key]
            if not isinstance(value, expected_types):
                invalid_fields.append(key)
            elif key in ['accuracy', 'precision', 'recall', 'f1_score']:
                if not (0 <= value <= 1):
                    invalid_fields.append(f"{key} (out of range [0,1])")
            elif key == 'cv_folds':
                if value < 2:
                    invalid_fields.append(f"{key} (must be >= 2)")
    
    # Validate confusion matrix structure
    if 'confusion_matrix' in metrics:
        cm = metrics['confusion_matrix']
        if not isinstance(cm, (list, np.ndarray)):
            invalid_fields.append('confusion_matrix (not a list/array)')
        elif isinstance(cm, list):
            try:
                cm_array = np.array(cm)
                if cm_array.shape != MODEL_METRICS_CONFUSION_MATRIX_SHAPE:
                    invalid_fields.append(f'confusion_matrix (wrong shape: {cm_array.shape})')
            except:
                invalid_fields.append('confusion_matrix (invalid array)')
        elif isinstance(cm, np.ndarray):
            if cm.shape != MODEL_METRICS_CONFUSION_MATRIX_SHAPE:
                invalid_fields.append(f'confusion_matrix (wrong shape: {cm.shape})')
    
    if missing_fields or invalid_fields:
        if strict:
            error_parts = []
            if missing_fields:
                error_parts.append(f"Missing fields: {missing_fields}")
            if invalid_fields:
                error_parts.append(f"Invalid fields: {invalid_fields}")
            raise ValueError(f"Model metrics validation failed: {'; '.join(error_parts)}")
        return {
            'valid': False,
            'missing_fields': missing_fields,
            'invalid_fields': invalid_fields
        }
    
    return {
        'valid': True,
        'missing_fields': [],
        'invalid_fields': []
    }

def validate_file_exists(filepath: str, strict: bool = True) -> Dict[str, Any]:
    """
    Validate that a file exists at the given path.
    
    Args:
        filepath: Path to the file
        strict: If True, raise FileNotFoundError if file doesn't exist.
    
    Returns:
        Dict with validation results.
    
    Raises:
        FileNotFoundError: If strict=True and file doesn't exist.
    """
    path = Path(filepath)
    
    if not path.exists():
        if strict:
            raise FileNotFoundError(f"File not found: {filepath}")
        return {
            'valid': False,
            'error': f"File not found: {filepath}",
            'path': filepath
        }
    
    return {
        'valid': True,
        'path': str(path),
        'size_bytes': path.stat().st_size
    }

def validate_dataframe_not_empty(df: pd.DataFrame, min_rows: int = 1, strict: bool = True) -> Dict[str, Any]:
    """
    Validate that a DataFrame has at least min_rows rows.
    
    Args:
        df: DataFrame to validate
        min_rows: Minimum number of rows required
        strict: If True, raise ValueError if not enough rows.
    
    Returns:
        Dict with validation results.
    
    Raises:
        ValueError: If strict=True and DataFrame has fewer than min_rows.
    """
    row_count = len(df)
    
    if row_count < min_rows:
        if strict:
            raise ValueError(f"DataFrame has {row_count} rows, minimum required: {min_rows}")
        return {
            'valid': False,
            'row_count': row_count,
            'min_required': min_rows
        }
    
    return {
        'valid': True,
        'row_count': row_count,
        'min_required': min_rows
    }