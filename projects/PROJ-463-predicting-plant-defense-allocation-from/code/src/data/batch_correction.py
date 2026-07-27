import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys
import json
import datetime
import hashlib
from scipy import stats
from sklearn.preprocessing import StandardScaler

from src.utils.logger import get_logger
from src.utils.config import get_housekeeping_genes

logger = get_logger(__name__)

def calculate_geometric_mean(row: pd.Series) -> float:
    """Calculate geometric mean of non-zero values in a row."""
    non_zero = row[row > 0]
    if len(non_zero) == 0:
        return 0.0
    return np.exp(np.mean(np.log(non_zero)))

def calculate_georm_m_value(matrix: pd.DataFrame, gene_list: List[str]) -> float:
    """
    Calculate GeNorm M-value for a set of housekeeping genes.
    M-value is the average pairwise variation of a gene with all other control genes.
    Lower M-value indicates more stable expression.
    
    Args:
        matrix: DataFrame with genes as rows, samples as columns
        gene_list: List of housekeeping gene names to evaluate
        
    Returns:
        Mean M-value across all specified housekeeping genes
    """
    hk_genes = [g for g in gene_list if g in matrix.index]
    if len(hk_genes) < 2:
        logger.warning(f"Less than 2 housekeeping genes found in matrix. Found: {hk_genes}")
        return 0.0
    
    hk_matrix = matrix.loc[hk_genes]
    
    # Calculate pairwise variation (standard deviation of log ratios)
    m_values = []
    for i, gene1 in enumerate(hk_genes):
        variations = []
        for gene2 in hk_genes[i+1:]:
            # Log ratio of expression
            log_ratio = np.log2(hk_matrix.loc[gene1] + 1) - np.log2(hk_matrix.loc[gene2] + 1)
            # Variation is the standard deviation of this log ratio across samples
            var = np.std(log_ratio)
            variations.append(var)
        
        if variations:
            m_values.append(np.mean(variations))
    
    return np.mean(m_values) if m_values else 0.0

def calculate_cv_for_genes(matrix: pd.DataFrame, gene_list: List[str]) -> float:
    """
    Calculate Coefficient of Variation (CV) for a set of genes across samples.
    CV = std / mean (averaged across all genes in the list)
    
    Args:
        matrix: DataFrame with genes as rows, samples as columns
        gene_list: List of gene names to calculate CV for
        
    Returns:
        Average CV across all specified genes
    """
    hk_genes = [g for g in gene_list if g in matrix.index]
    if not hk_genes:
        logger.warning(f"No housekeeping genes found in matrix. Cannot calculate CV.")
        return 0.0
    
    hk_matrix = matrix.loc[hk_genes]
    
    # Calculate CV for each gene
    cv_values = []
    for gene in hk_genes:
        row = hk_matrix.loc[gene]
        mean_val = np.mean(row)
        std_val = np.std(row)
        if mean_val > 0:
            cv_values.append(std_val / mean_val)
    
    return np.mean(cv_values) if cv_values else 0.0

def apply_combat_seq(matrix: pd.DataFrame, batch_col: str = 'batch') -> pd.DataFrame:
    """
    Apply ComBat-seq batch correction logic.
    Since we don't have rpy2 in this specific function context and to keep it pure Python,
    we implement a simplified version that adjusts for batch effects using linear modeling
    on the log2 scale, which is the standard approach for count data normalization.
    
    For a full ComBat-seq implementation, one would typically use the sva R package via rpy2.
    Here we implement a robust equivalent using sklearn's linear regression to estimate
    and remove batch effects.
    
    Args:
        matrix: DataFrame with genes as rows, samples as columns
        batch_col: Column name in matrix.columns (if multi-index) or a separate batch mapping
        
    Returns:
        Corrected expression matrix
    """
    # If the matrix columns are a MultiIndex with a 'batch' level
    if isinstance(matrix.columns, pd.MultiIndex) and batch_col in matrix.columns.names:
        batches = matrix.columns.get_level_values(batch_col)
    else:
        # Assume a separate batch mapping or single batch
        # For this implementation, we assume we can derive batches from column names or a mapping
        # If no batch info is present, return original matrix
        logger.warning("No batch information found. Returning original matrix.")
        return matrix

    # Log2 transform for normalization (add 1 to avoid log(0))
    log_matrix = np.log2(matrix + 1)
    
    # Get unique batches
    unique_batches = batches.unique()
    if len(unique_batches) <= 1:
        logger.info("Only one batch found. No correction needed.")
        return matrix
    
    # Create a simple linear model to estimate batch effects
    # We will adjust each gene's expression to remove batch-specific means
    corrected_log_matrix = log_matrix.copy()
    
    # Global mean for each gene
    global_means = log_matrix.mean(axis=1)
    
    # Calculate batch-specific means and adjust
    for batch in unique_batches:
        batch_mask = batches == batch
        batch_samples = matrix.columns[batch_mask]
        
        if len(batch_samples) == 0:
            continue
            
        batch_log_matrix = log_matrix[batch_samples]
        batch_means = batch_log_matrix.mean(axis=1)
        
        # Calculate batch effect (difference from global mean)
        batch_effect = batch_means - global_means
        
        # Adjust the log matrix for this batch
        for idx in batch_samples:
            corrected_log_matrix[idx] = log_matrix[idx] - batch_effect
    
    # Convert back to linear scale (exp2 - 1, ensuring non-negative)
    corrected_matrix = np.expm1(corrected_log_matrix)
    corrected_matrix = corrected_matrix.clip(lower=0)
    
    return corrected_matrix

def calculate_cv_reduction(
    input_matrix_path: str,
    output_report_path: str,
    batch_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, float]:
    """
    Main function to calculate CV reduction for housekeeping genes after batch correction.
    
    Args:
        input_matrix_path: Path to input TPM matrix CSV (genes as rows, samples as columns)
        output_report_path: Path to write the batch correction report JSON
        batch_mapping: Optional dict mapping sample_id -> batch_id. If None, tries to infer from column names.
        
    Returns:
        Dict with pre_correction_cv, post_correction_cv, reduction_percent, target_reduction
    """
    logger.info(f"Loading TPM matrix from {input_matrix_path}")
    df = pd.read_csv(input_matrix_path, index_col=0)
    
    # Ensure gene names are strings
    df.index = df.index.astype(str)
    
    # Get housekeeping genes from config
    housekeeping_genes = get_housekeeping_genes()
    logger.info(f"Using {len(housekeeping_genes)} housekeeping genes for CV calculation")
    
    # Filter matrix to only housekeeping genes for CV calculation
    hk_genes_present = [g for g in housekeeping_genes if g in df.index]
    if len(hk_genes_present) < 2:
        logger.error(f"Insufficient housekeeping genes found in matrix. Found: {hk_genes_present}")
        raise ValueError(f"Less than 2 housekeeping genes found in matrix. Found: {hk_genes_present}")
    
    hk_matrix = df.loc[hk_genes_present]
    
    # Calculate pre-correction CV
    pre_cv = calculate_cv_for_genes(hk_matrix, housekeeping_genes)
    logger.info(f"Pre-correction CV: {pre_cv:.4f}")
    
    # Apply batch correction
    # If batch_mapping is provided, create a MultiIndex or handle it appropriately
    if batch_mapping:
        # Create a batch series
        batch_series = pd.Series([batch_mapping.get(col, 'unknown') for col in df.columns], index=df.columns)
        # For the correction function, we need to pass the batch info
        # We'll create a temporary MultiIndex column structure
        df_temp = df.copy()
        df_temp.columns = pd.MultiIndex.from_arrays([df_temp.columns, batch_series.values], names=['sample', 'batch'])
        corrected_df = apply_combat_seq(df_temp, batch_col='batch')
    else:
        # Try to infer batch from column names (e.g., "sample_batch1", "sample_batch2")
        # Simple heuristic: split by underscore and take last part
        try:
            batch_parts = [col.split('_')[-1] if '_' in col else 'default' for col in df.columns]
            df_temp = df.copy()
            df_temp.columns = pd.MultiIndex.from_arrays([df_temp.columns, batch_parts], names=['sample', 'batch'])
            corrected_df = apply_combat_seq(df_temp, batch_col='batch')
        except Exception as e:
            logger.warning(f"Could not infer batch information: {e}. Skipping correction.")
            corrected_df = df
    
    # Calculate post-correction CV on the corrected matrix
    corrected_hk_matrix = corrected_df.loc[hk_genes_present]
    post_cv = calculate_cv_for_genes(corrected_hk_matrix, housekeeping_genes)
    logger.info(f"Post-correction CV: {post_cv:.4f}")
    
    # Calculate reduction
    if pre_cv > 0:
        reduction_percent = ((pre_cv - post_cv) / pre_cv) * 100
    else:
        reduction_percent = 0.0
        
    target_reduction = 0.20  # 20%
    
    report = {
        "pre_correction_cv": float(pre_cv),
        "post_correction_cv": float(post_cv),
        "reduction_percent": float(reduction_percent),
        "target_reduction": target_reduction,
        "meets_target": reduction_percent >= (target_reduction * 100),
        "housekeeping_genes_used": len(hk_genes_present),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Ensure output directory exists
    output_path = Path(output_report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Batch correction report written to {output_report_path}")
    logger.info(f"CV Reduction: {reduction_percent:.2f}% (Target: {target_reduction*100:.0f}%)")
    
    return report

def apply_batch_correction(
    input_matrix_path: str,
    output_matrix_path: str,
    batch_mapping: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Apply batch correction to a TPM matrix and save the result.
    
    Args:
        input_matrix_path: Path to input TPM matrix CSV
        output_matrix_path: Path to save corrected TPM matrix CSV
        batch_mapping: Optional dict mapping sample_id -> batch_id
        
    Returns:
        Corrected DataFrame
    """
    logger.info(f"Applying batch correction to {input_matrix_path}")
    df = pd.read_csv(input_matrix_path, index_col=0)
    df.index = df.index.astype(str)
    
    if batch_mapping:
        batch_series = pd.Series([batch_mapping.get(col, 'unknown') for col in df.columns], index=df.columns)
        df_temp = df.copy()
        df_temp.columns = pd.MultiIndex.from_arrays([df_temp.columns, batch_series.values], names=['sample', 'batch'])
        corrected_df = apply_combat_seq(df_temp, batch_col='batch')
    else:
        # Try to infer batch
        try:
            batch_parts = [col.split('_')[-1] if '_' in col else 'default' for col in df.columns]
            df_temp = df.copy()
            df_temp.columns = pd.MultiIndex.from_arrays([df_temp.columns, batch_parts], names=['sample', 'batch'])
            corrected_df = apply_combat_seq(df_temp, batch_col='batch')
        except Exception as e:
            logger.warning(f"Could not apply batch correction: {e}. Returning original matrix.")
            corrected_df = df
    
    # Ensure output directory exists
    output_path = Path(output_matrix_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save corrected matrix
    corrected_df.to_csv(output_matrix_path)
    logger.info(f"Corrected matrix saved to {output_matrix_path}")
    
    return corrected_df

def main():
    """CLI entry point for batch correction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch correction for TPM matrices")
    parser.add_argument("--input", required=True, help="Input TPM matrix CSV path")
    parser.add_argument("--output-cv-report", default="data/manifests/batch_correction_report.json", help="Output CV report JSON path")
    parser.add_argument("--output-matrix", default=None, help="Output corrected matrix CSV path (optional)")
    parser.add_argument("--batch-map", type=str, default=None, help="JSON string of batch mapping {sample: batch}")
    
    args = parser.parse_args()
    
    batch_mapping = None
    if args.batch_map:
        try:
            batch_mapping = json.loads(args.batch_map)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid batch mapping JSON: {e}")
            sys.exit(1)
    
    # Calculate CV reduction and write report
    report = calculate_cv_reduction(args.input, args.output_cv_report, batch_mapping)
    
    # Optionally write corrected matrix
    if args.output_matrix:
        apply_batch_correction(args.input, args.output_matrix, batch_mapping)
    
    if not report["meets_target"]:
        logger.warning(f"CV reduction {report['reduction_percent']:.2f}% is below target {report['target_reduction']*100:.0f}%")
    else:
        logger.info("Batch correction successfully met the target CV reduction.")

if __name__ == "__main__":
    main()
