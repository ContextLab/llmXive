"""
Metrics validation module for the llmXive pipeline.

Provides functions to scan parquet files for NaN values and
validate time-bound baseline runs.
"""
import os
import sys
import glob
import logging
import pandas as pd
import json
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validation.log')
    ]
)
logger = logging.getLogger(__name__)

def scan_parquet_for_nans(file_path: str) -> Dict[str, Any]:
    """
    Scan a parquet file for NaN values.
    
    Args:
        file_path: Path to the parquet file.
        
    Returns:
        Dictionary with 'has_nans' boolean and 'nan_count' per column.
    """
    try:
        df = pd.read_parquet(file_path)
        nan_counts = df.isna().sum()
        total_nans = nan_counts.sum()
        
        result = {
            'file': file_path,
            'has_nans': total_nans > 0,
            'nan_count': int(total_nans),
            'column_nans': nan_counts[nan_counts > 0].to_dict()
        }
        
        if result['has_nans']:
            logger.warning(f"NaNs found in {file_path}: {result['column_nans']}")
        else:
            logger.info(f"No NaNs found in {file_path}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error scanning {file_path}: {e}")
        raise

def validate_time_bound_baseline(
    file_path: str,
    min_steps: int = 1000
) -> Dict[str, Any]:
    """
    Validate a time-bound baseline run.
    
    Checks:
    1. The file exists and is readable.
    2. The 'Time-Bound' flag is present and True.
    3. The run contains at least min_steps steps.
    
    Args:
        file_path: Path to the baseline_partial.parquet file.
        min_steps: Minimum number of steps required (default 1000).
        
    Returns:
        Dictionary with validation results.
        
    Raises:
        ValueError: If validation fails.
    """
    if not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        error_msg = f"Failed to read parquet file {file_path}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Check for Time-Bound flag
    has_flag = False
    flag_value = False
    
    # Try common column names for the flag
    flag_columns = ['is_time_bound', 'time_bound', 'Time-Bound', 'flag', 'status']
    for col in flag_columns:
        if col in df.columns:
            # Check if any row has the flag set to True
            if df[col].dtype == 'object':
                # Check for string representation
                has_flag = (df[col] == 'Time-Bound').any() or (df[col] == 'True').any()
            elif df[col].dtype in ['bool', 'int', 'float']:
                has_flag = df[col].any()
            
            if has_flag:
                flag_value = df[col].iloc[0] if len(df) > 0 else False
                logger.info(f"Found flag column '{col}' with value: {flag_value}")
                break
    
    # If no explicit flag column found, check metadata or other indicators
    if not has_flag:
        # Check if there's a 'status' or 'reason' column indicating time-boundedness
        if 'status' in df.columns:
            has_flag = (df['status'] == 'Time-Bound').any()
        elif 'reason' in df.columns:
            has_flag = (df['reason'] == 'Time-Bound').any()
        else:
            # If we can't find a flag, we assume it's not a time-bound run
            # unless the filename suggests it
            if 'partial' in os.path.basename(file_path).lower():
                logger.warning(
                    f"File {file_path} appears to be partial but no explicit "
                    "Time-Bound flag found. Assuming time-bound based on filename."
                )
                has_flag = True
    
    # Check step count
    step_count = len(df)
    step_column = None
    
    # Try to find a step counter column
    step_columns = ['step', 'step_id', 'timestep', 'time_step', 'iteration']
    for col in step_columns:
        if col in df.columns:
            step_column = col
            step_count = df[col].max() + 1 if df[col].dtype in ['int', 'float'] else len(df)
            break
    
    # If no step column, use row count
    if step_column is None:
        step_count = len(df)
    
    meets_min_steps = step_count >= min_steps
    
    result = {
        'file': file_path,
        'exists': True,
        'is_time_bound': has_flag,
        'flag_value': str(flag_value),
        'step_count': step_count,
        'min_steps_required': min_steps,
        'meets_min_steps': meets_min_steps,
        'validation_passed': has_flag and meets_min_steps
    }
    
    # Log results
    if has_flag:
        logger.info(f"Time-Bound flag detected in {file_path}")
    else:
        logger.warning(f"No Time-Bound flag found in {file_path}")
        
    logger.info(f"Step count: {step_count} (min required: {min_steps})")
    
    if not meets_min_steps:
        error_msg = (
            f"Validation failed: {file_path} has {step_count} steps, "
            f"but minimum {min_steps} required for statistical significance."
        )
        logger.error(error_msg)
        result['error'] = error_msg
    elif not has_flag:
        error_msg = (
            f"Validation failed: {file_path} does not have the 'Time-Bound' flag set."
        )
        logger.error(error_msg)
        result['error'] = error_msg
    else:
        logger.info(f"Validation passed for {file_path}")
    
    return result

def validate_metrics_directory(
    directory: str,
    pattern: str = "*.parquet",
    min_steps: int = 1000
) -> Dict[str, Any]:
    """
    Validate all parquet files in a directory.
    
    Args:
        directory: Path to the directory containing parquet files.
        pattern: Glob pattern for files to validate (default: "*.parquet").
        min_steps: Minimum steps for time-bound validation (default: 1000).
        
    Returns:
        Dictionary with validation results for all files.
    """
    if not os.path.isdir(directory):
        error_msg = f"Directory not found: {directory}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    files = glob.glob(os.path.join(directory, pattern))
    
    results = {
        'directory': directory,
        'total_files': len(files),
        'files': [],
        'summary': {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'nan_errors': 0,
            'time_bound_errors': 0
        }
    }
    
    for file_path in files:
        file_result = {
            'file': file_path,
            'nan_validation': None,
            'time_bound_validation': None,
            'passed': False
        }
        
        # Check for NaNs
        try:
            nan_result = scan_parquet_for_nans(file_path)
            file_result['nan_validation'] = nan_result
            if nan_result['has_nans']:
                results['summary']['nan_errors'] += 1
        except Exception as e:
            file_result['nan_error'] = str(e)
            results['summary']['nan_errors'] += 1
            file_result['passed'] = False
            results['files'].append(file_result)
            continue
        
        # Check for time-bound baseline
        if 'baseline' in os.path.basename(file_path).lower():
            try:
                tb_result = validate_time_bound_baseline(file_path, min_steps)
                file_result['time_bound_validation'] = tb_result
                if tb_result['validation_passed']:
                    file_result['passed'] = True
                    results['summary']['passed'] += 1
                else:
                    file_result['passed'] = False
                    results['summary']['time_bound_errors'] += 1
            except Exception as e:
                file_result['time_bound_error'] = str(e)
                results['summary']['time_bound_errors'] += 1
                file_result['passed'] = False
        else:
            # For non-baseline files, just check NaNs
            if not file_result.get('nan_validation', {}).get('has_nans', False):
                file_result['passed'] = True
                results['summary']['passed'] += 1
            else:
                file_result['passed'] = False
                results['summary']['failed'] += 1
        
        results['summary']['total_validated'] += 1
        results['files'].append(file_result)
    
    # Log summary
    logger.info(f"Validation summary: {results['summary']}")
    
    return results

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate simulation metrics and time-bound baseline runs.'
    )
    parser.add_argument(
        '--path',
        type=str,
        default='data/raw',
        help='Path to the directory or file to validate (default: data/raw)'
    )
    parser.add_argument(
        '--min-steps',
        type=int,
        default=1000,
        help='Minimum steps required for time-bound baseline (default: 1000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to save validation results JSON (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        if os.path.isfile(args.path):
            # Validate a single file
            logger.info(f"Validating single file: {args.path}")
            if 'baseline' in os.path.basename(args.path).lower():
                result = validate_time_bound_baseline(args.path, args.min_steps)
            else:
                result = scan_parquet_for_nans(args.path)
                result['passed'] = not result.get('has_nans', True)
            
            print(json.dumps(result, indent=2, default=str))
            
            if not result.get('passed', False):
                sys.exit(1)
                
        elif os.path.isdir(args.path):
            # Validate directory
            logger.info(f"Validating directory: {args.path}")
            result = validate_metrics_directory(args.path, min_steps=args.min_steps)
            
            print(json.dumps(result, indent=2, default=str))
            
            if result['summary']['failed'] > 0 or result['summary']['time_bound_errors'] > 0:
                sys.exit(1)
        else:
            logger.error(f"Path does not exist: {args.path}")
            sys.exit(1)
            
        # Save results if output path specified
        if args.output:
            os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output}")
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()