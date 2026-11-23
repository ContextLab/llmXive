import os
import sys
import logging
import argparse
import pandas as pd
from typing import List, Optional

# Add project root to path if running as script
if os.path.basename(os.getcwd()) == 'code':
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    sys.path.insert(0, os.getcwd())

from utils import checksum_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyError(Exception):
    """Raised when a required input file is missing or blocked."""
    pass

def load_file_safe(path: str) -> Optional[pd.DataFrame]:
    """Load a CSV file safely, returning None if missing."""
    if not os.path.exists(path):
        logger.warning(f"File not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def check_blocked(path: str) -> bool:
    """Check if a .blocked marker file exists for the given path."""
    blocked_path = path + ".blocked"
    if os.path.exists(blocked_path):
        logger.warning(f"Blocked marker found: {blocked_path}")
        with open(blocked_path, 'r') as f:
            content = f.read().strip()
        logger.warning(f"Block reason: {content}")
        return True
    return False

def write_blocked_marker(path: str, reason: str):
    """Write a .blocked marker file."""
    blocked_path = path + ".blocked"
    with open(blocked_path, 'w') as f:
        f.write(f'{{"status": "blocked", "reason": "{reason}"}}')
    logger.info(f"Written blocked marker: {blocked_path}")

def run_t016c():
    """
    T016c: Filter the binned feature matrix and target vector to only housekeeping genes.
    
    Inputs:
      - data/processed/tss_binned_features.csv
      - data/processed/housekeeping_genes.csv
      - data/processed/imputed_expression.csv (to derive target vector if needed, though T016c description implies filtering the feature matrix primarily)
    
    Deliverable:
      - data/processed/housekeeping_matrix.csv (Filtered feature matrix for housekeeping genes)
    """
    # Define paths
    features_path = "data/processed/tss_binned_features.csv"
    housekeeping_genes_path = "data/processed/housekeeping_genes.csv"
    expression_path = "data/processed/imputed_expression.csv"
    output_path = "data/processed/housekeeping_matrix.csv"

    # Staged Acceptance: Check inputs
    if check_blocked(features_path):
        write_blocked_marker(output_path, "Input tss_binned_features.csv is blocked")
        raise DependencyError("Input tss_binned_features.csv is blocked")
    
    if check_blocked(housekeeping_genes_path):
        write_blocked_marker(output_path, "Input housekeeping_genes.csv is blocked")
        raise DependencyError("Input housekeeping_genes.csv is blocked")

    if check_blocked(expression_path):
        # Even if expression is blocked, we might still have features and gene list, 
        # but typically the target vector comes from expression. 
        # The task says "Filter the binned feature matrix... and target vector".
        # If expression is blocked, we can't form the full joint matrix with targets if required.
        # However, the deliverable is specifically the filtered feature matrix.
        # Let's check if we can proceed with just features and gene list.
        # If the task implies a joint matrix (features + targets), we need expression.
        # Given T015 merged them, let's assume we need to filter the features.
        # If expression is blocked, we might need to block the output if targets are part of the "matrix".
        # The task says "Filter the binned feature matrix... and target vector".
        # If we can't get the target vector, we can't produce the full requested output if it includes targets.
        # Let's assume the output is the feature matrix subset.
        pass 
    
    # Load inputs
    features_df = load_file_safe(features_path)
    housekeeping_df = load_file_safe(housekeeping_genes_path)
    expression_df = load_file_safe(expression_path)

    if features_df is None:
        write_blocked_marker(output_path, "Input tss_binned_features.csv missing")
        raise DependencyError("Input tss_binned_features.csv missing")

    if housekeeping_df is None:
        write_blocked_marker(output_path, "Input housekeeping_genes.csv missing")
        raise DependencyError("Input housekeeping_genes.csv missing")

    # Extract housekeeping gene names
    # Assuming the gene list file has a column 'gene_id' or 'gene_name'
    gene_col = None
    for col in ['gene_id', 'gene_name', 'Gene', 'ID']:
        if col in housekeeping_df.columns:
            gene_col = col
            break
    
    if gene_col is None:
        # Fallback: use the first column
        gene_col = housekeeping_df.columns[0]
        logger.warning(f"Could not find standard gene column, using '{gene_col}'")
    
    housekeeping_genes = set(housekeeping_df[gene_col].astype(str))
    logger.info(f"Loaded {len(housekeeping_genes)} housekeeping genes")

    # Filter features matrix
    # Assuming the first column of features_df is the gene identifier
    feature_gene_col = None
    for col in ['gene_id', 'gene_name', 'Gene', 'ID']:
        if col in features_df.columns:
            feature_gene_col = col
            break
    
    if feature_gene_col is None:
        # Fallback: use the first column
        feature_gene_col = features_df.columns[0]
        logger.warning(f"Could not find standard gene column in features, using '{feature_gene_col}'")

    # Filter rows where gene_id is in housekeeping_genes
    filtered_features = features_df[features_df[feature_gene_col].astype(str).isin(housekeeping_genes)]
    
    logger.info(f"Filtered features matrix: {len(features_df)} rows -> {len(filtered_features)} rows")

    if len(filtered_features) == 0:
        logger.warning("No housekeeping genes found in the feature matrix. Outputting empty matrix.")
    
    # If expression data is available and the task implies a joint matrix (features + targets),
    # we should also filter the expression part.
    # However, the deliverable is named "housekeeping_matrix.csv", which usually refers to the feature matrix X.
    # If the target vector Y is needed, it would be separate or appended.
    # Given T015 produced a merged matrix, and T016c filters that for housekeeping,
    # we assume the output is the subset of the feature matrix.
    # If the "target vector" implies we need to append expression values, we do that if expression_df exists.
    if expression_df is not None:
        # Filter expression for housekeeping genes
        expr_gene_col = None
        for col in ['gene_id', 'gene_name', 'Gene', 'ID']:
            if col in expression_df.columns:
                expr_gene_col = col
                break
        if expr_gene_col is None:
            expr_gene_col = expression_df.columns[0]
        
        filtered_expression = expression_df[expression_df[expr_gene_col].astype(str).isin(housekeeping_genes)]
        
        # Merge filtered features and filtered expression on gene ID
        # Assuming the gene ID column name is the same or we map it
        # We need to ensure the gene column is named consistently for merge
        # Let's standardize the gene column name to 'gene_id' for the merge if possible
        # But to be safe, let's just output the filtered features as the primary deliverable
        # and potentially append expression if the schema suggests it.
        # The task says "Filter the binned feature matrix ... and target vector".
        # This implies the output might contain both.
        # Let's assume the output should have the feature columns and the expression columns.
        # We'll merge on the gene ID.
        
        # Standardize column names for merge
        merged_df = filtered_features.merge(
            filtered_expression, 
            left_on=feature_gene_col, 
            right_on=expr_gene_col, 
            how='inner', 
            suffixes=('_features', '_expression')
        )
        # Drop duplicate gene column if present in suffix
        if f"{feature_gene_col}_expression" in merged_df.columns:
            merged_df = merged_df.drop(columns=[f"{feature_gene_col}_expression"])
        # Rename the key column back if needed, or keep as is
        # The output should be the matrix.
        final_output = merged_df
    else:
        final_output = filtered_features

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_output.to_csv(output_path, index=False)
    logger.info(f"Saved filtered matrix to {output_path}")

    # Checksum
    checksum = checksum_file(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")

    return output_path

def main():
    parser = argparse.ArgumentParser(description="T016c: Filter matrix for housekeeping genes")
    args = parser.parse_args()
    try:
        run_t016c()
    except DependencyError as e:
        logger.error(f"Dependency error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()