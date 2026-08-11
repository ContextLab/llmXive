import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# R integration for DESeq2
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, StrVector, FloatVector, IntVector
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

# Project utilities
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, watchdog, TimeoutError

# Configure logging
logger = logging.getLogger(__name__)

# R Package Wrappers (Lazy load)
def _get_r_packages():
    """Lazy import of R packages to avoid startup overhead if not needed."""
    try:
        dds = importr('DESeq2')
        sva = importr('sva')
        base = importr('base')
        stats = importr('stats')
        return dds, sva, base, stats
    except ImportError as e:
        logger.error(f"Failed to load required R packages: {e}")
        raise

def setup_r_environment():
    """
    Initializes the R environment and pre-loads necessary libraries.
    Raises RuntimeError if R or required packages (DESeq2, sva) are missing.
    """
    try:
        # Check if R is available
        if not ro.r['exists']("DESeq2"):
            # Force import to trigger error if missing
            importr('DESeq2')
    except (RRuntimeError, ImportError) as e:
        raise RuntimeError(
            f"R environment not properly configured or DESeq2 missing: {e}. "
            "Ensure rpy2, DESeq2, and sva are installed in the R environment."
        )
    logger.info("R environment ready.")

def load_discovery_set(tumor_type: str, project_root: Path) -> pd.DataFrame:
    """
    Loads the discovery set for a specific tumor type.
    
    Args:
        tumor_type: The exact string identifier for the tumor type.
        project_root: Path to the project root directory.
        
    Returns:
        DataFrame with columns: sample_id, tumor_type, response_label, expression_vector (or gene columns).
        
    Raises:
        FileNotFoundError: If the discovery set file is missing.
        ValueError: If required columns are missing.
    """
    file_path = project_root / "data" / "processed" / f"{tumor_type}_discovery_set.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Discovery set file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    required_cols = ['sample_id', 'tumor_type', 'response_label']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        
    # Expression data is expected to be in remaining columns (gene symbols)
    # We assume the DataFrame is already normalized (VST) and batch-corrected
    # based on the pipeline flow (T016 -> T020 -> T023b).
    
    logger.info(f"Loaded discovery set for {tumor_type}: {len(df)} samples, {len(df.columns) - 3} features.")
    return df

def run_deseq2_analysis_loo(
    tumor_type: str, 
    project_root: Path, 
    all_discovery_dfs: Dict[str, pd.DataFrame],
    timeout_seconds: int = 3600
) -> Optional[pd.DataFrame]:
    """
    Runs DESeq2 Wald test on the N-1 tumor types (excluding the held-out tumor_type).
    
    Logic:
    1. Construct N-1 dataset by excluding the held-out tumor_type.
    2. Run DESeq2 Wald test (FDR < 0.05, |log2FC| > 1.0).
    3. Return significant genes.
    
    Args:
        tumor_type: The tumor type to hold out.
        project_root: Path to project root.
        all_discovery_dfs: Dictionary mapping tumor_type -> DataFrame.
        timeout_seconds: Timeout for the R process.
        
    Returns:
        DataFrame of significant genes with columns: gene, log2FoldChange, pvalue, padj.
        Returns None if no data available or process fails.
    """
    # 1. Subset N-1 types
    n_minus_1_dfs = {k: v for k, v in all_discovery_dfs.items() if k != tumor_type}
    
    if not n_minus_1_dfs:
        logger.warning(f"No other tumor types found to compare against {tumor_type}. Skipping.")
        return None
    
    # Combine data
    combined_df = pd.concat(n_minus_1_dfs.values(), ignore_index=True)
    
    # Identify response column (0/1 or similar)
    # We assume 'response_label' is numeric or binary string. Convert to numeric if needed.
    if combined_df['response_label'].dtype == object:
        combined_df['response_label'] = combined_df['response_label'].map({'Responder': 1, 'NonResponder': 0, 'CR': 1, 'PR': 1, 'SD': 0, 'PD': 0}).fillna(0).astype(int)
    
    # Separate counts (expression) and metadata
    # Assuming gene columns are everything except sample_id, tumor_type, response_label
    meta_cols = ['sample_id', 'tumor_type', 'response_label']
    gene_cols = [c for c in combined_df.columns if c not in meta_cols]
    
    if len(gene_cols) == 0:
        logger.error(f"No gene expression columns found in combined data for {tumor_type}.")
        return None
        
    counts_matrix = combined_df[gene_cols].astype(float).T  # DESeq2 expects genes x samples
    col_data = combined_df.set_index('sample_id')[['response_label']].T  # Metadata x samples
    
    # Ensure column order matches
    if not counts_matrix.columns.equals(col_data.columns):
        # Reorder col_data to match counts_matrix columns
        col_data = col_data[counts_matrix.columns]
    
    # Setup R environment
    try:
        dds_pkg, sva_pkg, base_pkg, stats_pkg = _get_r_packages()
    except RuntimeError as e:
        logger.error(f"R setup failed: {e}")
        return None

    # Convert to R objects
    with pandas2ri.active():
        r_counts = pandas2ri.py2rpy(counts_matrix)
        r_coldata = pandas2ri.py2rpy(col_data)
    
    # Create DESeqDataSet
    # Formula: ~ response_label
    r_coldata['response_label'] = StrVector(col_data['response_label'].astype(str))
    
    # R code construction
    r_code = f"""
    library(DESeq2)
    library(sva)
    
    # Create DESeqDataSet
    counts <- {r_counts}
    coldata <- {r_coldata}
    
    # Ensure rownames of coldata match colnames of counts
    rownames(coldata) <- colnames(counts)
    
    dds <- DESeqDataSetFromMatrix(countData = counts,
                                  colData = coldata,
                                  design = ~ response_label)
    
    # Run DESeq
    dds <- DESeq(dds)
    
    # Extract results (Wald test)
    res <- results(dds, alpha=0.05)
    
    # Add gene names as a column
    res_df <- as.data.frame(res)
    res_df$gene <- rownames(res_df)
    
    # Filter: padj < 0.05 AND |log2FoldChange| > 1.0
    sig <- res_df[!is.na(res_df$padj) & res_df$padj < 0.05 & abs(res_df$log2FoldChange) > 1.0, ]
    
    # Return as list for conversion back
    list(
      genes = sig$gene,
      log2FC = sig$log2FoldChange,
      pval = sig$pvalue,
      padj = sig$padj
    )
    """
    
    try:
        # Execute with watchdog
        result = watchdog(r_code, timeout=timeout_seconds, logger=logger)
    except TimeoutError:
        logger.critical(f"DESeq2 analysis for {tumor_type} timed out after {timeout_seconds}s. Halting.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"R process failed for {tumor_type}: {e}")
        return None
    
    # Convert result back to DataFrame
    # result is a list of R vectors
    df_res = pd.DataFrame({
        'gene': result[0],
        'log2FoldChange': result[1],
        'pvalue': result[2],
        'padj': result[3]
    })
    
    logger.info(f"DESeq2 analysis for {tumor_type} (N-1={len(n_minus_1_dfs)} types) found {len(df_res)} significant genes.")
    return df_res

def process_tumor_type_loo(tumor_type: str, project_root: Path, all_discovery_dfs: Dict[str, pd.DataFrame]) -> str:
    """
    Wrapper to process a single tumor type LOO iteration and save results.
    
    Returns:
        Path to the saved CSV file.
    """
    output_file = project_root / "data" / "processed" / f"loo_iteration_{tumor_type}_de_results.csv"
    
    try:
        df_res = run_deseq2_analysis_loo(tumor_type, project_root, all_discovery_dfs)
        
        if df_res is not None and not df_res.empty:
            df_res.to_csv(output_file, index=False)
            logger.info(f"Saved LOO results for {tumor_type} to {output_file}")
            return str(output_file)
        else:
            logger.warning(f"No significant genes found for {tumor_type}. Creating empty file.")
            # Create empty file with headers to maintain consistency
            pd.DataFrame(columns=['gene', 'log2FoldChange', 'pvalue', 'padj']).to_csv(output_file, index=False)
            return str(output_file)
            
    except FileNotFoundError as e:
        logger.critical(f"Critical error processing {tumor_type}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to process {tumor_type}: {e}")
        # Decide: halt or skip? Task says "log critical error and skip this iteration"
        # But if the file is missing, it's a data integrity issue.
        # We log and return empty path to indicate failure for this iteration.
        return ""

def run_deseq2_analysis(project_root: Path) -> Dict[str, str]:
    """
    Main orchestrator for LOO-Blind DE Analysis.
    Iterates over all tumor types found in data/processed.
    
    Returns:
        Dictionary mapping tumor_type -> output_file_path.
    """
    ensure_directories(project_root)
    
    # Discover available tumor types from discovery sets
    processed_dir = project_root / "data" / "processed"
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    tumor_types = []
    for f in discovery_files:
        # Extract type from filename: {type}_discovery_set.csv
        name = f.stem
        if name.endswith("_discovery_set"):
            t_type = name.replace("_discovery_set", "")
            tumor_types.append(t_type)
    
    if len(tumor_types) < 2:
        logger.error(f"Insufficient tumor types ({len(tumor_types)}) for LOO analysis. Need at least 2.")
        return {}
    
    logger.info(f"Found {len(tumor_types)} tumor types for LOO analysis: {tumor_types}")
    
    # Load all discovery sets into memory (assuming fit in RAM as per constraints)
    all_discovery_dfs = {}
    for t_type in tumor_types:
        try:
            all_discovery_dfs[t_type] = load_discovery_set(t_type, project_root)
        except Exception as e:
            logger.error(f"Failed to load discovery set for {t_type}: {e}. Skipping type.")
    
    results = {}
    for t_type in tumor_types:
        logger.info(f"Starting LOO analysis for held-out type: {t_type}")
        try:
            out_path = process_tumor_type_loo(t_type, project_root, all_discovery_dfs)
            if out_path:
                results[t_type] = out_path
        except FileNotFoundError:
            logger.critical(f"Skipping {t_type} due to missing data.")
            continue
        except Exception as e:
            logger.error(f"Error in LOO iteration for {t_type}: {e}")
            continue
    
    return results

def main():
    """Entry point for the differential expression script."""
    setup_logging()
    project_root = get_project_root()
    
    logger.info("Starting LOO-Blind Differential Expression Analysis (T023b).")
    
    try:
        setup_r_environment()
    except RuntimeError as e:
        logger.critical(f"R Environment setup failed: {e}")
        sys.exit(1)
    
    results = run_deseq2_analysis(project_root)
    
    if not results:
        logger.error("No LOO analysis results generated.")
        sys.exit(1)
    
    logger.info(f"Successfully processed {len(results)} tumor types.")
    logger.info("LOO-Blind DE Analysis complete.")

if __name__ == "__main__":
    main()
