import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path if running as script
if 'code' not in sys.path and os.path.exists('code'):
    sys.path.insert(0, os.path.join(os.getcwd(), 'code'))

from utils.config import get_config
from utils.hashing import compute_file_hash


def load_merged_dataset(config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Load the merged dataset from the processed directory.
    
    Args:
        config: Optional configuration dictionary. If None, loads from defaults.
        
    Returns:
        pd.DataFrame: The loaded merged dataset.
        
    Raises:
        FileNotFoundError: If the merged dataset file does not exist.
    """
    if config is None:
        config = get_config()
        
    data_path = Path(config['paths']['data_processed'])
    merged_file = data_path / 'merged_dataset.csv'
    
    if not merged_file.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_file}. "
                              "Please run T016 (aggregation) first to generate this file.")
                             
    return pd.read_csv(merged_file)


def validate_numeric_columns(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate that all numeric columns contain only numeric values and no non-numeric entries.
    
    Args:
        df: The dataframe to validate.
        config: Optional configuration dictionary.
        
    Returns:
        Dict containing validation results:
            - 'is_valid': bool, True if all checks pass
            - 'errors': List[str], list of error messages
            - 'column_stats': Dict, statistics about numeric columns
            - 'non_numeric_entries': List[Dict], details of any non-numeric entries found
    """
    errors = []
    non_numeric_entries = []
    column_stats = {}
    
    if config is None:
        config = get_config()
        
    # Identify numeric columns (excluding sample ID and other non-numeric identifiers)
    # We assume the merged dataset has a 'sample_id' column and all others should be numeric
    # or categorical strings that are expected (like condition names)
    # For this validation, we focus on columns that are expected to be numeric for modeling
    
    # Heuristic: Columns that are not 'sample_id', 'condition', 'treatment' are likely numeric features
    exclude_cols = {'sample_id', 'condition', 'treatment', 'species', 'genotype'}
    numeric_candidates = [col for col in df.columns if col not in exclude_cols]
    
    for col in numeric_candidates:
        if col not in df.columns:
            continue
            
        col_data = df[col]
        stats = {
            'total_rows': len(col_data),
            'non_null': col_data.count(),
            'null_count': col_data.isna().sum(),
            'is_numeric': True,
            'dtype': str(col_data.dtype),
            'non_numeric_count': 0,
            'non_numeric_values': []
        }
        
        # Check if the column is entirely numeric
        try:
            # Attempt to convert to numeric, coercing errors to NaN
            converted = pd.to_numeric(col_data, errors='coerce')
            non_numeric_mask = converted.isna() & col_data.notna()
            
            if non_numeric_mask.any():
                stats['is_numeric'] = False
                stats['non_numeric_count'] = non_numeric_mask.sum()
                
                # Capture details of non-numeric entries
                non_numeric_indices = df[non_numeric_mask].index.tolist()
                non_numeric_values = col_data[non_numeric_mask].unique().tolist()
                
                for idx, val in zip(non_numeric_indices, non_numeric_values):
                    non_numeric_entries.append({
                        'column': col,
                        'row_index': idx,
                        'value': str(val)
                    })
                
                errors.append(f"Column '{col}' contains {stats['non_numeric_count']} non-numeric entries.")
            
            # Calculate numeric statistics only on valid numeric data
            valid_numeric = converted.dropna()
            if len(valid_numeric) > 0:
                stats['mean'] = float(valid_numeric.mean())
                stats['std'] = float(valid_numeric.std())
                stats['min'] = float(valid_numeric.min())
                stats['max'] = float(valid_numeric.max())
                
        except Exception as e:
            stats['is_numeric'] = False
            errors.append(f"Error processing column '{col}': {str(e)}")
        
        column_stats[col] = stats
    
    is_valid = len(errors) == 0
    
    return {
        'is_valid': is_valid,
        'errors': errors,
        'column_stats': column_stats,
        'non_numeric_entries': non_numeric_entries
    }


def generate_validation_report(df: pd.DataFrame, validation_results: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.
    
    Args:
        df: The dataframe that was validated.
        validation_results: Results from validate_numeric_columns.
        config: Optional configuration dictionary.
        
    Returns:
        Dict containing the full validation report.
    """
    if config is None:
        config = get_config()
        
    report = {
        'validation_timestamp': pd.Timestamp.now().isoformat(),
        'dataset_info': {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'file_hash': compute_file_hash(Path(config['paths']['data_processed']) / 'merged_dataset.csv')
        },
        'validation_results': validation_results,
        'summary': {
            'is_valid': validation_results['is_valid'],
            'total_errors': len(validation_results['errors']),
            'non_numeric_entries_found': len(validation_results['non_numeric_entries']),
            'numeric_columns_count': sum(1 for col, stats in validation_results['column_stats'].items() 
                                        if stats.get('is_numeric', False)),
            'total_numeric_columns': len(validation_results['column_stats'])
        },
        'recommendations': []
    }
    
    # Add recommendations based on findings
    if not validation_results['is_valid']:
        report['recommendations'].append(
            "Fix non-numeric entries in numeric columns before model training. "
            "Consider imputation or exclusion of affected samples."
        )
    
    if validation_results['summary']['non_numeric_entries_found'] > 0:
        report['recommendations'].append(
            f"Found {validation_results['summary']['non_numeric_entries_found']} non-numeric entries. "
            "Review data ingestion pipeline (T014, T015) for data type issues."
        )
        
    # Check for high null counts
    for col, stats in validation_results['column_stats'].items():
        if stats['null_count'] > len(df) * 0.1:  # More than 10% nulls
            report['recommendations'].append(
                f"Column '{col}' has {stats['null_count']} null values ({stats['null_count']/len(df)*100:.1f}%). "
                "Consider imputation strategy from T009."
            )
    
    return report


def main():
    """
    Main entry point for the validation script.
    
    This script:
    1. Loads the merged dataset from data/processed/merged_dataset.csv
    2. Validates that all numeric columns contain only numeric values
    3. Generates a validation report at data/results/data_validation_report.json
    4. Exits with code 1 if validation fails, 0 if successful
    """
    print("Starting data validation for merged dataset...")
    
    try:
        # Load configuration
        config = get_config()
        
        # Ensure output directories exist
        data_results_dir = Path(config['paths']['data_results'])
        data_results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the merged dataset
        print(f"Loading merged dataset from {config['paths']['data_processed']}/merged_dataset.csv")
        df = load_merged_dataset(config)
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
        
        # Validate numeric columns
        print("Validating numeric columns...")
        validation_results = validate_numeric_columns(df, config)
        
        # Generate report
        print("Generating validation report...")
        report = generate_validation_report(df, validation_results, config)
        
        # Save report
        report_path = data_results_dir / 'data_validation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Validation report saved to {report_path}")
        print(f"Validation status: {'PASSED' if report['summary']['is_valid'] else 'FAILED'}")
        
        if report['summary']['total_errors'] > 0:
            print(f"Errors found: {report['summary']['total_errors']}")
            for error in report['validation_results']['errors']:
                print(f"  - {error}")
        
        if report['summary']['non_numeric_entries_found'] > 0:
            print(f"Non-numeric entries found: {report['summary']['non_numeric_entries_found']}")
            
        if not report['summary']['is_valid']:
            print("\nValidation FAILED. Please review the report and fix data issues.")
            sys.exit(1)
        else:
            print("\nValidation PASSED. Dataset is ready for model training.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure T016 (aggregation) has been completed to generate merged_dataset.csv")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()