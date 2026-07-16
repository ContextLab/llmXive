import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MissingValueError(Exception):
    """Custom exception for missing value handling failures."""
    pass

def detect_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect missing values in the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with missing value statistics per column
    """
    missing_stats = {}
    for col in df.columns:
        total = len(df)
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / total * 100) if total > 0 else 0
        missing_stats[col] = {
            'total': total,
            'missing_count': int(missing_count),
            'missing_pct': float(missing_pct),
            'dtype': str(df[col].dtype)
        }
    
    total_cells = df.size
    total_missing = df.isna().sum().sum()
    overall_missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0
    
    return {
        'columns': missing_stats,
        'summary': {
            'total_cells': int(total_cells),
            'total_missing': int(total_missing),
            'overall_missing_pct': float(overall_missing_pct)
        }
    }

def handle_missing_values(
    df: pd.DataFrame, 
    strategy: str = 'mean', 
    numeric_only: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values based on the specified strategy.
    
    Args:
        df: Input DataFrame
        strategy: 'mean', 'median', 'mode', 'drop', or 'ffill'
        numeric_only: If True, only apply to numeric columns
        
    Returns:
        Tuple of (cleaned DataFrame, imputation log)
    """
    df_clean = df.copy()
    imputation_log = {
        'strategy': strategy,
        'columns_processed': [],
        'values_imputed': 0,
        'rows_dropped': 0
    }
    
    if strategy == 'drop':
        original_len = len(df_clean)
        df_clean = df_clean.dropna()
        imputation_log['rows_dropped'] = original_len - len(df_clean)
        logger.info(f"Dropped {imputation_log['rows_dropped']} rows due to missing values")
    else:
        cols_to_process = df_clean.columns
        if numeric_only:
            cols_to_process = df_clean.select_dtypes(include=[np.number]).columns
        
        for col in cols_to_process:
            missing_count = df_clean[col].isna().sum()
            if missing_count == 0:
                continue
            
            if strategy == 'mean':
                fill_val = df_clean[col].mean()
            elif strategy == 'median':
                fill_val = df_clean[col].median()
            elif strategy == 'mode':
                mode_val = df_clean[col].mode()
                fill_val = mode_val[0] if len(mode_val) > 0 else 0
            elif strategy == 'ffill':
                df_clean[col] = df_clean[col].ffill().bfill()
                imputation_log['columns_processed'].append(col)
                imputation_log['values_imputed'] += missing_count
                logger.info(f"Filled {missing_count} missing values in '{col}' using forward/backward fill")
                continue
            else:
                raise ValueError(f"Unsupported strategy: {strategy}")
            
            if pd.isna(fill_val):
                # If mean/median/mode is NaN (e.g., all values missing), drop column or fill with 0
                logger.warning(f"Cannot compute imputation value for '{col}', filling with 0")
                fill_val = 0
            
            df_clean[col] = df_clean[col].fillna(fill_val)
            imputation_log['columns_processed'].append(col)
            imputation_log['values_imputed'] += missing_count
            logger.info(f"Filled {missing_count} missing values in '{col}' with {strategy} ({fill_val:.4f})")
    
    return df_clean, imputation_log

def generate_cleaning_report(
    original_df: pd.DataFrame, 
    cleaned_df: pd.DataFrame, 
    imputation_log: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive cleaning report.
    
    Args:
        original_df: Original DataFrame before cleaning
        cleaned_df: Cleaned DataFrame
        imputation_log: Log from handle_missing_values
        
    Returns:
        Cleaning report dictionary
    """
    missing_before = detect_missing_values(original_df)
    missing_after = detect_missing_values(cleaned_df)
    
    report = {
        'original_shape': {
            'rows': int(original_df.shape[0]),
            'columns': int(original_df.shape[1])
        },
        'cleaned_shape': {
            'rows': int(cleaned_df.shape[0]),
            'columns': int(cleaned_df.shape[1])
        },
        'missing_before': missing_before,
        'missing_after': missing_after,
        'imputation_details': imputation_log,
        'column_dtypes': {
            col: str(dtype) for col, dtype in cleaned_df.dtypes.items()
        }
    }
    
    return report

def generate_statistical_summaries(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate basic statistical summaries for all numeric columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary containing statistical summaries per column
    """
    summaries = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for statistical summary.")
        return {'summary': {}, 'message': 'No numeric columns found'}
    
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        
        summary = {
            'count': int(len(series)),
            'mean': float(series.mean()),
            'std': float(series.std()) if len(series) > 1 else 0.0,
            'min': float(series.min()),
            'max': float(series.max()),
            'median': float(series.median()),
            'skewness': float(stats.skew(series)) if len(series) > 2 else 0.0,
            'kurtosis': float(stats.kurtosis(series)) if len(series) > 3 else 0.0,
            'q1': float(series.quantile(0.25)),
            'q3': float(series.quantile(0.75)),
            'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
            'outliers_count': int(
                ((series < (series.quantile(0.25) - 1.5 * (series.quantile(0.75) - series.quantile(0.25)))) | 
                 (series > (series.quantile(0.75) + 1.5 * (series.quantile(0.75) - series.quantile(0.25))))).sum()
            )
        }
        summaries[col] = summary
    
    return {
        'summary': summaries,
        'total_numeric_columns': len(numeric_cols),
        'columns_analyzed': list(numeric_cols)
    }

def process_dataset(
    input_path: str, 
    output_path: str, 
    missing_strategy: str = 'mean',
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Main function to process a dataset: detect missing values, handle them,
    and generate statistical summaries.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output cleaned CSV file
        missing_strategy: Strategy for handling missing values
        generate_report: Whether to generate a detailed report
        
    Returns:
        Processing report dictionary
    """
    logger.info(f"Loading dataset from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise MissingValueError(f"Failed to load dataset: {str(e)}")
    
    logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Detect missing values
    missing_stats = detect_missing_values(df)
    logger.info(f"Missing value detection complete. Overall missing: {missing_stats['summary']['overall_missing_pct']:.2f}%")
    
    # Handle missing values
    df_clean, imputation_log = handle_missing_values(df, strategy=missing_strategy)
    
    # Generate statistical summaries
    stat_summaries = generate_statistical_summaries(df_clean)
    
    # Save cleaned dataset
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Cleaned dataset saved to {output_path}")
    
    # Compile report
    report = {
        'input_file': input_path,
        'output_file': output_path,
        'processing_timestamp': pd.Timestamp.now().isoformat(),
        'statistical_summaries': stat_summaries,
        'missing_detection': missing_stats
    }
    
    if generate_report:
        cleaning_report = generate_cleaning_report(df, df_clean, imputation_log)
        report['cleaning_report'] = cleaning_report
    
    return report

def main():
    """
    CLI entry point for dataset processing.
    Expects input file path, output file path, and optional strategy.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Process dataset: clean missing values and generate stats.')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--strategy', type=str, default='mean', 
                        choices=['mean', 'median', 'mode', 'drop', 'ffill'],
                        help='Strategy for handling missing values')
    parser.add_argument('--no-report', action='store_true', help='Skip generating detailed cleaning report')
    
    args = parser.parse_args()
    
    try:
        report = process_dataset(
            input_path=args.input,
            output_path=args.output,
            missing_strategy=args.strategy,
            generate_report=not args.no_report
        )
        
        # Save report to JSON
        report_path = str(Path(args.output).with_suffix('.json'))
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Processing complete. Report saved to {report_path}")
        print(json.dumps(report['statistical_summaries'], indent=2))
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()