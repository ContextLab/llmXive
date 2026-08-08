import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, Formula
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.callbacks import logger as r_logger

# Configure R logging to not spam stdout during imports
r_logger.setLevel(logging.ERROR)

# Activate pandas conversion for rpy2
pandas2ri.activate()

# Import R packages
try:
    dds_pkg = importr('DESeq2')
    dds_pkg_version = dds_pkg.__version__
    logging.info(f"DESeq2 version {dds_pkg_version} loaded successfully.")
except ImportError:
    logging.error("DESeq2 R package is not installed. Please install it via BiocManager.")
    sys.exit(1)

from src.config import get_project_root
from src.utils import setup_logging, calculate_checksum

logger = logging.getLogger(__name__)

def setup_r_environment():
    """
    Setup R environment for DESeq2 analysis.
    Returns the loaded packages.
    """
    # Ensure pandas2ri is active
    pandas2ri.activate()
    logger.info("R environment configured for DESeq2.")
    return dds_pkg

def run_deseq2_analysis_r(counts_df: pd.DataFrame, 
                          metadata_df: pd.DataFrame, 
                          design_formula: str = "~ response_label") -> pd.DataFrame:
    """
    Run DESeq2 Wald test using rpy2.
    
    Args:
        counts_df: DataFrame with genes as rows, samples as columns.
        metadata_df: DataFrame with sample metadata (index must match columns of counts_df).
        design_formula: R formula string (default: ~ response_label).
        
    Returns:
        DataFrame with DE results (gene, log2FoldChange, pvalue, padj).
    """
    logger.info("Starting DESeq2 analysis via rpy2...")
    
    # Ensure metadata index matches counts columns
    if not all(metadata_df.index == counts_df.columns):
        # Reorder metadata to match counts columns
        metadata_df = metadata_df.reindex(counts_df.columns)
        
    # Create R objects
    r_counts = pandas2ri.py2rpy(counts_df)
    r_metadata = pandas2ri.py2rpy(metadata_df)
    
    # Create DESeqDataSet
    # We need to construct the call: DESeqDataSetFromMatrix(countData, colData, design)
    try:
        dds = dds_pkg.DESeqDataSetFromMatrix(
            countData=r_counts,
            colData=r_metadata,
            design=Formula(design_formula)
        )
    except Exception as e:
        logger.error(f"Failed to create DESeqDataSet: {e}")
        raise

    # Run DESeq
    try:
        dds = dds_pkg.DESeq(dds)
    except Exception as e:
        logger.error(f"DESeq2 analysis failed: {e}")
        raise

    # Get results
    try:
        res = dds_pkg.results(dds)
    except Exception as e:
        logger.error(f"Failed to extract results: {e}")
        raise

    # Convert back to pandas
    res_df = pandas2ri.rpy2py(res)
    
    # Reset index to have gene as a column
    res_df = res_df.reset_index()
    # Rename 'index' column to 'gene' if it exists
    if 'index' in res_df.columns:
        res_df.rename(columns={'index': 'gene'}, inplace=True)
        
    logger.info(f"DESeq2 analysis complete. {len(res_df)} genes processed.")
    return res_df

def run_deseq2_analysis_scipy(counts_df: pd.DataFrame, 
                              metadata_df: pd.DataFrame, 
                              response_col: str = "response_label") -> pd.DataFrame:
    """
    Fallback: Run simple t-test based differential expression if DESeq2 fails.
    Note: This is a simplified approximation and not the primary method.
    """
    logger.warning("Using scipy fallback for differential expression (DESeq2 unavailable or failed).")
    
    results = []
    genes = counts_df.index
    samples = counts_df.columns
    
    # Ensure metadata aligns
    if not all(metadata_df.index == samples):
        metadata_df = metadata_df.reindex(samples)
        
    groups = metadata_df[response_col].unique()
    if len(groups) != 2:
        raise ValueError(f"Scipy fallback requires exactly 2 response groups, found {len(groups)}")
    
    group_a = groups[0]
    group_b = groups[1]
    
    mask_a = metadata_df[response_col] == group_a
    mask_b = metadata_df[response_col] == group_b
    
    for gene in genes:
        vals_a = counts_df.loc[gene, mask_a].values
        vals_b = counts_df.loc[gene, mask_b].values
        
        # Filter out NaNs if any
        vals_a = vals_a[~np.isnan(vals_a)]
        vals_b = vals_b[~np.isnan(vals_b)]
        
        if len(vals_a) < 2 or len(vals_b) < 2:
            pval = np.nan
            log2fc = np.nan
        else:
            # Use Welch's t-test
            stat, pval = stats.ttest_ind(vals_a, vals_b, equal_var=False)
            # Calculate log2FC
            mean_a = np.mean(vals_a)
            mean_b = np.mean(vals_b)
            # Add small epsilon to avoid log(0)
            log2fc = np.log2((mean_b + 1e-6) / (mean_a + 1e-6))
        
        results.append({
            'gene': gene,
            'log2FoldChange': log2fc,
            'pvalue': pval,
            'padj': np.nan # Cannot calculate FDR without full distribution in this simple fallback
        })
        
    return pd.DataFrame(results)

def run_deseq2_analysis(counts_df: pd.DataFrame, 
                        metadata_df: pd.DataFrame, 
                        use_r: bool = True) -> pd.DataFrame:
    """
    Wrapper to run DE analysis. Prefers DESeq2 via rpy2, falls back to scipy if needed.
    """
    if use_r:
        try:
            return run_deseq2_analysis_r(counts_df, metadata_df)
        except Exception as e:
            logger.warning(f"DESeq2 (rpy2) failed: {e}. Attempting scipy fallback.")
            return run_deseq2_analysis_scipy(counts_df, metadata_df)
    else:
        return run_deseq2_analysis_scipy(counts_df, metadata_df)

def process_tumor_type_discovery(tumor_type: str, 
                                 input_dir: Path, 
                                 output_dir: Path, 
                                 fdr_threshold: float = 0.05, 
                                 log2fc_threshold: float = 1.0) -> Optional[Dict[str, Any]]:
    """
    Process a single tumor type discovery set.
    
    1. Load discovery set CSV.
    2. Verify filename ends with '_discovery_set.csv'.
    3. Run DESeq2 Wald test.
    4. Filter significant genes (FDR < 0.05, |log2FC| > 1.0).
    5. Save results to CSV.
    
    Args:
        tumor_type: Name of the tumor type (used to construct filenames).
        input_dir: Directory containing the discovery set CSV.
        output_dir: Directory to save the DE results CSV.
        fdr_threshold: Maximum adjusted p-value (FDR).
        log2fc_threshold: Minimum absolute log2 fold change.
        
    Returns:
        Dictionary with summary stats or None if no significant genes.
    """
    input_file = input_dir / f"{tumor_type}_discovery_set.csv"
    output_file = output_dir / f"{tumor_type}_de_results.csv"
    
    if not input_file.exists():
        logger.error(f"Discovery set file not found: {input_file}")
        return None
        
    # Data Leakage Prevention: Verify filename
    if not input_file.name.endswith('_discovery_set.csv'):
        logger.error(f"Data leakage risk: Input file {input_file.name} does not end with '_discovery_set.csv'. Aborting.")
        raise ValueError(f"Invalid input file for discovery analysis: {input_file.name}")
        
    logger.info(f"Processing discovery set for {tumor_type} from {input_file}")
    
    # Load data
    # Expected format: Rows=Genes, Cols=Samples, plus 'response_label' column if metadata is embedded
    # Or separate metadata. Assuming standard format from T020: 
    # Columns: sample_id, response_label, then gene expression columns.
    # If the output of T020 is just the expression matrix + metadata columns, we parse accordingly.
    
    df = pd.read_csv(input_file)
    
    # Identify metadata columns vs expression columns
    # Assuming 'sample_id' and 'response_label' are metadata
    metadata_cols = ['sample_id', 'response_label']
    # Check if they exist
    if not all(col in df.columns for col in metadata_cols):
        # Try to infer: maybe sample_id is the index?
        if 'sample_id' not in df.columns and df.index.name == 'sample_id':
            df = df.reset_index()
        else:
            logger.error(f"Missing required metadata columns {metadata_cols} in {input_file}")
            return None
            
    metadata_df = df[metadata_cols].set_index('sample_id')
    
    # Expression columns are everything else
    expr_cols = [c for c in df.columns if c not in metadata_cols]
    counts_df = df.set_index('sample_id')[expr_cols].T # Transpose to Genes x Samples
    # Ensure index is gene symbols
    counts_df.index.name = 'gene'
    
    logger.info(f"Loaded {len(counts_df)} genes and {len(metadata_df)} samples.")
    
    # Run DE
    try:
        de_results = run_deseq2_analysis(counts_df, metadata_df)
    except Exception as e:
        logger.error(f"DE analysis failed for {tumor_type}: {e}")
        return None
        
    # Filter results
    # Ensure padj is numeric
    de_results['padj'] = pd.to_numeric(de_results['padj'], errors='coerce')
    
    # Filter significant
    significant = de_results[
        (de_results['padj'] < fdr_threshold) & 
        (de_results['padj'].notna()) &
        (abs(de_results['log2FoldChange']) > log2fc_threshold)
    ].copy()
    
    # Sort by padj
    significant = significant.sort_values('padj')
    
    # Save full results
    de_results.to_csv(output_file, index=False)
    logger.info(f"Saved full DE results to {output_file}")
    
    # Save significant genes summary
    sig_summary = {
        'tumor_type': tumor_type,
        'total_genes_tested': len(de_results),
        'significant_genes_count': len(significant),
        'fdr_threshold': fdr_threshold,
        'log2fc_threshold': log2fc_threshold,
        'significant_genes': significant['gene'].tolist()
    }
    
    logger.info(f"Found {len(significant)} significant genes for {tumor_type}")
    return sig_summary

def main():
    """
    Main entry point for differential expression analysis.
    Iterates over all discovery sets in data/processed/ and runs DE.
    """
    setup_logging()
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_dir = processed_dir # Save results in same directory
    
    if not processed_dir.exists():
        logger.error("Processed data directory not found. Run T020 first.")
        sys.exit(1)
        
    # Find all discovery set files
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    if not discovery_files:
        logger.warning("No discovery set files found. Skipping DE analysis.")
        return
        
    logger.info(f"Found {len(discovery_files)} discovery sets.")
    
    all_results = []
    
    for f in discovery_files:
        # Extract tumor type from filename
        # Expected: {tumor_type}_discovery_set.csv
        tumor_type = f.stem.replace("_discovery_set", "")
        
        try:
            result = process_tumor_type_discovery(
                tumor_type=tumor_type,
                input_dir=processed_dir,
                output_dir=output_dir
            )
            if result:
                all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {tumor_type}: {e}")
            
    # Optional: Save a summary of all results
    summary_file = output_dir / "de_analysis_summary.json"
    with open(summary_file, 'w') as fh:
        json.dump(all_results, fh, indent=2)
        
    logger.info(f"DE analysis complete. Summary saved to {summary_file}")

if __name__ == "__main__":
    main()
