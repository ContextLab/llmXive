import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import logging configuration
from code.utils.logging_config import setup_pipeline_logger
from code.utils.streaming_utils import (
    stream_csv_rows,
    OnlineStatsCalculator,
    compute_online_stats,
    stream_numeric_data,
    get_file_row_count
)
from code.utils.data_model import Dataset
from code.utils.schema_definitions import (
    get_imputation_log_headers,
    get_exclusions_headers,
    get_filter_results_headers
)

# Setup logger
logger = setup_pipeline_logger("filter_datasets")

def load_dataset_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load a dataset from a CSV file.
    Returns a dictionary with 'data' (list of dicts) and 'metadata' (dict).
    For large files, this function should be used with streaming logic in downstream operations.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    data = []
    headers = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            data.append(row)
    
    return {
        'data': data,
        'metadata': {
            'source_file': file_path,
            'headers': headers,
            'row_count': len(data)
        }
    }

def calculate_missing_ratio(dataset: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate the ratio of missing values for each column.
    Uses streaming logic for large datasets to avoid loading everything into memory.
    """
    file_path = dataset['metadata']['source_file']
    headers = dataset['metadata']['headers']
    
    # Initialize counters for each column
    missing_counts = {col: 0 for col in headers}
    total_rows = 0
    
    # Stream through the file to count missing values
    for row in stream_csv_rows(file_path):
        total_rows += 1
        for col in headers:
            val = row.get(col, '').strip()
            if val == '' or val.lower() in ('nan', 'na', 'null', 'none'):
                missing_counts[col] += 1
    
    if total_rows == 0:
        return {col: 0.0 for col in headers}
    
    return {col: count / total_rows for col, count in missing_counts.items()}

def impute_missing_values(dataset: Dict[str, Any], method: str = 'mean') -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Impute missing values using the specified method (mean or median).
    Returns the imputed dataset and a log of imputation rates.
    Uses streaming logic for efficiency on large datasets.
    """
    file_path = dataset['metadata']['source_file']
    headers = dataset['metadata']['headers']
    
    # First pass: compute imputation values (mean/median) for each column
    col_values = {col: [] for col in headers}
    
    # Stream to collect numeric values
    for row in stream_csv_rows(file_path):
        for col in headers:
            val = row.get(col, '').strip()
            if val not in ('', 'nan', 'na', 'null', 'none'):
                try:
                    col_values[col].append(float(val))
                except ValueError:
                    pass  # Skip non-numeric values
    
    # Compute imputation values
    impute_values = {}
    for col, values in col_values.items():
        if not values:
            impute_values[col] = 0.0
            continue
        if method == 'mean':
            impute_values[col] = sum(values) / len(values)
        elif method == 'median':
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            if n % 2 == 0:
                impute_values[col] = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
            else:
                impute_values[col] = sorted_vals[n//2]
        else:
            raise ValueError(f"Unknown imputation method: {method}")
    
    # Second pass: write imputed data to a new file
    imputed_file_path = file_path.replace('.csv', '_imputed.csv')
    imputation_log = {}
    
    with open(file_path, 'r', newline='', encoding='utf-8') as infile, \
         open(imputed_file_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        
        total_rows = 0
        for row in reader:
            total_rows += 1
            imputed_row = row.copy()
            for col in headers:
                val = row.get(col, '').strip()
                if val == '' or val.lower() in ('nan', 'na', 'null', 'none'):
                    imputed_row[col] = str(impute_values[col])
                    if col not in imputation_log:
                        imputation_log[col] = 0
                    imputation_log[col] += 1
            
            writer.writerow(imputed_row)
    
    # Calculate imputation rates
    imputation_rates = {col: count / total_rows for col, count in imputation_log.items()}
    
    # Update dataset metadata
    dataset['metadata']['imputed_file'] = imputed_file_path
    dataset['metadata']['imputation_method'] = method
    
    return dataset, imputation_rates

def filter_by_missing_data(dataset: Dict[str, Any], threshold: float = 0.10) -> Tuple[bool, Dict[str, float]]:
    """
    Check if a dataset should be excluded based on missing data threshold.
    Returns (should_exclude, missing_ratios).
    """
    missing_ratios = calculate_missing_ratio(dataset)
    max_ratio = max(missing_ratios.values()) if missing_ratios else 0.0
    should_exclude = max_ratio > threshold
    return should_exclude, missing_ratios

def process_dataset_for_filtering(dataset: Dict[str, Any], 
                                  imputation_method: str = 'mean',
                                  missing_threshold: float = 0.10) -> Tuple[bool, Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Process a single dataset for filtering:
    1. Calculate missing ratios
    2. Impute if necessary
    3. Check if it passes the missing data threshold
    
    Returns (passed_filter, processed_dataset, imputation_log_entry)
    """
    dataset_id = dataset['metadata'].get('dataset_id', 'unknown')
    logger.info(f"Processing dataset {dataset_id}")
    
    # Calculate missing ratios
    should_exclude, missing_ratios = filter_by_missing_data(dataset, missing_threshold)
    
    if should_exclude:
        logger.warning(f"Dataset {dataset_id} excluded: missing rate {max(missing_ratios.values()):.2%} > {missing_threshold:.0%}")
        return False, dataset, None
    
    # Impute missing values
    dataset, imputation_rates = impute_missing_values(dataset, method=imputation_method)
    
    logger.info(f"Dataset {dataset_id} passed filtering. Imputation rates: {imputation_rates}")
    
    # Create imputation log entry
    imputation_log_entry = {
        'dataset_id': dataset_id,
        'variable': 'all',
        'imputation_method': imputation_method,
        'rate': str(max(imputation_rates.values()))
    }
    
    return True, dataset, imputation_log_entry

def run_filter_pipeline(datasets_dir: str, 
                        output_csv: str,
                        imputation_log_csv: str,
                        exclusions_csv: str,
                        filter_results_csv: str,
                        imputation_method: str = 'mean',
                        missing_threshold: float = 0.10) -> List[Dict[str, Any]]:
    """
    Run the full filtering pipeline on all datasets in the directory.
    Uses streaming logic for processing large files.
    """
    datasets_dir = Path(datasets_dir)
    output_csv = Path(output_csv)
    imputation_log_csv = Path(imputation_log_csv)
    exclusions_csv = Path(exclusions_csv)
    filter_results_csv = Path(filter_results_csv)
    
    # Ensure output directories exist
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    imputation_log_csv.parent.mkdir(parents=True, exist_ok=True)
    exclusions_csv.parent.mkdir(parents=True, exist_ok=True)
    filter_results_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize output files
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'source_file', 'passed_filter', 'missing_rate'])
        writer.writeheader()
    
    with open(imputation_log_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=get_imputation_log_headers())
        writer.writeheader()
    
    with open(exclusions_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=get_exclusions_headers())
        writer.writeheader()
    
    with open(filter_results_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=get_filter_results_headers())
        writer.writeheader()
    
    processed_datasets = []
    
    # Process each CSV file in the directory
    for csv_file in datasets_dir.glob('*.csv'):
        if csv_file.name.endswith('_imputed.csv') or csv_file.name == 'datasets.csv':
            continue
          
        try:
            dataset = load_dataset_from_file(str(csv_file))
            dataset_id = csv_file.stem
          
            # Process dataset
            passed, processed_dataset, imputation_entry = process_dataset_for_filtering(
                dataset, imputation_method, missing_threshold
            )
          
            # Calculate missing rate for logging
            missing_ratios = calculate_missing_ratio(processed_dataset)
            max_missing_rate = max(missing_ratios.values()) if missing_ratios else 0.0
          
            # Write to datasets.csv
            with open(output_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['dataset_id', 'source_file', 'passed_filter', 'missing_rate'])
                writer.writerow({
                    'dataset_id': dataset_id,
                    'source_file': str(csv_file),
                    'passed_filter': 'True' if passed else 'False',
                    'missing_rate': f"{max_missing_rate:.4f}"
                })
          
            # Write imputation log
            if imputation_entry:
                with open(imputation_log_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=get_imputation_log_headers())
                    writer.writerow(imputation_entry)
            
            # Write exclusion log if failed
            if not passed:
                exclusion_entry = {
                    'dataset_id': dataset_id,
                    'reason': 'missing_rate',
                    'details': f"missing_rate: {max_missing_rate:.1%}"
                }
                with open(exclusions_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=get_exclusions_headers())
                    writer.writerow(exclusion_entry)
            
            # Write filter results
            filter_result = {
                'dataset_id': dataset_id,
                'shapiro_p': 'N/A',  # Will be updated by T016
                'sample_size': dataset['metadata']['row_count'],
                'included': 'True' if passed else 'False'
            }
            with open(filter_results_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=get_filter_results_headers())
                writer.writerow(filter_result)
          
            if passed:
                processed_datasets.append(processed_dataset)
          
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            continue
    
    logger.info(f"Filter pipeline complete. Processed {len(processed_datasets)} datasets.")
    return processed_datasets

def main():
    """Main entry point for the filter_datasets script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter datasets based on missing data and normality')
    parser.add_argument('--datasets-dir', type=str, default='data/raw', help='Directory containing raw datasets')
    parser.add_argument('--output-csv', type=str, default='data/datasets.csv', help='Output CSV for dataset metadata')
    parser.add_argument('--imputation-log', type=str, default='data/imputation_log.csv', help='Output CSV for imputation log')
    parser.add_argument('--exclusions', type=str, default='data/exclusions.csv', help='Output CSV for excluded datasets')
    parser.add_argument('--filter-results', type=str, default='data/filter_results.csv', help='Output CSV for filter results')
    parser.add_argument('--imputation-method', type=str, default='mean', choices=['mean', 'median'], help='Imputation method')
    parser.add_argument('--missing-threshold', type=float, default=0.10, help='Maximum allowed missing data ratio')
    
    args = parser.parse_args()
    
    logger.info("Starting filter_datasets pipeline")
    
    try:
        processed = run_filter_pipeline(
            datasets_dir=args.datasets_dir,
            output_csv=args.output_csv,
            imputation_log_csv=args.imputation_log,
            exclusions_csv=args.exclusions,
            filter_results_csv=args.filter_results,
            imputation_method=args.imputation_method,
            missing_threshold=args.missing_threshold
        )
        logger.info(f"Pipeline completed successfully. Processed {len(processed)} datasets.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()