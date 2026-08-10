import pandas as pd
import numpy as np
import miceforest as mf
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import json
from src.utils.logger import get_logger

logger = get_logger("preprocessing.covariate_handler")

def calculate_missing_ratio(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate the ratio of missing values for specified columns.
    
    Args:
        df: Input DataFrame.
        columns: List of column names to check. If None, checks all numeric and object columns.
                
    Returns:
        Dictionary mapping column names to their missing ratios (0.0 to 1.0).
    """
    if columns is None:
        # Check numeric and object columns, exclude ID columns if they look like IDs
        columns = [c for c in df.columns if df[c].dtype in ['float64', 'int64', 'object', 'bool']]
    
    missing_ratios = {}
    for col in columns:
        total = len(df)
        if total == 0:
            missing_ratios[col] = 0.0
            continue
        missing = df[col].isna().sum()
        missing_ratios[col] = missing / total
        logger.debug(f"Missing ratio for {col}: {missing_ratios[col]:.4f} ({missing}/{total})")
        
    return missing_ratios

def exclude_high_missingness(df: pd.DataFrame, threshold: float = 0.20, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude columns with missingness above the threshold.
    
    Args:
        df: Input DataFrame.
        threshold: Maximum allowed missing ratio (default 0.20).
        columns: Specific columns to evaluate. If None, evaluates all applicable columns.
                
    Returns:
        Tuple of (DataFrame with high-missingness columns removed, list of removed column names).
    """
    ratios = calculate_missing_ratio(df, columns)
    excluded_cols = [col for col, ratio in ratios.items() if ratio > threshold]
    
    if excluded_cols:
        logger.warning(f"Excluding {len(excluded_cols)} columns due to high missingness (> {threshold*100}%): {excluded_cols}")
        return df.drop(columns=excluded_cols), excluded_cols
    
    logger.info(f"No columns excluded; all missingness ratios <= {threshold*100}%")
    return df, []

def impute_with_mice(df: pd.DataFrame, 
                     imputed_cols: Optional[List[str]] = None,
                     iterations: int = 5,
                     random_state: Optional[int] = None) -> Tuple[pd.DataFrame, mf.ImputedData]:
    """
    Perform Multiple Imputation by Chained Equations (MICE) using miceforest.
    
    Args:
        df: Input DataFrame.
        imputed_cols: List of columns to impute. If None, imputes all numeric columns with missing values.
        iterations: Number of MICE iterations.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (DataFrame with imputed values, the ImputedData object for diagnostics).
    """
    if imputed_cols is None:
        imputed_cols = [c for c in df.select_dtypes(include=[np.number]).columns if df[c].isna().any()]
    
    if not imputed_cols:
        logger.info("No columns selected for imputation; returning original DataFrame.")
        return df, None
    
    logger.info(f"Starting MICE imputation for {len(imputed_cols)} columns with {iterations} iterations.")
    
    try:
        # Create the kernel dataset
        kernel = mf.ImputationKernel(
            data=df[imputed_cols],
            datasets=1,
            save_all_iterations_data=True
        )
        
        if random_state is not None:
            np.random.seed(random_state)
        
        # Run imputation
        kernel.mice(iterations)
        
        # Get the completed dataset (using the last iteration)
        imputed_data = kernel.complete_data(dataset=0)
        
        # Replace the original columns in the full DataFrame
        result_df = df.copy()
        result_df[imputed_cols] = imputed_data[imputed_cols]
        
        logger.info(f"MICE imputation completed successfully.")
        return result_df, kernel
        
    except Exception as e:
        logger.error(f"MICE imputation failed: {str(e)}")
        raise

def process_covariates(df: pd.DataFrame, 
                       covariate_cols: List[str],
                       missing_threshold: float = 0.20,
                       impute: bool = True,
                       output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Full pipeline for covariate processing:
    1. Calculate missing ratios.
    2. Exclude columns with missingness > threshold.
    3. Impute remaining missing values using MICE if requested.
    
    Args:
        df: Input DataFrame.
        covariate_cols: List of columns to process.
        missing_threshold: Threshold for excluding columns.
        impute: Whether to perform MICE imputation on remaining missing values.
        output_path: Optional path to save the processed DataFrame.
        
    Returns:
        Processed DataFrame with imputed/excluded covariates.
    """
    logger.info(f"Processing covariates: {covariate_cols}")
    
    # Ensure we only process columns that exist
    available_cols = [c for c in covariate_cols if c in df.columns]
    missing_cols = [c for c in covariate_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Covariate columns not found in DataFrame: {missing_cols}")
    
    if not available_cols:
        logger.warning("No covariate columns found to process.")
        return df
    
    # Step 1: Exclude high missingness
    df_processed, excluded = exclude_high_missingness(df, threshold=missing_threshold, columns=available_cols)
    
    # Step 2: Impute if requested and there are remaining missing values
    if impute:
        remaining_missing = df_processed[available_cols].isna().sum().sum()
        if remaining_missing > 0:
            df_processed, kernel = impute_with_mice(df_processed, imputed_cols=available_cols)
            
            # Log imputation diagnostics if kernel exists
            if kernel:
                logger.info("Imputation diagnostics available in the returned ImputedData object.")
        else:
            logger.info("No missing values remaining after exclusion; skipping imputation.")
    
    # Step 3: Save output if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_processed.to_csv(output_path, index=False)
        logger.info(f"Processed covariates saved to {output_path}")
    
    return df_processed

def main():
    """
    Command-line entry point for covariate processing.
    Expected to be run with arguments specifying input/output paths and configuration.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process covariates with MICE imputation.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV/TSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output processed file.")
    parser.add_argument("--columns", type=str, nargs="+", required=True, help="List of covariate columns to process.")
    parser.add_argument("--threshold", type=float, default=0.20, help="Missingness threshold for exclusion.")
    parser.add_argument("--no-impute", action="store_true", help="Disable MICE imputation.")
    
    args = parser.parse_args()
    
    logger.info(f"Starting covariate processing pipeline for {args.input}")
    
    # Load data
    try:
        if args.input.endswith('.tsv'):
            df = pd.read_csv(args.input, sep='\t')
        else:
            df = pd.read_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        raise
    
    # Process
    df_processed = process_covariates(
        df,
        covariate_cols=args.columns,
        missing_threshold=args.threshold,
        impute=not args.no_impute,
        output_path=Path(args.output)
    )
    
    logger.info("Covariate processing pipeline completed.")

if __name__ == "__main__":
    main()
