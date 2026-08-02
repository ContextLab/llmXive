import os
import sys
import logging
import argparse
import json
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_data(path: str) -> pd.DataFrame:
    """Load data from a CSV file.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        DataFrame containing the data.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def save_data(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        path: Output path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved data to {path}")

def filter_genes_zero_expression(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out genes that have zero expression in all samples.
    
    Args:
        df: DataFrame with gene_id as first column, expression counts in subsequent columns.
        
    Returns:
        Filtered DataFrame.
    """
    # Identify expression columns (all except the first, assuming gene_id)
    expr_cols = df.columns[1:]
    
    # Check if sum across expression columns is zero
    zero_mask = (df[expr_cols].sum(axis=1) == 0)
    filtered_df = df[~zero_mask].copy()
    
    logger.info(f"Filtered {zero_mask.sum()} genes with zero expression. Remaining: {len(filtered_df)}")
    return filtered_df

def apply_log_pseudocount(df: pd.DataFrame) -> pd.DataFrame:
    """Apply logarithmic transformation with pseudocount to expression data.
    
    Transforms: log(counts + 1)
    
    Args:
        df: DataFrame with expression counts.
        
    Returns:
        DataFrame with transformed values.
    """
    expr_cols = df.columns[1:]
    df_transformed = df.copy()
    
    for col in expr_cols:
        df_transformed[col] = np.log2(df[col] + 1)
        
    logger.info("Applied log pseudocount transformation")
    return df_transformed

def impute_missing_values_median(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing values using the median per peak (column).
    
    Args:
        df: DataFrame with potential NaN values.
        
    Returns:
        DataFrame with imputed values.
    """
    expr_cols = df.columns[1:]
    df_imputed = df.copy()
    
    for col in expr_cols:
        median_val = df[col].median()
        df_imputed[col] = df_imputed[col].fillna(median_val)
        
    logger.info("Imputed missing values with median")
    return df_imputed

def select_top_variable_peaks(df: pd.DataFrame, n: int = 1000) -> pd.DataFrame:
    """Select the top N most variable peaks (columns) based on variance.
    
    Args:
        df: DataFrame with expression data.
        n: Number of top peaks to select.
        
    Returns:
        DataFrame containing only the gene_id and top N variable peaks.
    """
    expr_cols = df.columns[1:]
    variances = df[expr_cols].var(axis=0)
    top_peaks = variances.nlargest(n).index.tolist()
    
    result_df = df[['gene_id'] + top_peaks].copy()
    logger.info(f"Selected top {len(top_peaks)} variable peaks")
    return result_df

def calculate_coefficient_of_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the coefficient of variation for each gene across cell lines.
    
    Args:
        df: DataFrame with expression data.
        
    Returns:
        DataFrame with gene_id and CV values.
    """
    expr_cols = df.columns[1:]
    mean_vals = df[expr_cols].mean(axis=1)
    std_vals = df[expr_cols].std(axis=1)
    
    # Avoid division by zero
    cv = (std_vals / mean_vals).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    result_df = pd.DataFrame({'gene_id': df['gene_id'], 'cv': cv})
    return result_df

def define_housekeeping_genes(df_cv: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Define housekeeping genes based on low coefficient of variation.
    
    Args:
        df_cv: DataFrame with gene_id and cv columns.
        threshold: CV threshold below which a gene is considered housekeeping.
        
    Returns:
        DataFrame of housekeeping genes.
    """
    housekeeping = df_cv[df_cv['cv'] < threshold].copy()
    logger.info(f"Identified {len(housekeeping)} housekeeping genes (CV < {threshold})")
    return housekeeping

def define_cell_type_specific_genes(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Define cell-type-specific genes based on high variance.
    
    Args:
        df: DataFrame with expression data.
        threshold: Variance threshold.
        
    Returns:
        DataFrame of cell-type-specific genes.
    """
    expr_cols = df.columns[1:]
    variances = df[expr_cols].var(axis=0)
    # This function logic might need adjustment based on specific definition,
    # but per task T017, it filters genes with variance > threshold.
    # Assuming we calculate variance per gene across samples.
    gene_variances = df[expr_cols].var(axis=1)
    
    specific_genes = df[gene_variances > threshold].copy()
    logger.info(f"Identified {len(specific_genes)} cell-type-specific genes (Var > {threshold})")
    return specific_genes

def preprocess_tss_aggregated_features(input_path: str, output_path: str) -> None:
    """Main pipeline to preprocess TSS aggregated features.
    
    Args:
        input_path: Path to input CSV.
        output_path: Path to output CSV.
    """
    logger.info(f"Loading data from {input_path}")
    df = load_data(input_path)
    
    logger.info("Filtering zero expression genes")
    df = filter_genes_zero_expression(df)
    
    logger.info("Applying log pseudocount")
    df = apply_log_pseudocount(df)
    
    logger.info("Imputing missing values")
    df = impute_missing_values_median(df)
    
    logger.info("Selecting top variable peaks")
    df = select_top_variable_peaks(df, n=1000)
    
    save_data(df, output_path)
    logger.info(f"Preprocessing complete. Output saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess gene expression and accessibility data.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    parser.add_argument("--n-peaks", type=int, default=1000, help="Number of top variable peaks")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Override n-peaks if needed in a more complex pipeline
    # For now, just run the standard pipeline
    preprocess_tss_aggregated_features(args.input, args.output)

if __name__ == "__main__":
    main()
