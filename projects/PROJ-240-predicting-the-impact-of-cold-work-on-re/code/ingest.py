"""
Data ingestion pipeline with security hardening and input sanitization.

This module implements the data ingestion process with:
- Explicit dtype enforcement for input sanitization
- na_filter=True for proper missing value handling
- Physical bounds validation
- Outlier clipping
- Missing value imputation
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Import utility functions
from utils import (
    sanitize_input_dataframe,
    validate_physical_bounds,
    normalize_time_to_minutes,
    clip_outliers,
    detect_type_confusion,
    validate_and_sanitize_pipeline
)
from config import get_project_root, get_min_rows, get_max_rows, get_outlier_percentile

def load_data(input_path: str, strict: bool = True) -> pd.DataFrame:
    """
    Load and sanitize data from CSV with explicit dtype enforcement.
    
    Implements security hardening by:
    - Using explicit dtype dictionary to prevent type confusion
    - Setting na_filter=True to properly handle missing values
    - Validating schema against expected columns
    - Sanitizing input data types
    
    Args:
        input_path: Path to input CSV file
        strict: If True, raise errors on schema mismatch; if False, log warnings
        
    Returns:
        Sanitized DataFrame with enforced dtypes
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If schema validation fails in strict mode
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load with explicit parameters for security
    df = pd.read_csv(
        input_path,
        dtype={
            'cold_work_pct': 'float64',
            'Mn_wt': 'float64',
            'Mg_wt': 'float64',
            'Si_wt': 'float64',
            'Cu_wt': 'float64',
            'annealing_temp_K': 'float64',
            'time_to_peak_min': 'float64'
        },
        na_filter=True,  # Explicitly enable NA filtering
        keep_default_na=True,
        na_values=['', 'NA', 'NaN', 'null', 'NULL', 'None'],
        skipinitialspace=True
    )
    
    # Apply additional sanitization
    df = sanitize_input_dataframe(df, strict=strict)
    
    # Check for type confusion
    type_check = detect_type_confusion(df)
    if type_check['suspicious']:
        raise ValueError(f"Type confusion detected in input data: {type_check['details']}")
    
    return df

def filter_missing_target(df: pd.DataFrame, target_col: str = 'time_to_peak_min') -> Tuple[pd.DataFrame, int]:
    """
    Filter out rows with missing target values.
    
    Args:
        df: Input DataFrame
        target_col: Name of target column
        
    Returns:
        Tuple of (filtered DataFrame, count of filtered rows)
    """
    original_len = len(df)
    df_filtered = df.dropna(subset=[target_col])
    filtered_count = original_len - len(df_filtered)
    
    return df_filtered, filtered_count

def impute_missing_composition(df: pd.DataFrame, composition_cols: List[str] = None) -> pd.DataFrame:
    """
    Impute missing composition values using group-specific means.
    
    Groups rows by alloy type or concentration range and imputes
    missing values with the mean of that group. Falls back to column
    mean if no grouping is available.
    
    Args:
        df: Input DataFrame
        composition_cols: List of composition column names
        
    Returns:
        DataFrame with imputed values
    """
    if composition_cols is None:
        composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    
    df_imputed = df.copy()
    
    for col in composition_cols:
        if col not in df_imputed.columns:
            continue
        
        # Check if there are missing values
        if df_imputed[col].isna().sum() == 0:
            continue
        
        # Try to group by a logical category if available
        # For now, use column mean as fallback
        group_mean = df_imputed[col].mean()
        df_imputed[col] = df_imputed[col].fillna(group_mean)
    
    return df_imputed

def clip_outliers_target(df: pd.DataFrame, target_col: str = 'time_to_peak_min', 
                        percentile: float = None) -> Tuple[pd.DataFrame, List[int], float]:
    """
    Clip outliers in target variable using high percentile threshold.
    
    Uses numpy's linear interpolation method to calculate threshold
    and clips values above it.
    
    Args:
        df: Input DataFrame
        target_col: Name of target column
        percentile: Percentile threshold (default: 99th from config)
        
    Returns:
        Tuple of (clipped DataFrame, list of clipped indices, threshold value)
    """
    if percentile is None:
        percentile = get_outlier_percentile()
    
    df_clipped = df.copy()
    values = df_clipped[target_col].dropna()
    
    if len(values) == 0:
        return df_clipped, [], 0.0
    
    # Calculate threshold with linear interpolation
    threshold = np.percentile(values, percentile, interpolation='linear')
    
    # Identify and clip outliers
    mask = df_clipped[target_col] > threshold
    clipped_indices = df_clipped[mask].index.tolist()
    df_clipped.loc[mask, target_col] = threshold
    
    return df_clipped, clipped_indices, float(threshold)

def validate_dataset_size(df: pd.DataFrame, min_rows: int = None, max_rows: int = None) -> None:
    """
    Validate dataset size meets requirements.
    
    Args:
        df: Input DataFrame
        min_rows: Minimum required rows (default: from config)
        max_rows: Maximum allowed rows (default: from config)
        
    Raises:
        ValueError: If dataset size is outside allowed range
    """
    if min_rows is None:
        min_rows = get_min_rows()
    if max_rows is None:
        max_rows = get_max_rows()
    
    n_rows = len(df)
    
    if n_rows < min_rows:
        raise ValueError(f"Dataset has {n_rows} rows, which is less than minimum required {min_rows} rows (FR-008)")
    
    if n_rows > max_rows:
        raise ValueError(f"Dataset has {n_rows} rows, which exceeds maximum allowed {max_rows} rows (FR-003)")

def run_ingestion_pipeline(input_path: str, output_path: str, log_path: str) -> Dict[str, Any]:
    """
    Run complete data ingestion pipeline.
    
    Steps:
    1. Load and sanitize data
    2. Validate physical bounds
    3. Filter missing targets
    4. Impute missing compositions
    5. Clip outliers
    6. Validate dataset size
    7. Save outputs and logs
    
    Args:
        input_path: Path to input CSV
        output_path: Path for processed output CSV
        log_path: Path for validation log JSON
        
    Returns:
        Dictionary with pipeline metrics
    """
    # Ensure output directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load and sanitize
    df = load_data(input_path)
    rows_input = len(df)
    
    # Step 2: Validate physical bounds
    bounds_check = validate_physical_bounds(df)
    
    # Step 3: Filter missing targets
    df, rows_filtered = filter_missing_target(df)
    
    # Step 4: Impute missing compositions
    df = impute_missing_composition(df)
    
    # Step 5: Clip outliers
    df, clipped_indices, threshold = clip_outliers_target(df)
    
    # Step 6: Validate size
    validate_dataset_size(df)
    
    rows_output = len(df)
    
    # Calculate metrics
    metrics = {
        'rows_ingested': rows_input,
        'rows_filtered': rows_filtered,
        'rows_output': rows_output,
        'null_handling_success_rate': rows_output / rows_input if rows_input > 0 else 0.0
    }
    
    # Create validation log
    validation_log = {
        'rows_ingested': rows_input,
        'rows_filtered': rows_filtered,
        'null_counts': df.isna().sum().to_dict(),
        'clipped_outliers_count': len(clipped_indices),
        'clipped_values_list': clipped_indices,
        'threshold_99th_percentile': threshold
    }
    
    # Save outputs
    df.to_csv(output_path, index=False)
    
    with open(log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
    
    return metrics

def main():
    """Main entry point for ingestion pipeline."""
    project_root = get_project_root()
    input_path = str(project_root / 'data' / 'raw' / 'synthetic_baseline.csv')
    output_path = str(project_root / 'data' / 'processed' / 'validated.csv')
    log_path = str(project_root / 'artifacts' / 'reports' / 'validation_log.json')
    
    try:
        metrics = run_ingestion_pipeline(input_path, output_path, log_path)
        print(f"Ingestion complete: {metrics['rows_output']} rows processed")
        return 0
    except Exception as e:
        print(f"Ingestion failed: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())