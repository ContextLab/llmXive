"""
Sanity check module for verifying dataset integrity.
Ensures that merged datasets contain real measured values and not synthetic placeholders.
"""
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np

# Import project configuration and logging utilities
from utils.logging_config import get_logger
from utils.config import DATA_PROCESSED_PATH

logger = get_logger(__name__)

# Constants for detection
SYNTHETIC_PATTERNS = [
    r'^fake_',
    r'^synthetic_',
    r'^mock_',
    r'^placeholder_',
    r'^test_data_',
    r'^random_',
    r'^generated_',
    r'^dummy_'
]

FAKE_ID_PATTERNS = [
    r'^FAKE_ID_\d+$',
    r'^TEST_ID_\d+$',
    r'^MOCK_ID_\d+$',
    r'^0+$',  # All zeros
    r'^NA+$', # All NA strings
    r'^NULL+$'
]

SUSPICIOUS_STATISTICAL_THRESHOLDS = {
    'constant_ratio': 0.99,  # If >99% of values are identical
    'zero_variance': 1e-10,
    'perfect_correlation': 0.9999
}

def detect_synthetic_column_names(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with names suggesting synthetic or fake data.
    
    Args:
        df: DataFrame to check
        
    Returns:
        List of column names matching synthetic patterns
    """
    synthetic_cols = []
    for col in df.columns:
        col_str = str(col).lower()
        for pattern in SYNTHETIC_PATTERNS:
            if re.search(pattern, col_str):
                synthetic_cols.append(col)
                logger.warning(f"Detected potentially synthetic column name: {col}")
                break
    return synthetic_cols

def detect_constant_fake_ids(df: pd.DataFrame, id_columns: Optional[List[str]] = None) -> List[str]:
    """
    Detect columns that appear to be fake IDs (constant or following fake patterns).
    
    Args:
        df: DataFrame to check
        id_columns: Specific columns to check as IDs. If None, checks all object/string columns.
        
    Returns:
        List of column names identified as fake IDs
    """
    fake_id_cols = []
    
    if id_columns is None:
        # Check all object and string columns
        id_columns = [col for col in df.columns if df[col].dtype == 'object' or df[col].dtype == 'string']
    
    for col in id_columns:
        if col not in df.columns:
            continue
            
        unique_vals = df[col].unique()
        unique_count = len(unique_vals)
        total_count = len(df)
        
        # Check if column is constant
        if unique_count == 1:
            val = unique_vals[0]
            if isinstance(val, str):
                for pattern in FAKE_ID_PATTERNS:
                    if re.match(pattern, val):
                        fake_id_cols.append(col)
                        logger.warning(f"Detected constant fake ID column: {col} with value '{val}'")
                        break
            elif pd.isna(val) or val == '':
                fake_id_cols.append(col)
                logger.warning(f"Detected constant fake ID column: {col} with null/empty value")
            continue
        
        # Check if all values match fake patterns
        fake_pattern_count = 0
        for val in unique_vals:
            if isinstance(val, str):
                for pattern in FAKE_ID_PATTERNS:
                    if re.match(pattern, val):
                        fake_pattern_count += 1
                        break
        
        if fake_pattern_count == unique_count:
            fake_id_cols.append(col)
            logger.warning(f"Detected column {col} with all values matching fake ID patterns")
    
    return fake_id_cols

def detect_constant_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect numeric columns that are constant or have near-zero variance.
    
    Args:
        df: DataFrame to check
        
    Returns:
        List of column names with constant or suspiciously low variance
    """
    constant_cols = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if df[col].isna().all():
            continue  # Skip all-NA columns
            
        # Calculate variance
        var = df[col].var()
        
        if var == 0:
            constant_cols.append(col)
            logger.warning(f"Detected constant numeric column: {col} (variance = 0)")
        elif var < SUSPICIOUS_STATISTICAL_THRESHOLDS['zero_variance']:
            # Check if it's actually constant due to rounding
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) <= 2:
                constant_cols.append(col)
                logger.warning(f"Detected near-constant numeric column: {col} (variance = {var}, unique values = {len(unique_vals)})")
    
    return constant_cols

def detect_suspicious_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect various suspicious statistical patterns that might indicate synthetic data.
    
    Args:
        df: DataFrame to check
        
    Returns:
        Dictionary with detection results
    """
    results = {
        'constant_ratio_columns': [],
        'perfect_correlation_pairs': [],
        'all_nan_columns': [],
        'suspicious_summary': {}
    }
    
    # Check for constant ratio columns
    for col in df.columns:
        if df[col].isna().all():
            results['all_nan_columns'].append(col)
            continue
            
        non_na = df[col].dropna()
        if len(non_na) == 0:
            continue
            
        unique_count = len(non_na.unique())
        total_count = len(non_na)
        constant_ratio = unique_count / total_count if total_count > 0 else 0
        
        if constant_ratio < SUSPICIOUS_STATISTICAL_THRESHOLDS['constant_ratio']:
            results['constant_ratio_columns'].append({
                'column': col,
                'ratio': constant_ratio,
                'unique_values': unique_count,
                'total_values': total_count
            })
            logger.warning(f"Column {col} has suspiciously low unique value ratio: {constant_ratio:.4f}")
    
    # Check for perfect correlations between numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] > 1:
        corr_matrix = numeric_df.corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = abs(corr_matrix.iloc[i, j])
                if corr_val >= SUSPICIOUS_STATISTICAL_THRESHOLDS['perfect_correlation']:
                    results['perfect_correlation_pairs'].append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
                    logger.warning(f"Perfect correlation detected between {corr_matrix.columns[i]} and {corr_matrix.columns[j]}: {corr_val:.6f}")
    
    return results

def validate_dataset_integrity(df: pd.DataFrame, source_file: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Perform comprehensive integrity validation on the dataset.
    
    Args:
        df: DataFrame to validate
        source_file: Optional source file path for logging
        
    Returns:
        Tuple of (is_valid, details_dict)
    """
    details = {
        'source_file': source_file,
        'row_count': len(df),
        'column_count': len(df.columns),
        'issues': [],
        'warnings': [],
        'passed_checks': []
    }
    
    is_valid = True
    
    # Check 1: Synthetic column names
    synthetic_cols = detect_synthetic_column_names(df)
    if synthetic_cols:
        details['issues'].append({
            'type': 'synthetic_column_names',
            'columns': synthetic_cols,
            'message': f"Found {len(synthetic_cols)} columns with synthetic-looking names"
        })
        is_valid = False
    else:
        details['passed_checks'].append('No synthetic column names detected')
    
    # Check 2: Fake ID columns
    fake_id_cols = detect_constant_fake_ids(df)
    if fake_id_cols:
        details['issues'].append({
            'type': 'fake_id_columns',
            'columns': fake_id_cols,
            'message': f"Found {len(fake_id_cols)} columns with fake ID patterns"
        })
        is_valid = False
    else:
        details['passed_checks'].append('No fake ID columns detected')
    
    # Check 3: Constant numeric columns
    constant_num_cols = detect_constant_numeric_columns(df)
    if constant_num_cols:
        details['warnings'].append({
            'type': 'constant_numeric_columns',
            'columns': constant_num_cols,
            'message': f"Found {len(constant_num_cols)} constant numeric columns"
        })
        # This is a warning, not a failure, but we log it
        logger.warning(f"Dataset contains {len(constant_num_cols)} constant numeric columns")
    else:
        details['passed_checks'].append('No constant numeric columns detected')
    
    # Check 4: Suspicious statistical patterns
    suspicious_patterns = detect_suspicious_patterns(df)
    if suspicious_patterns['perfect_correlation_pairs']:
        details['warnings'].append({
            'type': 'perfect_correlations',
            'pairs': suspicious_patterns['perfect_correlation_pairs'],
            'message': f"Found {len(suspicious_patterns['perfect_correlation_pairs'])} pairs with perfect correlation"
        })
    
    if suspicious_patterns['all_nan_columns']:
        details['warnings'].append({
            'type': 'all_nan_columns',
            'columns': suspicious_patterns['all_nan_columns'],
            'message': f"Found {len(suspicious_patterns['all_nan_columns'])} columns with all NaN values"
        })
    
    # Check 5: Basic data existence
    if len(df) == 0:
        details['issues'].append({
            'type': 'empty_dataset',
            'message': 'Dataset is empty'
        })
        is_valid = False
    
    if len(df.columns) == 0:
        details['issues'].append({
            'type': 'no_columns',
            'message': 'Dataset has no columns'
        })
        is_valid = False
    
    # Check 6: Verify no random generation artifacts
    # Look for columns that might be from np.random or similar
    for col in df.columns:
        if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
            # Check for suspiciously round numbers or patterns
            non_na = df[col].dropna()
            if len(non_na) > 10:
                # Check if values are suspiciously uniform
                if non_na.nunique() == 1:
                    val = non_na.iloc[0]
                    if val == 0.0 or val == 1.0 or val == 10.0:
                        details['warnings'].append({
                            'type': 'suspicious_constant',
                            'column': col,
                            'value': val,
                            'message': f"Column {col} is constant with value {val}"
                        })
    
    return is_valid, details

def main():
    """
    Main function to run sanity checks on the processed dataset.
    """
    logger.info("Starting dataset sanity check...")
    
    # Determine the processed data file
    processed_path = Path(DATA_PROCESSED_PATH)
    
    # Look for the most recent processed file
    possible_files = [
        processed_path / "merged_proteomic_transcriptomic.csv",
        processed_path / "processed_data.csv",
        processed_path / "merged_data.csv"
    ]
    
    data_file = None
    for file_path in possible_files:
        if file_path.exists():
            data_file = file_path
            break
    
    if data_file is None:
        # Try to find any CSV in the processed directory
        csv_files = list(processed_path.glob("*.csv"))
        if csv_files:
            data_file = csv_files[-1]  # Use the most recent
        else:
            logger.error("No processed data file found. Please run the data ingestion pipeline first.")
            sys.exit(1)
    
    logger.info(f"Loading data from: {data_file}")
    
    try:
        df = pd.read_csv(data_file)
    except Exception as e:
        logger.error(f"Failed to load data file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    
    # Run validation
    is_valid, details = validate_dataset_integrity(df, source_file=str(data_file))
    
    # Report results
    logger.info("=" * 50)
    logger.info("SANITY CHECK RESULTS")
    logger.info("=" * 50)
    logger.info(f"Dataset: {data_file}")
    logger.info(f"Rows: {details['row_count']}, Columns: {details['column_count']}")
    logger.info(f"Overall Status: {'PASSED' if is_valid else 'FAILED'}")
    logger.info("-" * 50)
    
    if details['passed_checks']:
        logger.info("Passed checks:")
        for check in details['passed_checks']:
            logger.info(f"  ✓ {check}")
    
    if details['warnings']:
        logger.warning("Warnings:")
        for warning in details['warnings']:
            logger.warning(f"  ⚠ {warning['message']}")
    
    if details['issues']:
        logger.error("Issues detected:")
        for issue in details['issues']:
            logger.error(f"  ✗ {issue['message']}")
        logger.error(f"  Total issues: {len(details['issues'])}")
    
    logger.info("=" * 50)
    
    if not is_valid:
        logger.error("SANITY CHECK FAILED: Synthetic or fake data detected!")
        logger.error("The dataset contains values that appear to be synthetic placeholders.")
        logger.error("Please review the issues listed above and ensure real data is being used.")
        sys.exit(1)
    
    logger.info("SANITY CHECK PASSED: Dataset appears to contain real measured values.")
    sys.exit(0)

if __name__ == "__main__":
    main()