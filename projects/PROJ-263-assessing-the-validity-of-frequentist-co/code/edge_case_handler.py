import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_log_level, get_data_dir
from data_cleaner import validate_dataset_sufficiency

# Configure logging based on project settings
log_level = get_log_level()
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

MIN_ROWS_THRESHOLD = 50
MIN_CONTINUOUS_VARS = 1


def check_categorical_variables(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that appear to be categorical based on dtype or low cardinality.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of column names identified as categorical
    """
    categorical_cols = []
    
    for col in df.columns:
        # Check if dtype is object or string (explicitly categorical)
        if df[col].dtype == 'object' or df[col].dtype.name.startswith('string'):
            categorical_cols.append(col)
            continue
        
        # Check for integer columns with very low cardinality (potential categories)
        if pd.api.types.is_integer_dtype(df[col]):
            unique_count = df[col].nunique()
            total_count = len(df)
            # If unique values are very few compared to total, likely categorical
            if unique_count < 10 and unique_count / total_count < 0.05:
                categorical_cols.append(col)
                continue
                
    return categorical_cols


def validate_dataset_rows(dataset_info: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a dataset has sufficient rows for simulation.
    
    Args:
        dataset_info: Dictionary containing 'dataset_id' and 'df' (DataFrame)
        
    Returns:
        Tuple of (is_valid, reason_message)
    """
    dataset_id = dataset_info.get('dataset_id', 'unknown')
    df = dataset_info.get('df')
    
    if df is None:
        return False, f"Dataset {dataset_id} has no data."
        
    row_count = len(df)
    
    if row_count < MIN_ROWS_THRESHOLD:
        reason = f"Dataset {dataset_id} has {row_count} rows, which is below the minimum threshold of {MIN_ROWS_THRESHOLD}."
        logger.warning(reason)
        return False, reason
        
    logger.info(f"Dataset {dataset_id} has {row_count} rows, which meets the minimum threshold.")
    return True, f"Dataset {dataset_id} has sufficient rows ({row_count})."


def validate_continuous_variables(dataset_info: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a dataset has at least one continuous numeric variable.
    
    Args:
        dataset_info: Dictionary containing 'dataset_id' and 'df' (DataFrame)
        
    Returns:
        Tuple of (is_valid, reason_message)
    """
    dataset_id = dataset_info.get('dataset_id', 'unknown')
    df = dataset_info.get('df')
    
    if df is None:
        return False, f"Dataset {dataset_id} has no data."
        
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < MIN_CONTINUOUS_VARS:
        reason = f"Dataset {dataset_id} has {len(numeric_cols)} numeric columns, but needs at least {MIN_CONTINUOUS_VARS}."
        logger.warning(reason)
        return False, reason
        
    logger.info(f"Dataset {dataset_id} has {len(numeric_cols)} numeric columns.")
    return True, f"Dataset {dataset_id} has sufficient numeric variables ({len(numeric_cols)})."


def handle_edge_cases(dataset_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive edge case handler for a dataset.
    
    Performs the following checks:
    1. Validates row count sufficiency
    2. Identifies categorical variables
    3. Validates presence of continuous numeric variables
    4. Logs warnings for any issues found
    
    Args:
        dataset_info: Dictionary containing 'dataset_id' and 'df' (DataFrame)
        
    Returns:
        Dictionary with validation results and warnings
    """
    dataset_id = dataset_info.get('dataset_id', 'unknown')
    df = dataset_info.get('df')
    
    result = {
        'dataset_id': dataset_id,
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'categorical_columns': [],
        'numeric_columns': []
    }
    
    if df is None:
        result['is_valid'] = False
        result['errors'].append("Dataset is None")
        return result
        
    # 1. Check row count
    is_rows_valid, row_reason = validate_dataset_rows(dataset_info)
    if not is_rows_valid:
        result['is_valid'] = False
        result['errors'].append(row_reason)
    else:
        result['warnings'].append(row_reason)
        
    # 2. Check categorical variables
    categorical_cols = check_categorical_variables(df)
    result['categorical_columns'] = categorical_cols
    if categorical_cols:
        warning_msg = f"Dataset {dataset_id} contains {len(categorical_cols)} categorical columns: {categorical_cols}. These will be excluded from simulation."
        logger.warning(warning_msg)
        result['warnings'].append(warning_msg)
        
    # 3. Check continuous variables
    is_numeric_valid, numeric_reason = validate_continuous_variables(dataset_info)
    if not is_numeric_valid:
        result['is_valid'] = False
        result['errors'].append(numeric_reason)
    else:
        result['warnings'].append(numeric_reason)
        
    # Identify numeric columns for reference
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    result['numeric_columns'] = numeric_cols
    
    # Log summary
    if result['is_valid']:
        logger.info(f"Dataset {dataset_id} passed all edge case checks.")
    else:
        logger.error(f"Dataset {dataset_id} failed edge case checks: {result['errors']}")
        
    return result


def process_datasets_for_simulation(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of datasets, applying edge case handling to each.
    
    Args:
        datasets: List of dictionaries, each containing 'dataset_id' and 'df'
        
    Returns:
        List of dictionaries with validation results. Only valid datasets are included.
    """
    processed_results = []
    
    for dataset_info in datasets:
        result = handle_edge_cases(dataset_info)
        processed_results.append(result)
        
        if not result['is_valid']:
            logger.warning(f"Skipping dataset {result['dataset_id']} due to edge case failures.")
            
    return processed_results


def main():
    """
    Main entry point for testing the edge case handler.
    This function is intended for manual testing or integration into the main pipeline.
    """
    logger.info("Starting edge case handler demonstration.")
    
    # Example usage with a mock dataset structure
    # In production, this would be called by the main simulation loop
    sample_data = {
        'dataset_id': 'demo_dataset',
        'df': pd.DataFrame({
            'col1': [1.0, 2.0, 3.0, 4.0, 5.0] * 20, # 100 rows
            'col2': ['A', 'B', 'C'] * 33 + ['A'],   # Categorical
            'col3': [10, 20, 30] * 33 + [10]        # Numeric
        })
    }
    
    result = handle_edge_cases(sample_data)
    print(f"Validation Result: {result}")
    
    logger.info("Edge case handler demonstration complete.")


if __name__ == "__main__":
    main()
