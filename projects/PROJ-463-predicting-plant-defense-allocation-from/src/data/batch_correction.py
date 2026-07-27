import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import sys
from datetime import datetime

# Import from project utils as per API surface
from src.utils.logger import get_logger
from src.utils.config import get_housekeeping_genes

logger = get_logger(__name__)

def calculate_cv(values: np.ndarray) -> float:
    """
    Calculate the Coefficient of Variation (CV) for a 1D array of values.
    CV = (Standard Deviation) / (Mean)
    Handles zero or near-zero means to avoid division errors.
    """
    if len(values) == 0:
        return 0.0
    mean_val = np.mean(values)
    if abs(mean_val) < 1e-10:
        return 0.0
    std_val = np.std(values)
    return std_val / abs(mean_val)

def calculate_geomean_m_value(df: pd.DataFrame, housekeeping_genes: List[str]) -> float:
    """
    Calculate the GeNorm M-value for the housekeeping genes.
    M-value is the average pairwise variation of a gene with all other control genes.
    Lower M is better (more stable).
    """
    # Filter to housekeeping genes present in the dataframe
    hk_genes_present = [g for g in housekeeping_genes if g in df.columns]
    
    if len(hk_genes_present) < 2:
        logger.warning(f"Less than 2 housekeeping genes found in data. Available: {hk_genes_present}")
        return 0.0

    hk_df = df[hk_genes_present]
    
    # Normalize by geometric mean of each sample (row)
    # Geometric mean = exp(mean(log(x)))
    # Avoid log(0) by adding small epsilon
    epsilon = 1e-9
    log_df = np.log(hk_df + epsilon)
    geo_means = np.exp(log_df.mean(axis=1))
    
    # Normalize expression
    normalized_df = hk_df.div(geo_means, axis=0)
    
    # Calculate pairwise variations
    m_values = {}
    for gene in hk_genes_present:
        variations = []
        gene_series = normalized_df[gene]
        for other_gene in hk_genes_present:
            if gene == other_gene:
                continue
            other_series = normalized_df[other_gene]
            # Pairwise variation V = standard deviation of log2 ratios
            # log2(gene/other) = log2(gene) - log2(other)
            log_ratios = np.log2(gene_series + epsilon) - np.log2(other_series + epsilon)
            variations.append(np.std(log_ratios))
        m_values[gene] = np.mean(variations)
    
    # M-value is the average of these variations for each gene
    # We return the average M-value across all housekeeping genes as a stability metric
    if not m_values:
        return 0.0
    return np.mean(list(m_values.values()))

def apply_batch_correction(df: pd.DataFrame, method: str = "quantile") -> pd.DataFrame:
    """
    Apply batch correction to the expression matrix.
    Since we don't have explicit batch labels in the simplified task context,
    we use quantile normalization which forces distributions to be identical,
    effectively reducing batch effects if they manifest as distributional shifts.
    
    For a more robust implementation with explicit batch labels, ComBat-seq would be used.
    Here we simulate the effect of batch correction on the CV of housekeeping genes.
    """
    if method == "quantile":
        # Quantile normalization
        # Sort values in each column, calculate mean of sorted values across columns,
        # then replace original values with the mean sorted values at their rank positions.
        df_sorted = df.apply(lambda col: col.sort_values())
        mean_sorted = df_sorted.mean(axis=1)
        
        # Create a mapping from rank to mean value
        # We need to restore original order
        result = df.copy()
        for col in df.columns:
            ranks = df[col].rank(method='average')
            # Map ranks to mean_sorted values
            # Since mean_sorted is indexed by rank (1..N), we align
            result[col] = mean_sorted.reindex(ranks).values
        return result
    else:
        logger.warning(f"Unknown batch correction method: {method}. Returning original data.")
        return df

def calculate_cv_reduction(
    input_path: str,
    output_path: Optional[str] = None,
    housekeeping_genes: Optional[List[str]] = None
) -> Dict:
    """
    Main function to calculate CV reduction for housekeeping genes.
    
    1. Load TPM matrix from input_path.
    2. Calculate pre-correction CV for the fixed list of housekeeping genes.
    3. Apply batch correction.
    4. Calculate post-correction CV for the same genes.
    5. Calculate reduction percent.
    6. Save report to output_path.
    
    Args:
        input_path: Path to input TPM matrix CSV.
        output_path: Path to save the JSON report.
        housekeeping_genes: Optional override for the gene list.
        
    Returns:
        Dictionary containing pre_cv, post_cv, reduction_percent, target_reduction.
    """
    # Load configuration for housekeeping genes if not provided
    if housekeeping_genes is None:
        housekeeping_genes = get_housekeeping_genes()
    
    logger.info(f"Loading TPM matrix from {input_path}")
    df = pd.read_csv(input_path, index_col=0)
    
    # Ensure genes are rows, samples are columns (common for TPM matrices)
    # If the input has genes as columns, we transpose.
    # Assuming the input from T012c has genes as rows and samples as columns.
    # If not, we check: if the first column looks like gene IDs and the rest are numeric samples.
    # For safety, we assume the index is gene IDs.
    
    # Filter for housekeeping genes
    hk_genes_present = [g for g in housekeeping_genes if g in df.index]
    
    if len(hk_genes_present) == 0:
        raise ValueError(f"No housekeeping genes found in input data. Expected some from: {housekeeping_genes[:5]}...")
    
    hk_df = df.loc[hk_genes_present]
    
    # Flatten the values for CV calculation across all samples and genes
    # CV is typically calculated per gene across samples, then averaged, 
    # OR calculated across all values. The task asks for CV reduction on the fixed set.
    # We calculate the average CV across all housekeeping genes.
    
    # Pre-correction CV
    pre_cvs = []
    for gene in hk_genes_present:
        values = hk_df.loc[gene].values
        cv = calculate_cv(values)
        pre_cvs.append(cv)
    pre_cv = np.mean(pre_cvs)
    
    logger.info(f"Pre-correction CV (avg over housekeeping genes): {pre_cv:.4f}")
    
    # Apply batch correction
    logger.info("Applying batch correction (quantile normalization)...")
    corrected_df = apply_batch_correction(df)
    
    # Post-correction CV
    corrected_hk_df = corrected_df.loc[hk_genes_present]
    post_cvs = []
    for gene in hk_genes_present:
        values = corrected_hk_df.loc[gene].values
        cv = calculate_cv(values)
        post_cvs.append(cv)
    post_cv = np.mean(post_cvs)
    
    logger.info(f"Post-correction CV (avg over housekeeping genes): {post_cv:.4f}")
    
    # Calculate reduction
    if pre_cv == 0:
        reduction_percent = 0.0
    else:
        reduction_percent = (pre_cv - post_cv) / pre_cv
    
    report = {
        "pre_correction_cv": float(pre_cv),
        "post_correction_cv": float(post_cv),
        "reduction_percent": float(reduction_percent),
        "target_reduction": 0.20,
        "housekeeping_genes_used": hk_genes_present,
        "num_genes": len(hk_genes_present),
        "timestamp": datetime.now().isoformat()
    }
    
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Batch correction report saved to {output_path}")
    
    return report

def main():
    """CLI entry point for batch correction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate CV reduction for housekeeping genes after batch correction.")
    parser.add_argument("--input", type=str, required=True, help="Path to input TPM matrix CSV.")
    parser.add_argument("--output", type=str, default="data/manifests/batch_correction_report.json", help="Path to output JSON report.")
    parser.add_argument("--mode", type=str, default="real", choices=["real", "synthetic"], help="Mode of operation.")
    
    args = parser.parse_args()
    
    if args.mode == "synthetic":
        logger.info("Running in synthetic mode. Loading synthetic data if available.")
        # In synthetic mode, we might load a pre-generated synthetic TPM matrix
        # For now, we assume the input path is provided and valid
        pass
    
    try:
        report = calculate_cv_reduction(args.input, args.output)
        print(json.dumps(report, indent=2))
    except Exception as e:
        logger.error(f"Batch correction failed: {e}")
        raise

if __name__ == "__main__":
    main()
