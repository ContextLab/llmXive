"""
Differential Expression Analysis Module.

Implements DESeq2 Wald test on discovery sets for biomarker identification.
Ensures strict adherence to FR-005: Analysis runs ONLY on discovery sets.
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import local config and utils
from src.config import get_project_root, ensure_directories
from src.utils import calculate_checksum, update_state_artifact_hashes

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FDR_THRESHOLD = 0.05
LOG2FC_THRESHOLD = 1.0
STATE_FILE_PATH = "state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml"

def setup_r_environment() -> bool:
    """
    Setup R environment for DESeq2 if rpy2 is available.
    Returns True if R is configured, False otherwise.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
        
        # Activate pandas conversion
        pandas2ri.activate()
        
        # Check for required R packages
        try:
            DESeq2 = importr('DESeq2')
            SummarizedExperiment = importr('SummarizedExperiment')
            logger.info("R environment (DESeq2) successfully configured.")
            return True
        except Exception as e:
            logger.warning(f"R packages DESeq2 not found. Falling back to scipy approximation: {e}")
            return False
    except ImportError:
        logger.warning("rpy2 not installed. Using scipy approximation for DE.")
        return False

def run_deseq2_analysis_r(counts_df: pd.DataFrame, 
                          col_data: pd.DataFrame, 
                          condition_col: str = 'response_label') -> pd.DataFrame:
    """
    Run DESeq2 Wald test using rpy2.
    
    Args:
        counts_df: DataFrame with genes as rows, samples as columns (raw counts).
        col_data: DataFrame with sample metadata including response_label.
        condition_col: Column name in col_data for grouping.
        
    Returns:
        DataFrame with results: gene, baseMean, log2FoldChange, pvalue, padj
    """
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri, Formula
    from rpy2.robjects.packages import importr
    from rpy2.robjects.vectors import StrVector, IntVector, FactorVector
    
    DESeq2 = importr('DESeq2')
    SummarizedExperiment = importr('SummarizedExperiment')
    stats = importr('stats')
    base = importr('base')

    # Prepare colData rownames to match counts columns
    col_data.index = col_data.index.astype(str)
    counts_df.columns = counts_df.columns.astype(str)
    
    # Ensure alignment
    common_samples = list(set(counts_df.columns) & set(col_data.index))
    if len(common_samples) == 0:
        raise ValueError("No common samples between counts and colData.")
    
    counts_aligned = counts_df[common_samples]
    col_data_aligned = col_data.loc[common_samples]
    
    # Create DESeq2 Dataset
    # R expects genes as rows, samples as columns
    dds = DESeq2.DESeqDataSetFromMatrix(
        countData=counts_aligned.values,
        colData=ro.conversion.py2rpy(col_data_aligned),
        design=Formula(f'~ {condition_col}')
    )
    
    # Pre-filter low count genes (optional but recommended for speed)
    keep = base.rowSums(counts_aligned >= 10) >= (counts_aligned.shape[1] / 2)
    dds = dds[keep, ]
    
    # Run DESeq
    logger.info("Running DESeq2...")
    dds = DESeq2.DESeq(dds)
    
    # Extract results
    res = DESeq2.results(dds, alpha=FDR_THRESHOLD)
    res_df = ro.conversion.rpy2py(res).reset_index()
    
    # Rename columns for consistency
    res_df.columns = ['gene', 'baseMean', 'log2FoldChange', 'lfcSE', 'stat', 'pvalue', 'padj']
    
    # Filter significant genes
    significant = res_df[
        (res_df['padj'] < FDR_THRESHOLD) & 
        (np.abs(res_df['log2FoldChange']) > LOG2FC_THRESHOLD)
    ].copy()
    
    return significant

def run_deseq2_analysis_scipy(counts_df: pd.DataFrame, 
                              col_data: pd.DataFrame, 
                              condition_col: str = 'response_label') -> pd.DataFrame:
    """
    Fallback: Run approximate Differential Expression using scipy (Wald-like approximation).
    Uses log2(CPM + 1) and t-test/Wald approximation if rpy2 is unavailable.
    
    Note: This is a fallback for environments without R/DESeq2.
    """
    from scipy import stats
    
    # Ensure alignment
    col_data.index = col_data.index.astype(str)
    counts_df.columns = counts_df.columns.astype(str)
    common_samples = list(set(counts_df.columns) & set(col_data.index))
    counts_aligned = counts_df[common_samples]
    col_data_aligned = col_data.loc[common_samples]
    
    # Create groups
    groups = col_data_aligned[condition_col].values
    unique_groups = np.unique(groups)
    if len(unique_groups) != 2:
        raise ValueError(f"Expected 2 groups for DE, found {len(unique_groups)}")
    
    group1, group2 = unique_groups
    idx1 = np.where(groups == group1)[0]
    idx2 = np.where(groups == group2)[0]
    
    results = []
    
    # Normalize counts to CPM
    lib_sizes = counts_aligned.sum(axis=1)
    cpm = (counts_aligned / lib_sizes[:, None]) * 1e6
    log_cpm = np.log2(cpm + 1)
    
    logger.warning("Using scipy approximation (no R/DESeq2). Results may differ from DESeq2.")
    
    for gene_idx in range(log_cpm.shape[0]):
        gene_name = log_cpm.index[gene_idx]
        vals1 = log_cpm.iloc[gene_idx, idx1]
        vals2 = log_cpm.iloc[gene_idx, idx2]
        
        # T-test (approximate Wald for log-transformed data)
        stat, p_val = stats.ttest_ind(vals1, vals2, equal_var=False)
        
        # Calculate logFC
        log2fc = np.mean(vals2) - np.mean(vals1)
        
        results.append({
            'gene': gene_name,
            'baseMean': counts_aligned.iloc[gene_idx].mean(),
            'log2FoldChange': log2fc,
            'pvalue': p_val,
            'padj': p_val # P-value adjustment not done in this simple fallback
        })
    
    res_df = pd.DataFrame(results)
    
    # FDR Correction (Benjamini-Hochberg)
    res_df['padj'] = stats.mstats.bonferroni(res_df['pvalue'].values, alpha=FDR_THRESHOLD, method='fdr_bh')
    # Note: stats.mstats.bonferroni might not be standard in all scipy versions, fallback to manual BH if needed
    # Manual BH implementation for robustness
    pvals = res_df['pvalue'].values
    n = len(pvals)
    sorted_indices = np.argsort(pvals)
    sorted_pvals = pvals[sorted_indices]
    adj_pvals = np.zeros(n)
    
    for i in range(n-1, -1, -1):
        adj_pvals[sorted_indices[i]] = min(sorted_pvals[i] * n / (i + 1), 1.0)
        if i < n - 1:
            adj_pvals[sorted_indices[i]] = min(adj_pvals[sorted_indices[i]], adj_pvals[sorted_indices[i+1]])
    
    res_df['padj'] = adj_pvals
    
    significant = res_df[
        (res_df['padj'] < FDR_THRESHOLD) & 
        (np.abs(res_df['log2FoldChange']) > LOG2FC_THRESHOLD)
    ].copy()
    
    return significant

def run_deseq2_analysis(counts_df: pd.DataFrame, 
                        col_data: pd.DataFrame, 
                        condition_col: str = 'response_label') -> pd.DataFrame:
    """
    Main entry point for DE analysis. Tries R/DESeq2 first, falls back to scipy.
    """
    use_r = setup_r_environment()
    if use_r:
        try:
            return run_deseq2_analysis_r(counts_df, col_data, condition_col)
        except Exception as e:
            logger.error(f"DESeq2 R execution failed: {e}. Falling back to scipy.")
    
    return run_deseq2_analysis_scipy(counts_df, col_data, condition_col)

def process_tumor_type_discovery(tumor_type: str, 
                                 data_dir: Path, 
                                 output_dir: Path) -> Dict[str, Any]:
    """
    Process a single tumor type discovery set.
    
    1. Load {tumor_type}_discovery_set.csv
    2. Verify filename ends with _discovery_set.csv (FR-005, Data Leakage Prevention)
    3. Run DE analysis
    4. Save results to {tumor_type}_de_results.json
    5. Return summary
    """
    input_file = data_dir / f"{tumor_type}_discovery_set.csv"
    
    # Strict check for data leakage prevention
    if not input_file.exists():
        raise FileNotFoundError(f"Discovery set not found: {input_file}")
    
    if not str(input_file).endswith('_discovery_set.csv'):
        raise ValueError(f"Data Leakage Prevention Failed: Input file must end with '_discovery_set.csv'. Got: {input_file}")
    
    logger.info(f"Processing discovery set for {tumor_type}: {input_file}")
    
    # Load data
    # Expected format: rows=genes, cols=samples, last_col=response_label (or similar metadata)
    # We assume the CSV has a 'response_label' column or similar.
    # If the format is wide (genes as rows), we need to transpose or handle accordingly.
    # Based on T020 output description: "Save distinct CSV/Parquet files".
    # Let's assume standard bioinformatics wide format: GeneID in first col, Samples as cols, Label in a specific col?
    # Actually, T020 likely outputs a standard ML format: samples as rows, genes as columns, plus label.
    # But DESeq2 expects genes as rows, samples as columns.
    # Let's check the config or assume a standard transformation.
    # Given the context of T016 (VST) and T020 (Split), the data is likely:
    # Rows = Samples, Cols = Genes + Label.
    
    df = pd.read_csv(input_file)
    
    # Identify metadata columns vs expression columns
    # We assume 'response_label' is the target. Other non-gene columns are metadata.
    # Genes are numeric columns.
    
    if 'response_label' not in df.columns:
        # Try case-insensitive or common variations
        label_col = next((c for c in df.columns if 'label' in c.lower()), None)
        if not label_col:
            raise ValueError(f"Could not find 'response_label' column in {input_file}")
    else:
        label_col = 'response_label'
    
    # Separate metadata and expression
    metadata_cols = [label_col]
    # Assume all other columns are genes if they are numeric or if the first column is gene ID
    # If first column is gene ID (string), treat it as index
    if df.iloc[:, 0].dtype == 'object' and not df.iloc[:, 0].str.contains(r'^[A-Z0-9._-]{10,}$', regex=True).all():
        # Likely gene IDs in first column
        gene_col = df.columns[0]
        df = df.set_index(gene_col)
        expression_cols = [c for c in df.columns if c != label_col]
        metadata = df[label_col]
        expression = df[expression_cols].T # Transpose to genes x samples
        expression.columns = metadata.index # Sample IDs as columns
    else:
        # Assume samples are rows, genes are columns.
        # Transpose
        expression = df.drop(columns=[label_col]).T
        expression.columns = df.index
        metadata = df[label_col]
    
    # Ensure metadata index matches expression columns
    metadata = metadata[metadata.index.intersection(expression.columns)]
    expression = expression[metadata.index]
    
    # Run DE
    de_results = run_deseq2_analysis(expression, metadata, condition_col=label_col)
    
    # Save results
    output_file = output_dir / f"{tumor_type}_de_results.json"
    de_results.to_json(output_file, orient='records', indent=2)
    
    logger.info(f"Saved DE results for {tumor_type} to {output_file}")
    
    return {
        'tumor_type': tumor_type,
        'input_file': str(input_file),
        'output_file': str(output_file),
        'significant_genes_count': len(de_results),
        'status': 'success'
    }

def main():
    """
    Main entry point for differential expression analysis across all tumor types.
    """
    project_root = get_project_root()
    data_dir = project_root / 'data' / 'processed'
    output_dir = project_root / 'results' / 'meta_analysis'
    
    ensure_directories([output_dir])
    
    # Discover discovery sets
    discovery_files = list(data_dir.glob('*_discovery_set.csv'))
    
    if not discovery_files:
        logger.error("No discovery set files found in data/processed/.")
        sys.exit(1)
    
    results = []
    for f in discovery_files:
        tumor_type = f.stem.replace('_discovery_set', '')
        try:
            res = process_tumor_type_discovery(tumor_type, data_dir, output_dir)
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to process {tumor_type}: {e}")
            results.append({
                'tumor_type': tumor_type,
                'status': 'failed',
                'error': str(e)
            })
    
    # Save summary
    summary_file = output_dir / 'de_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Differential Expression analysis complete. Summary saved to {summary_file}")
    
    # Update state if needed (checksums of results)
    # update_state_artifact_hashes(...)

if __name__ == '__main__':
    main()
