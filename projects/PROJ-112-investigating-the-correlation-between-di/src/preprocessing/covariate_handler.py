import pandas as pd
import numpy as np
import miceforest as mf
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import os
from src.utils.logger import get_logger

def calculate_missing_ratio(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate the missing ratio for specified columns in a DataFrame.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to check. If None, checks all numeric columns.
    
    Returns:
        Series with missing ratio for each column.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    missing_counts = df[columns].isna().sum()
    total_counts = len(df)
    
    return missing_counts / total_counts

def exclude_high_missingness(df: pd.DataFrame, threshold: float = 0.20, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude columns with missing data ratio exceeding the threshold.
    
    Args:
        df: Input DataFrame.
        threshold: Maximum allowed missing ratio (default 0.20).
        columns: List of columns to check. If None, checks all numeric columns.
    
    Returns:
        Tuple of (filtered DataFrame, list of excluded column names).
    """
    missing_ratios = calculate_missing_ratio(df, columns)
    excluded_cols = missing_ratios[missing_ratios > threshold].index.tolist()
    
    if excluded_cols:
        logging.getLogger(__name__).warning(
            f"Excluding {len(excluded_cols)} columns due to missingness > {threshold*100}%: {excluded_cols}"
        )
    
    return df.drop(columns=excluded_cols), excluded_cols

def impute_with_mice(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                     iterations: int = 5, seed: int = 42) -> pd.DataFrame:
    """
    Perform Multiple Imputation by Chained Equations (MICE) using miceforest.
    
    Args:
        df: Input DataFrame.
        columns: List of columns to impute. If None, imputes all numeric columns with missing values.
        iterations: Number of MICE iterations.
        seed: Random seed for reproducibility.
    
    Returns:
        DataFrame with imputed values.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only columns with missing values
    cols_with_missing = [c for c in columns if df[c].isna().any()]
    
    if not cols_with_missing:
        logging.getLogger(__name__).info("No missing values found in specified columns. Skipping imputation.")
        return df.copy()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting MICE imputation on {len(cols_with_missing)} columns with {iterations} iterations.")
    
    # Create a copy to avoid modifying the original
    df_imputed = df.copy()
    
    # Initialize the kernel dataset
    try:
        kernel_data = mf.KernelDataset(
            data=df_imputed[cols_with_missing].copy(),
            verbose=False
        )
        
        # Run imputation
        kernel_data.complete_imputations(
            iterations=iterations,
            random_state=seed
        )
        
        # Extract the first completed dataset (or mean of multiple if needed)
        # Here we take the first iteration's completed data for simplicity
        imputed_values = kernel_data.complete_data(0)
        
        # Replace missing values in the original dataframe
        for col in cols_with_missing:
            df_imputed[col].fillna(imputed_values[col], inplace=True)
    
    except Exception as e:
        logger.error(f"MICE imputation failed: {str(e)}")
        raise
    
    logger.info("MICE imputation completed successfully.")
    return df_imputed

def process_covariates(df: pd.DataFrame, covariate_cols: List[str], 
                       missing_threshold: float = 0.20, 
                       impute_iterations: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full pipeline to process covariates: calculate missingness, exclude high missingness,
    and impute remaining missing values using MICE.
    
    Args:
        df: Input DataFrame.
        covariate_cols: List of covariate column names to process.
        missing_threshold: Threshold for excluding columns (> threshold).
        impute_iterations: Number of MICE iterations.
    
    Returns:
        Tuple of (processed DataFrame, metadata dictionary).
    """
    logger = logging.getLogger(__name__)
    metadata = {
        "original_columns": len(covariate_cols),
        "excluded_columns": [],
        "imputed_columns": [],
        "total_rows": len(df)
    }
    
    logger.info(f"Processing {len(covariate_cols)} covariates with missing threshold {missing_threshold}.")
    
    # Filter to existing columns
    existing_cols = [c for c in covariate_cols if c in df.columns]
    if len(existing_cols) < len(covariate_cols):
        missing_cols = set(covariate_cols) - set(existing_cols)
        logger.warning(f"Covariates not found in DataFrame: {missing_cols}")
    metadata["original_columns"] = len(existing_cols)
    
    # Exclude high missingness
    df_filtered, excluded = exclude_high_missingness(
        df[existing_cols].copy(), 
        threshold=missing_threshold
    )
    metadata["excluded_columns"] = excluded
    
    # Impute remaining
    if df_filtered.isna().any().any():
        df_imputed = impute_with_mice(df_filtered, iterations=impute_iterations)
        metadata["imputed_columns"] = df_filtered.columns[df_filtered.isna().any()].tolist()
        # Actually, after imputation there should be no missing values in these columns
        # unless the imputation failed or columns were non-numeric
        metadata["imputed_columns"] = [c for c in df_imputed.columns if df_imputed[c].isna().any()]
    else:
        df_imputed = df_filtered
        metadata["imputed_columns"] = []
    
    logger.info(f"Covariate processing complete. Excluded: {len(excluded)}, Imputed: {len(metadata['imputed_columns'])}")
    
    return df_imputed, metadata

def main():
    """
    Example usage of the covariate handler pipeline.
    Reads a CSV from data/processed/, processes covariates, and saves the result.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process covariates with MICE imputation.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file path.")
    parser.add_argument("--covariates", type=str, nargs="+", required=True, 
                        help="List of covariate column names.")
    parser.add_argument("--threshold", type=float, default=0.20, 
                        help="Missing data threshold for exclusion.")
    parser.add_argument("--iterations", type=int, default=5, 
                        help="Number of MICE iterations.")
    
    args = parser.parse_args()
    
    logger = get_logger("covariate_handler")
    logger.info(f"Starting covariate processing for {args.input}")
    
    # Load data
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    
    # Process covariates
    df_processed, metadata = process_covariates(
        df, 
        args.covariates, 
        missing_threshold=args.threshold, 
        impute_iterations=args.iterations
    )
    
    # Save results
    df_processed.to_csv(args.output, index=False)
    logger.info(f"Processed data saved to {args.output}")
    
    # Log metadata
    logger.info(f"Metadata: {metadata}")

if __name__ == "__main__":
    main()
