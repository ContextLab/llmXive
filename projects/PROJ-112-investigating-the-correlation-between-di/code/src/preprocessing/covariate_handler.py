import pandas as pd
import numpy as np
import miceforest as mf
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import os

from src.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_missing_ratio(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate the ratio of missing values per column.
    
    Args:
        df: Input DataFrame
        columns: List of columns to check. If None, checks all numeric and object columns.
    
    Returns:
        Series with missing ratio per column.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number, object]).columns.tolist()
    
    missing_counts = df[columns].isna().sum()
    total_counts = len(df)
    
    return (missing_counts / total_counts).round(4)

def exclude_high_missingness(
    df: pd.DataFrame, 
    threshold: float = 0.20, 
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude columns with missingness above a threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed missing ratio (default 0.20).
        columns: Specific columns to evaluate. If None, evaluates all applicable columns.
    
    Returns:
        Tuple of (DataFrame with excluded columns, list of excluded column names)
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number, object]).columns.tolist()
    
    missing_ratios = calculate_missing_ratio(df, columns)
    excluded_cols = missing_ratios[missing_ratios > threshold].index.tolist()
    
    if excluded_cols:
        logger.warning(f"Excluding {len(excluded_cols)} columns due to missingness > {threshold*100}%: {excluded_cols}")
        df_filtered = df.drop(columns=excluded_cols)
        return df_filtered, excluded_cols
    
    logger.info("No columns excluded due to missingness threshold.")
    return df, []

def impute_with_mice(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    number_of_iterations: int = 5,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Perform MICE imputation using miceforest.
    
    Args:
        df: Input DataFrame with missing values.
        columns: Columns to impute. If None, imputes all numeric columns with missing values.
        number_of_iterations: Number of MICE iterations.
        random_state: Random seed for reproducibility.
    
    Returns:
        Imputed DataFrame.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only columns that actually have missing values
    cols_to_impute = [col for col in columns if df[col].isna().any()]
    
    if not cols_to_impute:
        logger.info("No missing values found in specified columns. Returning original DataFrame.")
        return df.copy()
    
    logger.info(f"Starting MICE imputation on {len(cols_to_impute)} columns for {number_of_iterations} iterations.")
    
    try:
        kernel = mf.ImputationKernel(
            df[cols_to_impute],
            datasets=1,
            random_state=random_state
        )
        
        kernel.mice(number_of_iterations=number_of_iterations)
        
        imputed_data = kernel.complete_data(dataset=0)
        
        # Merge back with non-imputed columns
        df_imputed = df.copy()
        df_imputed[cols_to_impute] = imputed_data[cols_to_impute]
        
        logger.info("MICE imputation completed successfully.")
        return df_imputed
        
    except Exception as e:
        logger.error(f"MICE imputation failed: {str(e)}")
        raise

def process_covariates(
    df: pd.DataFrame,
    covariate_columns: List[str],
    missing_threshold: float = 0.20,
    impute: bool = True,
    num_iterations: int = 5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main pipeline for covariate handling: exclusion and imputation.
    
    Args:
        df: Input DataFrame.
        covariate_columns: List of columns to process.
        missing_threshold: Threshold for excluding columns (>20% missing).
        impute: Whether to perform MICE imputation on remaining missing values.
        num_iterations: Number of MICE iterations if imputation is performed.
    
    Returns:
        Tuple of (processed DataFrame, processing summary dict)
    """
    logger.info(f"Starting covariate processing for columns: {covariate_columns}")
    
    summary = {
        "original_columns": len(covariate_columns),
        "excluded_columns": [],
        "imputed_columns": [],
        "final_columns": []
    }
    
    # Step 1: Exclude high missingness
    df_filtered, excluded = exclude_high_missingness(
        df, 
        threshold=missing_threshold, 
        columns=covariate_columns
    )
    summary["excluded_columns"] = excluded
    
    # Step 2: Impute remaining missing values if requested
    if impute:
        df_processed = impute_with_mice(
            df_filtered,
            columns=[c for c in covariate_columns if c in df_filtered.columns],
            number_of_iterations=num_iterations
        )
        # Identify which columns had imputation actually applied
        summary["imputed_columns"] = [c for c in covariate_columns if c in df_processed.columns and df[c].isna().any()]
    else:
        df_processed = df_filtered
        summary["imputed_columns"] = []
    
    summary["final_columns"] = [c for c in covariate_columns if c in df_processed.columns]
    
    logger.info(f"Covariate processing complete. Retained {len(summary['final_columns'])} columns.")
    
    return df_processed, summary

def main():
    """
    CLI entry point for covariate handling demonstration/testing.
    Reads a sample CSV, processes covariates, and saves results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process covariates with MICE imputation and exclusion.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file.")
    parser.add_argument("--columns", type=str, nargs="+", required=True, help="List of covariate columns to process.")
    parser.add_argument("--threshold", type=float, default=0.20, help="Missingness threshold for exclusion.")
    parser.add_argument("--no-impute", action="store_true", help="Disable MICE imputation.")
    parser.add_argument("--iterations", type=int, default=5, help="Number of MICE iterations.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    logger.info(f"Processing covariates: {args.columns}")
    df_processed, summary = process_covariates(
        df,
        covariate_columns=args.columns,
        missing_threshold=args.threshold,
        impute=not args.no_impute,
        num_iterations=args.iterations
    )
    
    logger.info(f"Saving processed data to {args.output}")
    df_processed.to_csv(args.output, index=False)
    
    # Save summary to a sidecar file
    summary_path = args.output.replace('.csv', '_summary.json')
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Processing summary saved to {summary_path}")
    return 0

if __name__ == "__main__":
    exit(main())
