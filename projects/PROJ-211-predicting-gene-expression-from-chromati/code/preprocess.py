import os
import sys
import logging
import argparse
import json
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np

from utils import checksum_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(input_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def save_data(df: pd.DataFrame, output_path: str) -> None:
    """Save a DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved data to {output_path}")

def filter_genes_zero_expression(df: pd.DataFrame, gene_col: str = 'gene_id', value_cols: List[str] = None) -> pd.DataFrame:
    """Filter out genes that have zero expression in all samples."""
    if value_cols is None:
        # Assume all columns except gene_id are expression values
        value_cols = [col for col in df.columns if col != gene_col]
    
    # Check if any sample has non-zero expression
    mask = (df[value_cols] != 0).any(axis=1)
    filtered_df = df[mask].copy()
    logger.info(f"Filtered {len(df) - len(filtered_df)} genes with zero expression in all samples.")
    return filtered_df

def apply_log_pseudocount(df: pd.DataFrame, value_cols: List[str] = None, pseudocount: float = 1.0) -> pd.DataFrame:
    """Apply log(x + pseudocount) transformation to expression values."""
    if value_cols is None:
        value_cols = [col for col in df.columns if col != 'gene_id']
    
    df_transformed = df.copy()
    for col in value_cols:
        if col in df_transformed.columns:
            df_transformed[col] = np.log2(df_transformed[col] + pseudocount)
    
    logger.info(f"Applied log pseudocount transformation to {len(value_cols)} columns.")
    return df_transformed

def impute_missing_values_median(df: pd.DataFrame, value_cols: List[str] = None) -> pd.DataFrame:
    """Impute missing values with the median of each column."""
    if value_cols is None:
        value_cols = [col for col in df.columns if col != 'gene_id']
    
    df_imputed = df.copy()
    for col in value_cols:
        if col in df_imputed.columns:
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
    
    logger.info(f"Imputed missing values using median for {len(value_cols)} columns.")
    return df_imputed

def select_top_variable_peaks(df: pd.DataFrame, top_n: int = 1000) -> pd.DataFrame:
    """Select the top N most variable peaks based on variance."""
    # Assuming columns are peaks, calculate variance across rows
    if df.shape[0] == 0:
        return df
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return df
    
    variances = df[numeric_cols].var(axis=0)
    top_peaks = variances.nlargest(top_n).index.tolist()
    
    # Ensure 'gene_id' is included if present
    if 'gene_id' in df.columns:
        top_peaks = ['gene_id'] + top_peaks
    
    result = df[top_peaks]
    logger.info(f"Selected top {top_n} variable peaks.")
    return result

def calculate_coefficient_of_variation(df: pd.DataFrame, value_cols: List[str] = None) -> pd.Series:
    """Calculate the coefficient of variation (CV) for each row (gene) across samples."""
    if value_cols is None:
        value_cols = [col for col in df.columns if col != 'gene_id']
    
    cv_series = df[value_cols].std(axis=1) / df[value_cols].mean(axis=1)
    # Handle division by zero
    cv_series = cv_series.replace([np.inf, -np.inf], np.nan).fillna(0)
    return cv_series

def define_housekeeping_genes(df: pd.DataFrame, cv_threshold: float = 0.2, gene_col: str = 'gene_id') -> pd.DataFrame:
    """Identify housekeeping genes based on coefficient of variation threshold."""
    cv = calculate_coefficient_of_variation(df)
    df_with_cv = df.copy()
    df_with_cv['_cv'] = cv
    
    # Filter for genes with CV < threshold
    housekeeping = df_with_cv[df_with_cv['_cv'] < cv_threshold]
    housekeeping = housekeeping.drop(columns=['_cv'])
    
    logger.info(f"Identified {len(housekeeping)} housekeeping genes (CV < {cv_threshold}).")
    return housekeeping

def define_cell_type_specific_genes(df: pd.DataFrame, cv_threshold: float = 0.5, gene_col: str = 'gene_id') -> pd.DataFrame:
    """Identify cell-type-specific genes based on coefficient of variation threshold."""
    cv = calculate_coefficient_of_variation(df)
    df_with_cv = df.copy()
    df_with_cv['_cv'] = cv
    
    # Filter for genes with CV > threshold
    specific = df_with_cv[df_with_cv['_cv'] > cv_threshold]
    specific = specific.drop(columns=['_cv'])
    
    logger.info(f"Identified {len(specific)} cell-type-specific genes (CV > {cv_threshold}).")
    return specific

def filter_to_gene_list(df: pd.DataFrame, gene_list_path: str, gene_col: str = 'gene_id') -> pd.DataFrame:
    """Filter the DataFrame to only include genes present in the provided gene list file."""
    if not os.path.exists(gene_list_path):
        raise FileNotFoundError(f"Gene list file not found: {gene_list_path}")
    
    gene_list_df = pd.read_csv(gene_list_path)
    if gene_col not in gene_list_df.columns:
        # If the gene list file only contains gene IDs without a column header, assume the first column is the ID
        if len(gene_list_df.columns) >= 1:
            gene_list = gene_list_df.iloc[:, 0].tolist()
        else:
            raise ValueError("Gene list file is empty or has no valid columns.")
    else:
        gene_list = gene_list_df[gene_col].tolist()
    
    filtered_df = df[df[gene_col].isin(gene_list)]
    logger.info(f"Filtered matrix to {len(filtered_df)} genes from the provided list.")
    return filtered_df

def main():
    parser = argparse.ArgumentParser(description="Filter feature matrix to housekeeping genes.")
    parser.add_argument("--input", type=str, default="data/processed/imputed_expression.csv",
                        help="Path to the imputed expression matrix CSV.")
    parser.add_argument("--gene-list", type=str, default="data/processed/housekeeping_genes.csv",
                        help="Path to the housekeeping genes list CSV.")
    parser.add_argument("--output", type=str, default="data/processed/housekeeping_matrix.csv",
                        help="Path to save the filtered housekeeping matrix CSV.")
    parser.add_argument("--gene-col", type=str, default="gene_id",
                        help="Column name for gene identifiers.")
    
    args = parser.parse_args()
    
    try:
        # Load the full imputed expression matrix
        df = load_data(args.input)
        
        # Filter the matrix to only include housekeeping genes
        housekeeping_matrix = filter_to_gene_list(df, args.gene_list, args.gene_col)
        
        # Save the filtered matrix
        save_data(housekeeping_matrix, args.output)
        
        # Calculate and log checksum
        checksum = checksum_file(args.output)
        logger.info(f"Checksum for {args.output}: {checksum}")
        
        # Optionally write checksum to a log file if needed, but task specifically asks for checksum_file usage
        # which is already done.
        
        logger.info("Task T016c completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()