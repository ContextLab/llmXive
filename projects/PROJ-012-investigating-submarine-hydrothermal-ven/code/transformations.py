"""
Transformation module for non-normal diversity indices.

Implements CLR (Centered Log-Ratio) and log-transformations for alpha diversity data
to meet GLMM assumptions of normality and homoscedasticity.
"""
import logging
import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Import from existing project modules
from utils import get_logger
from data_models import DiversityMetric

logger = get_logger(__name__)


def add_pseudocount(df: pd.DataFrame, column: str, pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Add a small pseudocount to avoid log(0) issues.
    
    Args:
        df: Input DataFrame
        column: Name of the column to transform
        pseudocount: Small value to add (default 1e-6)
        
    Returns:
        DataFrame with pseudocount added to specified column
    """
    df = df.copy()
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    df[column] = df[column] + pseudocount
    return df


def log_transform(df: pd.DataFrame, column: str, base: float = np.e, pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Apply log transformation to a diversity metric column.
    
    Args:
        df: Input DataFrame
        column: Name of the column to transform
        base: Log base (default: e for natural log)
        pseudocount: Small value to add to avoid log(0)
        
    Returns:
        DataFrame with transformed column
    """
    df = df.copy()
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    # Add pseudocount to handle zeros
    df = add_pseudocount(df, column, pseudocount)
    
    # Apply log transformation
    if base == np.e:
        df[f"{column}_log"] = np.log(df[column])
    else:
        df[f"{column}_log"] = np.log(df[column]) / np.log(base)
    
    logger.info(f"Applied log transformation (base={base}) to column '{column}'")
    return df


def clr_transform(df: pd.DataFrame, columns: List[str], pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to multiple columns.
    
    CLR transformation: clr(x)_i = log(x_i / g(x)) where g(x) is the geometric mean of all components.
    This is appropriate for compositional data like diversity indices when considered jointly.
    
    Args:
        df: Input DataFrame
        columns: List of column names to transform
        pseudocount: Small value to add to avoid log(0)
        
    Returns:
        DataFrame with CLR-transformed columns (named as {column}_clr)
    """
    df = df.copy()
    
    # Validate columns exist
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in DataFrame: {missing}. Available: {list(df.columns)}")
    
    # Add pseudocount to all specified columns
    for col in columns:
        df = add_pseudocount(df, col, pseudocount)
    
    # Calculate geometric mean across the specified columns for each row
    # Geometric mean: exp(mean(log(x)))
    log_values = np.log(df[columns])
    geometric_mean = np.exp(log_values.mean(axis=1))
    
    # Apply CLR transformation: log(x_i / g(x))
    for col in columns:
        clr_col = f"{col}_clr"
        df[clr_col] = np.log(df[col] / geometric_mean)
        logger.debug(f"Calculated CLR for column '{col}'")
    
    logger.info(f"Applied CLR transformation to columns: {columns}")
    return df


def check_normality(df: pd.DataFrame, column: str, method: str = 'shapiro') -> Tuple[float, float]:
    """
    Check normality of a column using Shapiro-Wilk test.
    
    Args:
        df: Input DataFrame
        column: Column to test
        method: Test method ('shapiro' or 'anderson')
        
    Returns:
        Tuple of (statistic, p-value)
    """
    from scipy import stats
    
    data = df[column].dropna()
    
    if len(data) < 3:
        logger.warning(f"Not enough data points ({len(data)}) for normality test on '{column}'")
        return 0.0, 1.0
    
    if method == 'shapiro':
        stat, p_val = stats.shapiro(data)
    else:
        result = stats.anderson(data, dist='norm')
        stat = result.statistic[0]  # Simplified
        p_val = 0.05  # Anderson-Darling doesn't give direct p-value
        
    return stat, p_val


def select_transformation(df: pd.DataFrame, columns: List[str], 
                          target_pvalue: float = 0.05) -> Dict[str, str]:
    """
    Automatically select the best transformation for each column based on normality tests.
    
    Args:
        df: Input DataFrame
        columns: Columns to evaluate
        target_pvalue: P-value threshold for normality (default 0.05)
        
    Returns:
        Dictionary mapping column names to recommended transformations
    """
    recommendations = {}
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found, skipping")
            continue
        
        # Check original normality
        stat, p_val = check_normality(df, col, 'shapiro')
        
        if p_val > target_pvalue:
            recommendations[col] = 'none'
            logger.info(f"Column '{col}' is already normal (p={p_val:.4f})")
            continue
        
        # Try log transformation
        log_df = log_transform(df, col, pseudocount=1e-6)
        log_col = f"{col}_log"
        log_stat, log_p = check_normality(log_df, log_col, 'shapiro')
        
        if log_p > p_val:
            recommendations[col] = 'log'
            logger.info(f"Log transformation improves normality for '{col}' (p: {p_val:.4f} -> {log_p:.4f})")
        else:
            # Try sqrt transformation as alternative
            sqrt_col = f"{col}_sqrt"
            df[sqrt_col] = np.sqrt(df[col])
            sqrt_stat, sqrt_p = check_normality(df, sqrt_col, 'shapiro')
            
            if sqrt_p > p_val:
                recommendations[col] = 'sqrt'
                logger.info(f"Sqrt transformation improves normality for '{col}' (p: {p_val:.4f} -> {sqrt_p:.4f})")
            else:
                recommendations[col] = 'none'
                logger.warning(f"No transformation significantly improved normality for '{col}'")
    
    return recommendations


def run_diversity_transformation(input_path: Union[str, Path], 
                                 output_path: Union[str, Path],
                                 diversity_columns: Optional[List[str]] = None,
                                 method: str = 'auto',
                                 pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Main function to transform diversity metrics for GLMM analysis.
    
    Args:
        input_path: Path to input CSV with diversity metrics
        output_path: Path to write transformed CSV
        diversity_columns: List of columns to transform (default: auto-detect)
        method: 'auto', 'log', 'clr', or 'none'
        pseudocount: Pseudocount for log/CLR transformations
        
    Returns:
        Transformed DataFrame
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    logger.info(f"Loading diversity data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Auto-detect diversity columns if not specified
    if diversity_columns is None:
        diversity_columns = [col for col in df.columns 
                           if col.lower() in ['shannon', 'simpson', 'shannon_diversity', 'simpson_diversity']]
    
    if not diversity_columns:
        raise ValueError("No diversity columns found. Specify 'diversity_columns' parameter.")
    
    logger.info(f"Processing diversity columns: {diversity_columns}")
    
    # Apply transformation based on method
    if method == 'auto':
        recommendations = select_normality = select_transformation(df, diversity_columns)
        transformed_df = df.copy()
        
        for col, rec in recommendations.items():
            if rec == 'log':
                transformed_df = log_transform(transformed_df, col, pseudocount=pseudocount)
            elif rec == 'clr' or rec == 'sqrt':  # Fallback to log if sqrt not implemented
                transformed_df = log_transform(transformed_df, col, pseudocount=pseudocount)
            # 'none' requires no action
        
        logger.info("Auto-selected transformations applied")
        
    elif method == 'log':
        transformed_df = df.copy()
        for col in diversity_columns:
            transformed_df = log_transform(transformed_df, col, pseudocount=pseudocount)
        logger.info(f"Applied log transformation to all specified columns")
        
    elif method == 'clr':
        transformed_df = clr_transform(df, diversity_columns, pseudocount=pseudocount)
        logger.info("Applied CLR transformation to all specified columns")
        
    elif method == 'none':
        transformed_df = df.copy()
        logger.info("No transformation applied")
        
    else:
        raise ValueError(f"Unknown method: {method}. Use 'auto', 'log', 'clr', or 'none'")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    logger.info(f"Writing transformed data to {output_path}")
    transformed_df.to_csv(output_path, index=False)
    
    # Log summary statistics
    for col in diversity_columns:
        original_mean = df[col].mean()
        original_std = df[col].std()
        
        # Find transformed column name
        transformed_col = None
        for suffix in ['_log', '_clr', '_sqrt']:
            if f"{col}{suffix}" in transformed_df.columns:
                transformed_col = f"{col}{suffix}"
                break
        
        if transformed_col:
            trans_mean = transformed_df[transformed_col].mean()
            trans_std = transformed_df[transformed_col].std()
            logger.info(f"  {col}: mean={original_mean:.4f}±{original_std:.4f} -> {transformed_col}: mean={trans_mean:.4f}±{trans_std:.4f}")
    
    return transformed_df


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transform diversity metrics for GLMM analysis")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file path")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file path")
    parser.add_argument("--columns", "-c", nargs="+", default=None, 
                      help="Columns to transform (default: auto-detect)")
    parser.add_argument("--method", "-m", choices=['auto', 'log', 'clr', 'none'], 
                      default='auto', help="Transformation method")
    parser.add_argument("--pseudocount", "-p", type=float, default=1e-6,
                      help="Pseudocount for log/CLR transformations")
    parser.add_argument("--log-level", "-l", default="INFO", 
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)
    
    try:
        run_diversity_transformation(
            input_path=args.input,
            output_path=args.output,
            diversity_columns=args.columns,
            method=args.method,
            pseudocount=args.pseudocount
        )
        logger.info("Transformation completed successfully")
    except Exception as e:
        logger.error(f"Transformation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
