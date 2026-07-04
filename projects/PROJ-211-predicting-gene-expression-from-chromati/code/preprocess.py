"""
Preprocessing module for gene expression and chromatin accessibility data.
Implements filtering, transformation, imputation, and gene selection logic.
"""
import os
import sys
import logging
import argparse
import json
from typing import Tuple, List, Optional

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(filepath: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    logger.info(f"Loading data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def save_data(df: pd.DataFrame, filepath: str) -> None:
    """Save a DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    logger.info(f"Saving data to {filepath}")
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows to {filepath}")


def filter_genes_zero_expression(df: pd.DataFrame, expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter out genes with zero expression in all samples.
    
    Args:
        df: DataFrame containing gene data
        expression_cols: List of column names representing expression values.
                       If None, assumes all numeric columns after the first are expression.
    
    Returns:
        Filtered DataFrame
    """
    if expression_cols is None:
        # Assume first column is gene identifier, rest are numeric expression
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 0:
            expression_cols = numeric_cols
        else:
            logger.warning("No numeric columns found for expression filtering")
            return df
    
    # Check if all expression values are zero for each gene
    mask = (df[expression_cols] == 0).all(axis=1)
    filtered_df = df[~mask]
    removed_count = len(df) - len(filtered_df)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} genes with zero expression in all samples")
    else:
        logger.info("No genes removed (none had zero expression in all samples)")
    return filtered_df


def apply_log_pseudocount(df: pd.DataFrame, expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply logarithmic pseudocount transformation: log(counts + 1).
    
    Args:
        df: DataFrame containing count data
        expression_cols: List of column names to transform.
                       If None, transforms all numeric columns.
    
    Returns:
        Transformed DataFrame
    """
    result_df = df.copy()
    if expression_cols is None:
        expression_cols = result_df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in expression_cols:
        result_df[col] = np.log1p(result_df[col])
    
    logger.info(f"Applied log pseudocount transformation to {len(expression_cols)} columns")
    return result_df


def preprocess_tss_aggregated_features(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Main preprocessing pipeline for TSS aggregated features.
    1. Filter genes with zero expression
    2. Apply log pseudocount
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
    
    Returns:
        Processed DataFrame
    """
    df = load_data(input_path)
    df = filter_genes_zero_expression(df)
    df = apply_log_pseudocount(df)
    save_data(df, output_path)
    return df


def impute_missing_values_median(df: pd.DataFrame, expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Impute missing values using the median per column (per peak/gene feature).
    
    Args:
        df: DataFrame with potential missing values
        expression_cols: Columns to impute. If None, all numeric columns.
    
    Returns:
        DataFrame with imputed values
    """
    result_df = df.copy()
    if expression_cols is None:
        expression_cols = result_df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in expression_cols:
        median_val = result_df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        result_df[col] = result_df[col].fillna(median_val)
    
    logger.info(f"Imputed missing values using median for {len(expression_cols)} columns")
    return result_df


def select_top_variable_peaks(df: pd.DataFrame, n: int = 1000, expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Select top N features (peaks) based on variance across samples.
    
    Args:
        df: Input DataFrame
        n: Number of top variable peaks to select
        expression_cols: Columns to calculate variance on. If None, all numeric cols.
    
    Returns:
        DataFrame with only the top N variable peaks
    """
    if expression_cols is None:
        expression_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    variances = df[expression_cols].var()
    top_vars = variances.nlargest(n)
    top_peak_names = top_vars.index.tolist()
    
    # Assume first column is identifier, rest are data
    id_col = df.columns[0]
    result_df = df[[id_col] + top_peak_names]
    
    logger.info(f"Selected top {n} variable peaks based on variance")
    return result_df


def calculate_coefficient_of_variation(df: pd.DataFrame, expression_cols: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate the coefficient of variation (CV) for each gene across samples.
    CV = std / mean.
    
    Args:
        df: Input DataFrame
        expression_cols: Columns to calculate CV on.
    
    Returns:
        Series of CV values indexed by gene identifier
    """
    if expression_cols is None:
        expression_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    means = df[expression_cols].mean(axis=1)
    stds = df[expression_cols].std(axis=1)
    
    # Avoid division by zero
    cv = stds / means.replace(0, np.nan)
    return cv


def define_housekeeping_genes(df: pd.DataFrame, output_path: str, 
                              cv_threshold: float = 0.2, 
                              n_genes: int = 500,
                              gene_col: str = 'gene_id',
                              expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Identify housekeeping genes: low coefficient of variation across cell lines.
    
    Args:
        df: Input DataFrame with expression data
        output_path: Path to save the CSV of housekeeping genes
        cv_threshold: Maximum CV threshold (default 0.2)
        n_genes: Maximum number of genes to return (default 500)
        gene_col: Name of the gene identifier column
        expression_cols: Columns representing expression values
    
    Returns:
        DataFrame of selected housekeeping genes
    """
    logger.info("Calculating coefficient of variation for housekeeping gene selection")
    
    if expression_cols is None:
        expression_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    cv_series = calculate_coefficient_of_variation(df, expression_cols)
    
    # Filter genes with CV <= threshold
    low_cv_mask = cv_series <= cv_threshold
    candidates = df[low_cv_mask]
    
    logger.info(f"Found {len(candidates)} genes with CV <= {cv_threshold}")
    
    # Sort by CV (lowest first) and take top N
    candidates = candidates.sort_values(by=cv_series.name) # This might need adjustment based on actual series name
    # Recalculate CV on the subset to sort correctly if the series was filtered
    cv_subset = calculate_coefficient_of_variation(candidates, expression_cols)
    candidates = candidates.sort_values(by=cv_subset.name)
    
    selected = candidates.head(n_genes)
    
    logger.info(f"Selected {len(selected)} housekeeping genes")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    selected.to_csv(output_path, index=False)
    
    return selected


def define_cell_type_specific_genes(df: pd.DataFrame, output_path: str,
                                    variance_threshold: float = 0.5,
                                    n_genes: int = 500,
                                    gene_col: str = 'gene_id',
                                    expression_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Identify cell-type-specific genes: high variance across cell lines.
    
    Args:
        df: Input DataFrame with expression data (imputed)
        output_path: Path to save the CSV of cell-type-specific genes
        variance_threshold: Minimum variance threshold (default 0.5)
        n_genes: Maximum number of genes to return (default 500)
        gene_col: Name of the gene identifier column
        expression_cols: Columns representing expression values
    
    Returns:
        DataFrame of selected cell-type-specific genes
    """
    logger.info("Calculating variance for cell-type-specific gene selection")
    
    if expression_cols is None:
        expression_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate variance across samples (axis=1) for each gene
    variances = df[expression_cols].var(axis=1)
    
    # Filter genes with variance > threshold
    high_var_mask = variances > variance_threshold
    candidates = df[high_var_mask]
    
    logger.info(f"Found {len(candidates)} genes with variance > {variance_threshold}")
    
    if len(candidates) == 0:
        logger.warning("No genes found above the variance threshold. Returning empty file or adjusting threshold.")
        # If no genes meet the strict threshold, we might still want to return the top N most variable
        # to ensure the pipeline produces an artifact, but strictly following the spec:
        # "Define cell-type-specific genes (500 genes, variance > 0.5)"
        # If fewer than 500 exist, we return what exists.
        selected = candidates.head(n_genes)
    else:
        # Sort by variance (highest first) and take top N
        candidates = candidates.sort_values(by=variances.name, ascending=False)
        selected = candidates.head(n_genes)
    
    logger.info(f"Selected {len(selected)} cell-type-specific genes")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    selected.to_csv(output_path, index=False)
    
    return selected


def main():
    """
    CLI entry point for preprocessing tasks.
    """
    parser = argparse.ArgumentParser(description="Preprocessing pipeline for gene expression data")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # T017: Define cell-type-specific genes
    parser_t017 = subparsers.add_parser("t017", help="Define cell-type-specific genes")
    parser_t017.add_argument("--input", type=str, required=True, 
                             help="Path to imputed expression CSV")
    parser_t017.add_argument("--output", type=str, required=True,
                             help="Path to output CSV for cell-type-specific genes")
    parser_t017.add_argument("--variance-threshold", type=float, default=0.5,
                             help="Minimum variance threshold (default: 0.5)")
    parser_t017.add_argument("--n-genes", type=int, default=500,
                             help="Maximum number of genes to select (default: 500)")
    
    # T016: Define housekeeping genes (for completeness)
    parser_t016 = subparsers.add_parser("t016", help="Define housekeeping genes")
    parser_t016.add_argument("--input", type=str, required=True,
                             help="Path to imputed expression CSV")
    parser_t016.add_argument("--output", type=str, required=True,
                             help="Path to output CSV for housekeeping genes")
    parser_t016.add_argument("--cv-threshold", type=float, default=0.2,
                             help="Maximum CV threshold (default: 0.2)")
    parser_t016.add_argument("--n-genes", type=int, default=500,
                             help="Maximum number of genes to select (default: 500)")
    
    args = parser.parse_args()
    
    if args.command == "t017":
        logger.info(f"Running T017: Cell-type-specific gene definition")
        logger.info(f"Input: {args.input}")
        logger.info(f"Output: {args.output}")
        logger.info(f"Variance Threshold: {args.variance_threshold}")
        logger.info(f"Max Genes: {args.n_genes}")
        
        df = load_data(args.input)
        define_cell_type_specific_genes(
            df, 
            args.output, 
            variance_threshold=args.variance_threshold,
            n_genes=args.n_genes
        )
        logger.info("T017 completed successfully")
        
    elif args.command == "t016":
        logger.info(f"Running T016: Housekeeping gene definition")
        df = load_data(args.input)
        define_housekeeping_genes(
            df,
            args.output,
            cv_threshold=args.cv_threshold,
            n_genes=args.n_genes
        )
        logger.info("T016 completed successfully")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()