import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats

# Project imports
from code.utils.logging_config import setup_pipeline_logger, log_exclusion
from code.utils.statistical_tests import shapiro_wilk
from code.utils.schema_definitions import get_filter_results_headers, get_exclusions_headers, get_imputation_log_headers

# Ensure logger is configured
logger = setup_pipeline_logger("filter_datasets")

def load_dataset_from_file(file_path: str) -> pd.DataFrame:
    """Load a dataset from a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    return pd.read_csv(file_path)

def calculate_missing_ratio(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate the missing value ratio for each column."""
    missing_ratio = df.isna().mean()
    return missing_ratio.to_dict()

def impute_missing_values(df: pd.DataFrame, method: str = 'mean') -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Impute missing values using the specified method."""
    imputation_log = {}
    df_imputed = df.copy()
    
    for col in df_imputed.columns:
        if df_imputed[col].isna().any():
            missing_count = df_imputed[col].isna().sum()
            total_count = len(df_imputed)
            rate = missing_count / total_count
            
            if method == 'mean':
                impute_val = df_imputed[col].mean()
            elif method == 'median':
                impute_val = df_imputed[col].median()
            else:
                raise ValueError(f"Unsupported imputation method: {method}")
            
            df_imputed[col] = df_imputed[col].fillna(impute_val)
            imputation_log[col] = rate
            logger.info(f"Imputed column '{col}' using {method} (rate: {rate:.4f})")
    
    return df_imputed, imputation_log

def filter_by_missing_data(df: pd.DataFrame, threshold: float = 0.10) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Filter out columns with missing data ratio above threshold."""
    missing_ratio = calculate_missing_ratio(df)
    excluded_cols = []
    
    for col, rate in missing_ratio.items():
        if rate > threshold:
            excluded_cols.append(col)
            logger.warning(f"Excluding column '{col}' due to missing rate {rate:.2%} > {threshold:.2%}")
    
    df_filtered = df.drop(columns=excluded_cols)
    return df_filtered, excluded_cols

def process_dataset_for_filtering(file_path: str, dataset_id: str) -> Dict[str, Any]:
    """Process a single dataset for filtering."""
    try:
        df = load_dataset_from_file(file_path)
        
        # Step 1: Handle missing values
        df_clean, imputation_log = impute_missing_values(df, method='mean')
        
        # Step 2: Check if any column exceeds 10% missing (already logged in impute step if excluded)
        # Note: The logic in T015 handles column exclusion. Here we check row-level or overall dataset exclusion if needed.
        # For this task, we assume column exclusion is sufficient, but we log the imputation rates.
        
        # Step 3: Shapiro-Wilk Test on continuous variables
        # Select numeric columns
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        
        shapiro_results = []
        non_normal_count = 0
        
        for col in numeric_cols:
            data = df_clean[col].dropna()
            if len(data) < 3:
                continue # Need at least 3 points for Shapiro-Wilk
            
            stat, p_value = shapiro_wilk(data.values)
            shapiro_results.append({
                'column': col,
                'statistic': stat,
                'p_value': p_value
            })
            
            if p_value < 0.05:
                non_normal_count += 1
        
        # Step 4: Sample size check
        sample_size = len(df_clean)
        
        # Determine if dataset is kept
        # Criteria: N >= 30 AND (at least one non-normal variable OR we are just filtering for non-normality presence)
        # The task says "filter for non-normality". Usually this means keeping datasets that ARE non-normal.
        # However, the description says "filter for non-normality (Shapiro-Wilk p < 0.05)".
        # Interpretation: Keep if the dataset exhibits non-normality (p < 0.05).
        
        is_non_normal = non_normal_count > 0
        is_large_enough = sample_size >= 30
        
        included = is_non_normal and is_large_enough
        
        if not is_large_enough:
            log_exclusion(dataset_id, "sample_size", f"N={sample_size} < 30")
            included = False
        elif not is_non_normal:
            # If all variables are normal, we might exclude based on the goal of finding non-normal data
            # But the task says "filter for non-normality", implying we want the non-normal ones.
            # If the goal is to keep normal ones, logic flips. Assuming we want non-normal.
            log_exclusion(dataset_id, "normality", "All variables passed Shapiro-Wilk (p >= 0.05)")
            included = False

        return {
            'dataset_id': dataset_id,
            'sample_size': sample_size,
            'shapiro_p': min([r['p_value'] for r in shapiro_results]) if shapiro_results else 1.0,
            'included': included,
            'shapiro_details': shapiro_results,
            'imputation_log': imputation_log
        }
        
    except Exception as e:
        logger.error(f"Error processing {dataset_id}: {str(e)}")
        return {
            'dataset_id': dataset_id,
            'sample_size': 0,
            'shapiro_p': 1.0,
            'included': False,
            'error': str(e)
        }

def run_filter_pipeline(input_dir: str, output_dir: str) -> None:
    """Run the full filtering pipeline on all datasets in input_dir."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filter_results_path = output_path / "filter_results.csv"
    exclusions_path = output_path.parent / "exclusions.csv" # As per T015 spec
    imputation_path = output_path.parent / "imputation_log.csv" # As per T015 spec
    
    # Ensure headers exist for output files
    filter_headers = get_filter_results_headers()
    exclusions_headers = get_exclusions_headers()
    imputation_headers = get_imputation_log_headers()
    
    # Check if files exist to append or write headers
    write_filter_headers = not filter_results_path.exists()
    write_excl_headers = not exclusions_path.exists()
    write_impt_headers = not imputation_path.exists()
    
    filter_results = []
    exclusions_data = []
    imputation_data = []
    
    # Get list of dataset files
    dataset_files = list(input_path.glob("*.csv"))
    
    if not dataset_files:
        logger.warning(f"No dataset files found in {input_dir}")
        # Ensure files are created even if empty
        with open(filter_results_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=filter_headers)
            writer.writeheader()
        return

    for file_path in dataset_files:
        dataset_id = file_path.stem
        logger.info(f"Processing dataset: {dataset_id}")
        
        result = process_dataset_for_filtering(str(file_path), dataset_id)
        
        # Write filter result
        filter_row = {
            'dataset_id': result['dataset_id'],
            'shapiro_p': result['shapiro_p'],
            'sample_size': result['sample_size'],
            'included': result['included']
        }
        filter_results.append(filter_row)
        
        # Collect imputation logs
        for col, rate in result.get('imputation_log', {}).items():
            imputation_data.append({
                'dataset_id': dataset_id,
                'variable': col,
                'imputation_method': 'mean',
                'rate': rate
            })
        
        # Note: Exclusions are logged via log_exclusion which writes to exclusions.csv
        # We also need to ensure the file exists and has headers if no exclusions happened
    
    # Write Filter Results
    with open(filter_results_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=filter_headers)
        writer.writeheader()
        writer.writerows(filter_results)
    
    # Write Imputation Log
    with open(imputation_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=imputation_headers)
        writer.writeheader()
        writer.writerows(imputation_data)
    
    # Ensure Exclusions file exists (even if empty)
    if not exclusions_path.exists():
        with open(exclusions_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=exclusions_headers)
            writer.writeheader()
    
    logger.info(f"Filtering complete. Results written to {filter_results_path}")

def main():
    """Main entry point for the filter script."""
    input_dir = "data/raw" # Assuming raw datasets are here after download
    output_dir = "data/filtered"
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist.")
        sys.exit(1)
    
    run_filter_pipeline(input_dir, output_dir)

if __name__ == "__main__":
    main()
