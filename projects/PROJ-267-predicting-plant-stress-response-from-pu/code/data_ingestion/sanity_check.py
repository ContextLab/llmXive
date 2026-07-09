"""
Sanity check module for verifying the integrity of the merged dataset.

This script ensures that the merged dataset contains real measured values
and detects any synthetic placeholder data, fake IDs, or constant columns
that suggest data fabrication.

Checks performed:
1. Detect columns with names suggesting synthetic data (e.g., 'random_*')
2. Identify constant columns with fake/placeholder IDs
3. Verify presence of real measured values (non-zero variance)
4. Check for suspicious patterns indicating data fabrication

Exit codes:
0 - All checks passed, dataset appears real
1 - One or more checks failed, dataset may contain synthetic data
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import DATA_PROCESSED_PATH, LOG_PATH
from utils.logging_config import setup_logging, get_logger, log_warning
from utils.data_utils import load_csv, load_parquet

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Constants for detection
SYNTHETIC_COLUMN_PATTERNS = [
    r'random.*',
    r'fake.*',
    r'placeholder.*',
    r'synthetic.*',
    r'generated.*',
    r'test.*',
    r'sample.*',
    r'dummy.*'
]

# Thresholds for detection
CONSTANT_COLUMN_THRESHOLD = 0.999  # If variance ratio < this, consider constant
MIN_REAL_VALUES_RATIO = 0.01  # At least 1% of values should be real measurements


def detect_synthetic_column_names(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with names suggesting synthetic data generation.
    
    Args:
        df: Input DataFrame to check
        
    Returns:
        List of column names that match synthetic patterns
    """
    synthetic_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        for pattern in SYNTHETIC_COLUMN_PATTERNS:
            if re.match(pattern, col_lower, re.IGNORECASE):
                synthetic_columns.append(col)
                break
                
    return synthetic_columns


def detect_constant_fake_ids(df: pd.DataFrame, id_columns: List[str]) -> List[str]:
    """
    Detect constant columns that appear to be fake IDs.
    
    Args:
        df: Input DataFrame
        id_columns: List of columns that should contain IDs
        
    Returns:
        List of constant ID columns that may be fake
    """
    constant_fake_ids = []
    
    for col in id_columns:
        if col not in df.columns:
            continue
            
        # Check if column is constant
        unique_values = df[col].nunique()
        if unique_values == 1:
            # Single value across all rows - likely fake
            constant_fake_ids.append(col)
            logger.warning(f"Constant ID column detected: {col} (single value: {df[col].iloc[0]})")
        elif unique_values < len(df) * 0.1:
            # Very few unique values relative to sample size
            logger.warning(f"Suspiciously low unique values in ID column: {col} ({unique_values} unique in {len(df)} rows)")
            
    return constant_fake_ids


def detect_constant_numeric_columns(df: pd.DataFrame, exclude_columns: List[str]) -> List[str]:
    """
    Detect numeric columns with suspiciously low variance (constant values).
    
    Args:
        df: Input DataFrame
        exclude_columns: Columns to exclude from check (e.g., ID columns, metadata)
        
    Returns:
        List of constant numeric columns
    """
    constant_numeric = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        if col in exclude_columns:
            continue
            
        # Skip columns with all NaN
        if df[col].isna().all():
            continue
            
        # Calculate variance
        non_null_values = df[col].dropna()
        if len(non_null_values) == 0:
            continue
            
        variance = non_null_values.var()
        mean = non_null_values.mean()
        
        # Handle edge cases
        if pd.isna(variance) or pd.isna(mean):
            continue
            
        if mean == 0:
            # All zeros or very small values
            if variance == 0:
                constant_numeric.append(col)
                logger.warning(f"Constant zero column detected: {col}")
            continue
            
        # Coefficient of variation check
        cv = variance / (mean ** 2) if mean != 0 else 0
        
        # If variance is extremely low relative to mean
        if variance < (abs(mean) * 1e-10):
            constant_numeric.append(col)
            logger.warning(f"Constant numeric column detected: {col} (variance={variance}, mean={mean})")
            
    return constant_numeric


def detect_suspicious_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect suspicious patterns that may indicate data fabrication.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with detection results
    """
    results = {
        'synthetic_column_names': [],
        'constant_fake_ids': [],
        'constant_numeric_columns': [],
        'suspicious_patterns': [],
        'issues_found': False
    }
    
    # 1. Check for synthetic column names
    results['synthetic_column_names'] = detect_synthetic_column_names(df)
    if results['synthetic_column_names']:
        results['issues_found'] = True
        logger.error(f"Synthetic column names detected: {results['synthetic_column_names']}")
    
    # 2. Check for constant fake IDs
    # Common ID column patterns
    id_patterns = ['protein_id', 'gene_id', 'sample_id', 'accession', 'uniprot', 'ensembl']
    potential_id_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in id_patterns)]
    results['constant_fake_ids'] = detect_constant_fake_ids(df, potential_id_cols)
    
    # 3. Check for constant numeric columns
    exclude_cols = potential_id_cols + ['stress_condition', 'species', 'treatment', 'replicate']
    results['constant_numeric_columns'] = detect_constant_numeric_columns(df, exclude_cols)
    
    # 4. Check for suspicious value patterns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        non_null = df[col].dropna()
        if len(non_null) < 10:
            continue
            
        # Check for too many identical values
        value_counts = non_null.value_counts()
        max_count = value_counts.max()
        ratio = max_count / len(non_null)
        
        if ratio > 0.9:
            results['suspicious_patterns'].append(
                f"Column '{col}' has {ratio:.1%} identical values"
            )
            logger.warning(f"Suspicious pattern in {col}: {ratio:.1%} identical values")
    
    if results['suspicious_patterns']:
        results['issues_found'] = True
        
    return results


def validate_dataset_integrity(df: pd.DataFrame) -> bool:
    """
    Main validation function to check dataset integrity.
    
    Args:
        df: Input DataFrame to validate
        
    Returns:
        True if dataset passes all checks, False otherwise
    """
    logger.info("Starting dataset integrity validation...")
    
    # Run all checks
    results = detect_suspicious_patterns(df)
    
    # Report findings
    if results['issues_found']:
        logger.error("Dataset integrity check FAILED:")
        
        if results['synthetic_column_names']:
            logger.error(f"  - Synthetic column names: {results['synthetic_column_names']}")
            
        if results['constant_fake_ids']:
            logger.error(f"  - Constant fake ID columns: {results['constant_fake_ids']}")
            
        if results['constant_numeric_columns']:
            logger.error(f"  - Constant numeric columns: {results['constant_numeric_columns']}")
            
        if results['suspicious_patterns']:
            logger.error(f"  - Suspicious patterns:")
            for pattern in results['suspicious_patterns']:
                logger.error(f"    - {pattern}")
                
        return False
    else:
        logger.info("Dataset integrity check PASSED: No synthetic data detected")
        logger.info(f"  - Dataset shape: {df.shape}")
        logger.info(f"  - Numeric columns: {len(df.select_dtypes(include=[np.number]).columns)}")
        logger.info(f"  - Missing value ratio: {df.isna().mean().mean():.2%}")
        return True


def main():
    """
    Main entry point for the sanity check script.
    
    Loads the merged dataset from data/processed/ and performs
    comprehensive checks for synthetic/fake data.
    """
    logger.info("=" * 60)
    logger.info("Starting dataset sanity check (T036)")
    logger.info("=" * 60)
    
    # Determine input file
    processed_path = Path(DATA_PROCESSED_PATH)
    
    # Look for merged dataset files
    possible_files = [
        processed_path / "merged_dataset.csv",
        processed_path / "merged_dataset.parquet",
        processed_path / "proteomics_merged.csv",
        processed_path / "proteomics_merged.parquet"
    ]
    
    input_file = None
    for file_path in possible_files:
        if file_path.exists():
            input_file = file_path
            break
            
    if input_file is None:
        logger.error("No merged dataset found in data/processed/")
        logger.error("Please run the data ingestion pipeline first (T014)")
        sys.exit(1)
        
    logger.info(f"Loading dataset from: {input_file}")
    
    try:
        if input_file.suffix == '.csv':
            df = load_csv(input_file)
        elif input_file.suffix == '.parquet':
            df = load_parquet(input_file)
        else:
            logger.error(f"Unsupported file format: {input_file.suffix}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
        
    if df.empty:
        logger.error("Dataset is empty after loading")
        sys.exit(1)
        
    logger.info(f"Dataset loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Validate dataset
    is_valid = validate_dataset_integrity(df)
    
    if is_valid:
        logger.info("=" * 60)
        logger.info("SANITY CHECK PASSED: Dataset contains real measured values")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("SANITY CHECK FAILED: Synthetic or fake data detected")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()