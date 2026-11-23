import pandas as pd
import numpy as np
import miceforest as mf
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

def calculate_missing_ratio(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate the missing data ratio for specified columns.
    
    Args:
        df: Input DataFrame
        columns: List of column names to check. If None, checks all columns.
    
    Returns:
        Dictionary mapping column names to their missing ratios.
    """
    if columns is None:
        columns = df.columns.tolist()
    
    missing_ratios = {}
    for col in columns:
        if col in df.columns:
            missing_ratios[col] = df[col].isna().sum() / len(df)
        else:
            missing_ratios[col] = 0.0
    
    return missing_ratios

def exclude_high_missingness(
    df: pd.DataFrame, 
    threshold: float = 0.20, 
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude rows where missing data exceeds the threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed missing ratio (default 0.20 for 20%)
        columns: List of columns to consider for missingness check.
    
    Returns:
        Tuple of (filtered DataFrame, list of excluded sample IDs).
    """
    if columns is None:
        columns = df.columns.tolist()
    
    # Calculate missing ratio per row for the specified columns
    missing_counts = df[columns].isna().sum(axis=1)
    total_columns = len(columns)
    missing_ratio = missing_counts / total_columns
    
    # Identify rows to exclude
    exclude_mask = missing_ratio > threshold
    excluded_indices = df.index[exclude_mask].tolist()
    
    # Filter dataframe
    filtered_df = df[~exclude_mask].copy()
    
    return filtered_df, excluded_indices

def impute_with_mice(
    df: pd.DataFrame, 
    columns: Optional[List[str]] = None, 
    n_iterations: int = 5, 
    kernel: str = "lightgbm",
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Perform Multiple Imputation by Chained Equations (MICE) using miceforest.
    
    Args:
        df: Input DataFrame with missing values.
        columns: List of columns to impute. If None, imputes all numeric columns with missing values.
        n_iterations: Number of imputation iterations.
        kernel: Kernel type for imputation ('lightgbm' or 'knn').
        random_seed: Random seed for reproducibility.
    
    Returns:
        DataFrame with imputed values (single imputed version).
    """
    if df.empty:
        return df
    
    # Determine columns to impute
    if columns is None:
        # Select numeric columns that have missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        columns_to_impute = [col for col in numeric_cols if df[col].isna().any()]
    else:
        columns_to_impute = [col for col in columns if col in df.columns and df[col].isna().any()]
    
    if not columns_to_impute:
        return df.copy()
    
    # Initialize the dataset
    kernel_func = getattr(mf, kernel.capitalize(), mf.LightGBM)
    imputation_data = mf.ImputationKernel(
        df[columns_to_impute],
        n_iterations=n_iterations,
        random_seed=random_seed,
        save_all_iterations_data=False
    )
    
    # Run imputation
    imputation_data.impute()
    
    # Get the completed dataset (using the last iteration)
    completed_df = imputation_data.complete_data()
    
    # Reconstruct full dataframe
    result_df = df.copy()
    result_df[columns_to_impute] = completed_df[columns_to_impute]
    
    return result_df

def process_covariates(
    input_path: str, 
    output_path: str, 
    exclusion_log_path: str,
    threshold: float = 0.20,
    impute: bool = True,
    columns: Optional[List[str]] = None,
    n_iterations: int = 5,
    kernel: str = "lightgbm",
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Main pipeline to process covariates: exclude high missingness and impute remaining.
    
    Args:
        input_path: Path to input TSV/CSV file.
        output_path: Path to write the processed DataFrame.
        exclusion_log_path: Path to write the exclusion log.
        threshold: Maximum allowed missing ratio for exclusion.
        impute: Whether to perform MICE imputation on remaining data.
        columns: Columns to process.
        n_iterations: MICE iterations.
        kernel: MICE kernel type.
        random_seed: Random seed.
    
    Returns:
        Dictionary with processing statistics.
    """
    # Load data
    if input_path.endswith('.tsv'):
        df = pd.read_csv(input_path, sep='\t')
    else:
        df = pd.read_csv(input_path)
    
    original_count = len(df)
    
    # Exclude high missingness
    filtered_df, excluded_ids = exclude_high_missingness(df, threshold, columns)
    excluded_count = original_count - len(filtered_df)
    
    # Write exclusion log
    with open(exclusion_log_path, 'w') as f:
        f.write(f"Covariate Exclusion Log\n")
        f.write(f"=======================\n")
        f.write(f"Threshold: {threshold * 100}%\n")
        f.write(f"Original sample count: {original_count}\n")
        f.write(f"Excluded sample count: {excluded_count}\n")
        f.write(f"Remaining sample count: {len(filtered_df)}\n")
        f.write(f"\nExcluded Sample IDs:\n")
        for sid in excluded_ids:
            f.write(f"{sid}\n")
    
    # Perform imputation if requested and data exists
    if impute and not filtered_df.empty:
        imputed_df = impute_with_mice(filtered_df, columns, n_iterations, kernel, random_seed)
    else:
        imputed_df = filtered_df
    
    # Save output
    if output_path.endswith('.tsv'):
        imputed_df.to_csv(output_path, sep='\t', index=False)
    else:
        imputed_df.to_csv(output_path, index=False)
    
    return {
        "original_count": original_count,
        "excluded_count": excluded_count,
        "remaining_count": len(imputed_df),
        "imputed": impute and not filtered_df.empty
    }

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for the covariate handler script."""
    parser = argparse.ArgumentParser(description="Process covariates with MICE imputation and exclusion logic.")
    parser.add_argument("--input", type=str, required=True, help="Path to input TSV/CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output processed file.")
    parser.add_argument("--exclusion-log", type=str, required=True, help="Path to exclusion log file.")
    parser.add_argument("--threshold", type=float, default=0.20, help="Missing data threshold for exclusion (default: 0.20).")
    parser.add_argument("--no-impute", action="store_true", help="Disable MICE imputation.")
    parser.add_argument("--columns", type=str, nargs="+", default=None, help="Columns to process.")
    parser.add_argument("--iterations", type=int, default=5, help="Number of MICE iterations.")
    parser.add_argument("--kernel", type=str, default="lightgbm", choices=["lightgbm", "knn"], help="MICE kernel type.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser

def main():
    """Main entry point for the script."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    columns = args.columns if args.columns else None
    
    stats = process_covariates(
        input_path=args.input,
        output_path=args.output,
        exclusion_log_path=args.exclusion_log,
        threshold=args.threshold,
        impute=not args.no_impute,
        columns=columns,
        n_iterations=args.iterations,
        kernel=args.kernel,
        random_seed=args.seed
    )
    
    print(f"Processing complete. Stats: {stats}")

if __name__ == "__main__":
    main()
