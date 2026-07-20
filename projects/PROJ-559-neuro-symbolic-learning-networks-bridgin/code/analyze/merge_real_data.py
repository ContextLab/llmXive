"""
merge_real_data.py

Implements logic to merge simulated and real student data, validate the
data_source effect, and save the merged dataset and validation report.

Dependencies:
- T026: Mixed effects model implementation (data availability)
- T034: Real student data ingestion (data availability)

Output:
- data/derived/merged_student_data.csv
- data/derived/merge_validation_report.json
"""
import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DERIVED_DIR = os.path.join(DATA_DIR, 'derived')
SIMULATED_LOGS_PATH = os.path.join(DERIVED_DIR, 'simulation_logs.csv')
REAL_DATA_PATH = os.path.join(DATA_DIR, 'real', 'student_data.csv')
MERGED_OUTPUT_PATH = os.path.join(DERIVED_DIR, 'merged_student_data.csv')
VALIDATION_REPORT_PATH = os.path.join(DERIVED_DIR, 'merge_validation_report.json')

# Minimum records required for analysis
MIN_TOTAL_RECORDS = 200
MIN_REAL_RECORDS = 50  # Minimum real data records to attempt merge

def load_real_student_data(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load real student data from CSV.

    Args:
        path: Optional path to real data CSV. Defaults to REAL_DATA_PATH.

    Returns:
        DataFrame with real student records.

    Raises:
        FileNotFoundError: If the real data file does not exist.
        ValueError: If required columns are missing.
    """
    file_path = path or REAL_DATA_PATH
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Real student data file not found at: {file_path}")

    logger.info(f"Loading real student data from: {file_path}")
    df = pd.read_csv(file_path)

    required_columns = ['problem_id', 'condition', 'correct', 'rt_seconds', 'comprehension_rating']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Real data missing required columns: {missing_cols}")

    # Add data_source column
    df['data_source'] = 'real'
    logger.info(f"Loaded {len(df)} real student records")
    return df

def load_simulated_data(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load simulated student data from CSV.

    Args:
        path: Optional path to simulated logs CSV. Defaults to SIMULATED_LOGS_PATH.

    Returns:
        DataFrame with simulated student records.

    Raises:
        FileNotFoundError: If the simulated data file does not exist.
        ValueError: If required columns are missing.
    """
    file_path = path or SIMULATED_LOGS_PATH
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Simulated data file not found at: {file_path}")

    logger.info(f"Loading simulated student data from: {file_path}")
    df = pd.read_csv(file_path)

    required_columns = ['student_id', 'problem_id', 'condition', 'correct', 'rt_seconds', 'comprehension_rating']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Simulated data missing required columns: {missing_cols}")

    # Add data_source column
    df['data_source'] = 'simulated'
    # Ensure student_id is present (might be named differently in some versions)
    if 'student_id' not in df.columns:
        df['student_id'] = [f"sim_{i}" for i in range(len(df))]

    logger.info(f"Loaded {len(df)} simulated student records")
    return df

def validate_data_source_effects(merged_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate that the merged dataset has appropriate data_source effects.

    Args:
        merged_df: The merged DataFrame.

    Returns:
        Dictionary with validation results.
    """
    validation_result = {
        'total_records': len(merged_df),
        'real_records': len(merged_df[merged_df['data_source'] == 'real']),
        'simulated_records': len(merged_df[merged_df['data_source'] == 'simulated']),
        'meets_minimum_threshold': len(merged_df) >= MIN_TOTAL_RECORDS,
        'data_source_balance': {},
        'column_completeness': {},
        'issues': []
    }

    # Check minimum threshold
    if validation_result['total_records'] < MIN_TOTAL_RECORDS:
        validation_result['issues'].append(
            f"Total records ({validation_result['total_records']}) below minimum threshold ({MIN_TOTAL_RECORDS})"
        )

    # Check data source balance
    source_counts = merged_df['data_source'].value_counts()
    validation_result['data_source_balance'] = source_counts.to_dict()

    # Check for missing values in key columns
    key_columns = ['correct', 'rt_seconds', 'comprehension_rating', 'data_source']
    for col in key_columns:
        missing = merged_df[col].isna().sum()
        validation_result['column_completeness'][col] = {
            'missing_count': int(missing),
            'missing_percentage': float(missing / len(merged_df) * 100) if len(merged_df) > 0 else 0.0
        }
        if missing > 0:
            validation_result['issues'].append(
                f"Column '{col}' has {missing} missing values ({validation_result['column_completeness'][col]['missing_percentage']:.2f}%)"
            )

    # Check condition distribution per data source
    condition_counts = merged_df.groupby(['data_source', 'condition']).size().unstack(fill_value=0)
    validation_result['condition_distribution'] = condition_counts.to_dict()

    # Validate that we have both data sources
    if 'real' not in merged_df['data_source'].values:
        validation_result['issues'].append("No real data found in merged dataset")
    if 'simulated' not in merged_df['data_source'].values:
        validation_result['issues'].append("No simulated data found in merged dataset")

    return validation_result

def merge_datasets(real_df: pd.DataFrame, simulated_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge real and simulated datasets.

    Args:
        real_df: DataFrame with real student data.
        simulated_df: DataFrame with simulated student data.

    Returns:
        Merged DataFrame.
    """
    logger.info(f"Merging {len(real_df)} real records with {len(simulated_df)} simulated records")

    # Select common columns for merging
    common_columns = ['problem_id', 'condition', 'correct', 'rt_seconds', 'comprehension_rating', 'data_source']

    # Ensure both DataFrames have the same columns
    real_subset = real_df[common_columns].copy()
    simulated_subset = simulated_df[common_columns].copy()

    # Concatenate
    merged_df = pd.concat([real_subset, simulated_subset], ignore_index=True)

    logger.info(f"Merged dataset contains {len(merged_df)} total records")
    return merged_df

def save_merged_data(df: pd.DataFrame, path: Optional[str] = None) -> str:
    """
    Save merged DataFrame to CSV.

    Args:
        df: DataFrame to save.
        path: Optional output path. Defaults to MERGED_OUTPUT_PATH.

    Returns:
        Path to saved file.
    """
    output_path = path or MERGED_OUTPUT_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged data to: {output_path}")
    return output_path

def save_validation_report(report: Dict[str, Any], path: Optional[str] = None) -> str:
    """
    Save validation report to JSON.

    Args:
        report: Validation report dictionary.
        path: Optional output path. Defaults to VALIDATION_REPORT_PATH.

    Returns:
        Path to saved file.
    """
    output_path = path or VALIDATION_REPORT_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Saved validation report to: {output_path}")
    return output_path

def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for merging real and simulated data.

    Args:
        args: Command line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description='Merge simulated and real student data and validate data_source effects.'
    )
    parser.add_argument(
        '--real-data',
        type=str,
        default=None,
        help='Path to real student data CSV (default: data/real/student_data.csv)'
    )
    parser.add_argument(
        '--simulated-data',
        type=str,
        default=None,
        help='Path to simulated data CSV (default: data/derived/simulation_logs.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path for merged output CSV (default: data/derived/merged_student_data.csv)'
    )
    parser.add_argument(
        '--report',
        type=str,
        default=None,
        help='Path for validation report JSON (default: data/derived/merge_validation_report.json)'
    )
    parser.add_argument(
        '--fail-on-low-count',
        action='store_true',
        help='Fail if total records below minimum threshold'
    )

    parsed_args = parser.parse_args(args)

    try:
        # Load real data
        real_df = load_real_student_data(parsed_args.real_data)

        # Load simulated data
        simulated_df = load_simulated_data(parsed_args.simulated_data)

        # Merge datasets
        merged_df = merge_datasets(real_df, simulated_df)

        # Validate data source effects
        validation_report = validate_data_source_effects(merged_df)

        # Save outputs
        save_merged_data(merged_df, parsed_args.output)
        save_validation_report(validation_report, parsed_args.report)

        # Check for issues
        if validation_report['issues']:
            logger.warning("Validation issues found:")
            for issue in validation_report['issues']:
                logger.warning(f"  - {issue}")

            if parsed_args.fail_on_low_count and not validation_report['meets_minimum_threshold']:
                logger.error(f"Total records ({validation_report['total_records']}) below minimum threshold ({MIN_TOTAL_RECORDS})")
                return 1

        logger.info("Merge and validation completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
