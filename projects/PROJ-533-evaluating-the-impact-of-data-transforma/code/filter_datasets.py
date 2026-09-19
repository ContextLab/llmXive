import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from code.utils.logging_config import setup_pipeline_logger, log_imputation_rate, log_exclusion
from code.utils.schema_definitions import get_imputation_log_headers, get_exclusions_headers, get_filter_results_headers
from code.utils.statistical_tests import shapiro_test

# Initialize logger
logger = setup_pipeline_logger()

def load_dataset_from_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load a dataset from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame or None if loading fails
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded dataset from {file_path}", 
                   extra={"dataset_path": file_path, "shape": list(df.shape)})
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {str(e)}",
                    extra={"dataset_path": file_path, "error": str(e)})
        return None

def calculate_missing_ratio(df: pd.DataFrame, variable: str) -> float:
    """
    Calculate the ratio of missing values for a specific variable.
    
    Args:
        df: DataFrame
        variable: Column name
        
    Returns:
        Ratio of missing values (0.0 to 1.0)
    """
    if variable not in df.columns:
        return 0.0
    
    total_count = len(df)
    if total_count == 0:
        return 0.0
    
    missing_count = df[variable].isna().sum()
    return float(missing_count) / total_count

def impute_missing_values(df: pd.DataFrame, method: str = 'mean') -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Impute missing values in numeric columns using specified method.
    
    Args:
        df: Input DataFrame
        method: Imputation method ('mean' or 'median')
        
    Returns:
        Tuple of (imputed DataFrame, list of imputation logs)
    """
    imputation_logs = []
    df_imputed = df.copy()
    
    numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        missing_ratio = calculate_missing_ratio(df_imputed, col)
        
        if missing_ratio > 0:
            if method == 'mean':
                fill_value = df_imputed[col].mean()
            elif method == 'median':
                fill_value = df_imputed[col].median()
            else:
                logger.warning(f"Unknown imputation method: {method}, skipping {col}")
                continue
            
            if pd.isna(fill_value):
                logger.warning(f"Cannot compute {method} for {col}, skipping imputation")
                continue
            
            # Apply imputation
            df_imputed[col] = df_imputed[col].fillna(fill_value)
            
            # Log the imputation
            log_entry = {
                'variable': col,
                'imputation_method': method,
                'rate': missing_ratio,
                'fill_value': fill_value
            }
            imputation_logs.append(log_entry)
            log_imputation_rate(col, method, missing_ratio)
            logger.info(f"Imputed {col} using {method} (rate={missing_ratio:.4f}, value={fill_value:.4f})")
    
    return df_imputed, imputation_logs

def filter_by_missing_data(df: pd.DataFrame, threshold: float = 0.10) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Filter out variables with missing data ratio above threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed missing ratio (default 0.10 = 10%)
        
    Returns:
        Tuple of (filtered DataFrame, list of exclusion logs)
    """
    exclusion_logs = []
    cols_to_drop = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        missing_ratio = calculate_missing_ratio(df, col)
        
        if missing_ratio > threshold:
            cols_to_drop.append(col)
            exclusion_entry = {
                'variable': col,
                'reason': 'high_missing_ratio',
                'details': f'Missing ratio {missing_ratio:.4f} exceeds threshold {threshold}',
                'missing_ratio': missing_ratio
            }
            exclusion_logs.append(exclusion_entry)
            log_exclusion(col, 'high_missing_ratio', f'Missing ratio {missing_ratio:.4f} exceeds threshold {threshold}')
            logger.warning(f"Excluding {col} due to high missing ratio: {missing_ratio:.4f}")
    
    if cols_to_drop:
        df_filtered = df.drop(columns=cols_to_drop)
        logger.info(f"Dropped {len(cols_to_drop)} columns due to high missing ratio")
    else:
        df_filtered = df.copy()
    
    return df_filtered, exclusion_logs

def process_dataset_for_filtering(dataset_id: str, file_path: str, 
                                 imputation_method: str = 'mean',
                                 missing_threshold: float = 0.10) -> Dict[str, Any]:
    """
    Process a single dataset for filtering: load, impute, filter, and log.
    
    Args:
        dataset_id: Unique identifier for the dataset
        file_path: Path to the dataset CSV file
        imputation_method: Method for imputation ('mean' or 'median')
        missing_threshold: Threshold for excluding variables with high missing data
        
    Returns:
        Dictionary containing processing results
    """
    result = {
        'dataset_id': dataset_id,
        'success': False,
        'original_shape': None,
        'final_shape': None,
        'imputed_variables': [],
        'excluded_variables': [],
        'error': None
    }
    
    # Load dataset
    df = load_dataset_from_file(file_path)
    if df is None:
        result['error'] = 'Failed to load dataset'
        return result
    
    result['original_shape'] = list(df.shape)
    logger.info(f"Processing dataset {dataset_id}: original shape {result['original_shape']}")
    
    # Impute missing values
    df_imputed, imputation_logs = impute_missing_values(df, method=imputation_method)
    result['imputed_variables'] = [log['variable'] for log in imputation_logs]
    
    # Filter by missing data
    df_filtered, exclusion_logs = filter_by_missing_data(df_imputed, threshold=missing_threshold)
    result['excluded_variables'] = [log['variable'] for log in exclusion_logs]
    
    result['final_shape'] = list(df_filtered.shape)
    result['success'] = True
    
    logger.info(f"Dataset {dataset_id} processed successfully: final shape {result['final_shape']}")
    return result

def run_filter_pipeline(data_dir: str, imputation_method: str = 'mean',
                       missing_threshold: float = 0.10) -> bool:
    """
    Run the full filtering pipeline on all datasets in the data directory.
    
    Args:
        data_dir: Directory containing downloaded datasets
        imputation_method: Method for imputation ('mean' or 'median')
        missing_threshold: Threshold for excluding variables with high missing data
        
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return False
    
    # Initialize output files
    imputation_log_path = data_path.parent / 'imputation_log.csv'
    exclusions_path = data_path.parent / 'exclusions.csv'
    
    # Write headers
    with open(imputation_log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=get_imputation_log_headers())
        writer.writeheader()
    
    with open(exclusions_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=get_exclusions_headers())
        writer.writeheader()
    
    logger.info(f"Initialized imputation log at {imputation_log_path}")
    logger.info(f"Initialized exclusions log at {exclusions_path}")
    
    # Process each dataset
    dataset_files = list(data_path.glob('*.csv'))
    if not dataset_files:
        logger.warning(f"No CSV files found in {data_dir}")
        return True
    
    success_count = 0
    total_count = len(dataset_files)
    
    for file_path in dataset_files:
        # Extract dataset_id from filename (assuming format: dataset_id.csv or dataset_id_*.csv)
        dataset_id = file_path.stem
        
        try:
            result = process_dataset_for_filtering(
                dataset_id=str(dataset_id),
                file_path=str(file_path),
                imputation_method=imputation_method,
                missing_threshold=missing_threshold
            )
            
            if result['success']:
                success_count += 1
                
                # Append to imputation log
                for log_entry in result.get('imputed_logs', []):
                    with open(imputation_log_path, 'a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=get_imputation_log_headers())
                        writer.writerow({
                            'dataset_id': dataset_id,
                            'variable': log_entry['variable'],
                            'imputation_method': log_entry['imputation_method'],
                            'rate': log_entry['rate']
                        })
                
                # Append to exclusions log
                for log_entry in result.get('exclusion_logs', []):
                    with open(exclusions_path, 'a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=get_exclusions_headers())
                        writer.writerow({
                            'dataset_id': dataset_id,
                            'variable': log_entry['variable'],
                            'reason': log_entry['reason'],
                            'details': log_entry['details']
                        })
            else:
                logger.error(f"Failed to process dataset {dataset_id}: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {str(e)}", exc_info=True)
    
    logger.info(f"Filter pipeline completed: {success_count}/{total_count} datasets processed successfully")
    return success_count > 0

def main():
    """Main entry point for the filter_datasets script."""
    logger.info("Starting filter_datasets pipeline")
    
    # Default paths
    data_dir = 'data/datasets'
    imputation_method = 'mean'
    missing_threshold = 0.10
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        imputation_method = sys.argv[2]
    if len(sys.argv) > 3:
        missing_threshold = float(sys.argv[3])
    
    success = run_filter_pipeline(
        data_dir=data_dir,
        imputation_method=imputation_method,
        missing_threshold=missing_threshold
    )
    
    if success:
        logger.info("Filter pipeline completed successfully")
        sys.exit(0)
    else:
        logger.error("Filter pipeline failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
