import os
import sys
import logging
import argparse
import json
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np

from utils import checksum_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/preprocess.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_data(input_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def save_data(df: pd.DataFrame, output_path: str) -> None:
    """Save a DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")


def filter_genes_zero_expression(df: pd.DataFrame, expression_cols: List[str]) -> pd.DataFrame:
    """Filter genes with zero expression in all samples."""
    logger.info(f"Filtering genes with zero expression in all samples")
    if not expression_cols:
        raise ValueError("No expression columns provided")
    
    non_zero_mask = (df[expression_cols] > 0).any(axis=1)
    filtered_df = df[non_zero_mask]
    logger.info(f"Filtered {len(df) - len(filtered_df)} genes with zero expression")
    return filtered_df


def apply_log_pseudocount(df: pd.DataFrame, expression_cols: List[str], pseudocount: float = 1.0) -> pd.DataFrame:
    """Apply logarithmic transformation with pseudocount to expression values."""
    logger.info(f"Applying log pseudocount transformation with pseudocount={pseudocount}")
    result_df = df.copy()
    for col in expression_cols:
        result_df[col] = np.log1p(result_df[col])
    logger.info("Log pseudocount transformation complete")
    return result_df


def impute_missing_values_median(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Impute missing values using median per peak/feature."""
    logger.info(f"Imputing missing values using median for {len(feature_cols)} features")
    result_df = df.copy()
    for col in feature_cols:
        median_val = result_df[col].median()
        result_df[col] = result_df[col].fillna(median_val)
    logger.info("Median imputation complete")
    return result_df


def select_top_variable_peaks(df: pd.DataFrame, feature_cols: List[str], top_n: int = 1000) -> List[str]:
    """Select top N most variable peaks based on variance."""
    logger.info(f"Selecting top {top_n} most variable peaks")
    if len(feature_cols) == 0:
        return []
    
    variances = df[feature_cols].var(axis=0)
    top_peaks = variances.nlargest(top_n).index.tolist()
    logger.info(f"Selected top {len(top_peaks)} variable peaks")
    return top_peaks


def calculate_coefficient_of_variation(df: pd.DataFrame, expression_cols: List[str]) -> pd.Series:
    """Calculate coefficient of variation (CV) for each gene across samples."""
    logger.info(f"Calculating coefficient of variation for {len(expression_cols)} samples")
    if len(expression_cols) == 0:
        return pd.Series(dtype=float)
    
    means = df[expression_cols].mean(axis=1)
    stds = df[expression_cols].std(axis=1)
    
    # Avoid division by zero
    cv = stds / means.replace(0, np.nan)
    cv = cv.fillna(0)
    
    logger.info(f"Calculated CV for {len(cv)} genes")
    return cv


def define_housekeeping_genes(df: pd.DataFrame, expression_cols: List[str], threshold: float = 0.2) -> pd.DataFrame:
    """Define housekeeping genes as those with CV < threshold."""
    logger.info(f"Defining housekeeping genes with CV threshold < {threshold}")
    cv_series = calculate_coefficient_of_variation(df, expression_cols)
    
    housekeeping_mask = cv_series < threshold
    housekeeping_genes = df[housekeeping_mask]
    
    logger.info(f"Identified {len(housekeeping_genes)} housekeeping genes")
    return housekeeping_genes


def define_cell_type_specific_genes(df: pd.DataFrame, expression_cols: List[str], threshold: float = 0.5) -> pd.DataFrame:
    """Define cell-type-specific genes as those with CV > threshold."""
    logger.info(f"Defining cell-type-specific genes with CV threshold > {threshold}")
    
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return pd.DataFrame(columns=df.columns)
    
    cv_series = calculate_coefficient_of_variation(df, expression_cols)
    
    cell_type_specific_mask = cv_series > threshold
    cell_type_specific_genes = df[cell_type_specific_mask]
    
    logger.info(f"Identified {len(cell_type_specific_genes)} cell-type-specific genes")
    return cell_type_specific_genes


def preprocess_tss_aggregated_features(input_path: str, output_path: str, gene_col: str = 'gene_id', 
                                       expression_cols: Optional[List[str]] = None) -> None:
    """
    Preprocess TSS aggregated features:
    1. Load data
    2. Identify expression columns if not provided
    3. Filter genes with zero expression
    4. Apply log pseudocount
    5. Impute missing values
    6. Save processed data
    """
    df = load_data(input_path)
    
    if expression_cols is None:
        # Assume all columns except the gene identifier are expression columns
        expression_cols = [col for col in df.columns if col != gene_col]
    
    # Filter genes with zero expression
    df = filter_genes_zero_expression(df, expression_cols)
    
    # Apply log pseudocount
    df = apply_log_pseudocount(df, expression_cols)
    
    # Impute missing values
    df = impute_missing_values_median(df, expression_cols)
    
    # Save processed data
    save_data(df, output_path)
    logger.info(f"Preprocessing complete. Output saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Preprocess gene expression and chromatin accessibility data")
    parser.add_argument('--input', type=str, default='data/processed/imputed_expression.csv',
                        help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/processed/cell_type_specific_genes.csv',
                        help='Output CSV file path for cell-type-specific genes')
    parser.add_argument('--cv-threshold', type=float, default=0.5,
                        help='Coefficient of variation threshold for cell-type-specific genes')
    parser.add_argument('--gene-col', type=str, default='gene_id',
                        help='Column name for gene identifiers')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_data(args.input)
        
        # Identify expression columns (all columns except gene identifier)
        expression_cols = [col for col in df.columns if col != args.gene_col]
        
        if not expression_cols:
            logger.error("No expression columns found in the input file")
            sys.exit(1)
        
        # Define cell-type-specific genes
        cell_type_specific_df = define_cell_type_specific_genes(df, expression_cols, args.cv_threshold)
        
        # Save output
        save_data(cell_type_specific_df, args.output)
        
        # Calculate checksum
        checksum = checksum_file(args.output)
        logger.info(f"Checksum for {args.output}: {checksum}")
        
        # Log checksum to file
        checksum_log_path = 'logs/checksums.txt'
        os.makedirs(os.path.dirname(checksum_log_path), exist_ok=True)
        with open(checksum_log_path, 'a') as f:
            f.write(f"{args.output}: {checksum}\n")
        
        logger.info("Task completed successfully")
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        raise


if __name__ == "__main__":
    main()