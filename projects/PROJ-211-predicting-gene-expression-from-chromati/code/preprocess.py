import os
import sys
import logging
import argparse
import json
from typing import Tuple, List, Optional
import pandas as pd
import hashlib

from utils import checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DependencyError(Exception):
    """Raised when a required input file is missing or blocked."""
    pass

def load_data(file_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    logger.info(f"Loading data from {file_path}")
    return pd.read_csv(file_path)

def save_data(df: pd.DataFrame, file_path: str) -> None:
    """Save a DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info(f"Saved data to {file_path}")

def merge_peak_features_and_expression(
    peak_features_path: str,
    expression_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Merge aggregated peak features with gene expression counts to form the joint matrix.
    
    Inputs:
      - peak_features_path: Path to tss_binned_features.csv (Rows=Genes, Cols=200 Bins)
      - expression_path: Path to imputed_expression.csv (Rows=Genes, Cols=Cell Lines)
      - output_path: Path to save the merged matrix
      
    Returns:
      - The merged DataFrame
    """
    if not os.path.exists(peak_features_path):
        raise FileNotFoundError(f"Peak features file not found: {peak_features_path}")
    if not os.path.exists(expression_path):
        raise FileNotFoundError(f"Expression file not found: {expression_path}")
    
    # Check for blocked markers
    if os.path.exists(peak_features_path + ".blocked"):
        raise DependencyError(f"Input {peak_features_path} is blocked.")
    if os.path.exists(expression_path + ".blocked"):
        raise DependencyError(f"Input {expression_path} is blocked.")

    logger.info(f"Loading peak features from {peak_features_path}")
    peak_df = pd.read_csv(peak_features_path)
    
    logger.info(f"Loading expression data from {expression_path}")
    expr_df = pd.read_csv(expression_path)

    # Determine the common key column (usually 'GeneID' or 'gene_id')
    # We assume both files have a column named 'GeneID' based on project conventions.
    key_col = 'GeneID'
    
    if key_col not in peak_df.columns:
        # Fallback: try to find a similar column
        candidates = [c for c in peak_df.columns if 'gene' in c.lower()]
        if candidates:
            key_col = candidates[0]
            logger.warning(f"Using '{key_col}' as key column for peak features.")
        else:
            raise ValueError(f"Could not find gene identifier column in {peak_features_path}")

    if key_col not in expr_df.columns:
        candidates = [c for c in expr_df.columns if 'gene' in c.lower()]
        if candidates:
            key_col = candidates[0]
            logger.warning(f"Using '{key_col}' as key column for expression data.")
        else:
            raise ValueError(f"Could not find gene identifier column in {expression_path}")

    # Ensure key column is consistent
    peak_df[key_col] = peak_df[key_col].astype(str)
    expr_df[key_col] = expr_df[key_col].astype(str)

    # Merge on the gene key
    # Inner join ensures we only keep genes present in both datasets
    merged_df = pd.merge(peak_df, expr_df, on=key_col, how='inner')
    
    if merged_df.empty:
        logger.warning("Merge resulted in an empty DataFrame. No common genes found.")
    
    logger.info(f"Merged matrix shape: {merged_df.shape}")
    
    # Save the result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged matrix to {output_path}")
    
    return merged_df

def main():
    parser = argparse.ArgumentParser(description="Merge peak features and expression data.")
    parser.add_argument(
        "--peak-features", 
        type=str, 
        default="data/processed/tss_binned_features.csv",
        help="Path to the binned peak features CSV."
    )
    parser.add_argument(
        "--expression", 
        type=str, 
        default="data/processed/imputed_expression.csv",
        help="Path to the imputed expression CSV."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/merged_matrix.csv",
        help="Path to save the merged matrix."
    )
    
    args = parser.parse_args()
    
    try:
        # Perform the merge
        merged_df = merge_peak_features_and_expression(
            args.peak_features,
            args.expression,
            args.output
        )
        
        # Calculate and log checksum
        checksum = checksum_file(args.output)
        logger.info(f"Checksum for {args.output}: {checksum}")
        
        print(f"Success: Merged matrix saved to {args.output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except DependencyError as e:
        # Staged Acceptance: Write blocked marker
        blocked_path = args.output + ".blocked"
        logger.error(f"Dependency error: {e}")
        with open(blocked_path, 'w') as f:
            json.dump({"status": "blocked", "reason": "Input missing"}, f)
        logger.info(f"Created blocked marker: {blocked_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()