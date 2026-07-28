"""
Differential Expression Analysis Module.

Implements DESeq2 Wald test via rpy2 for identifying predictive biomarkers.
Operates strictly on discovery sets to prevent data leakage.
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import rpy2
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

import pandas as pd
import numpy as np

from src.config import get_project_root, ensure_directories
from src.utils import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Thresholds
FDR_THRESHOLD = 0.05
LOG2FC_THRESHOLD = 1.0

def setup_r_environment() -> None:
    """
    Initialize R environment and load required packages (DESeq2).
    Raises an error if packages are missing or R is unavailable.
    """
    # Activate pandas conversion
    pandas2ri.activate()

    try:
        # Load base and stats
        base = importr('base')
        stats = importr('stats')
    except ImportError as e:
        logger.error(f"Failed to import base R packages: {e}")
        raise

    # Check for DESeq2
    try:
        deseq2 = importr('DESeq2')
        logger.info("DESeq2 package loaded successfully.")
    except ImportError:
        logger.error("DESeq2 package not found in R. Please install it via BiocManager.")
        raise RuntimeError("DESeq2 package is required but not installed.")

    # Check for BiocGenerics (dependency)
    try:
        bioc_generics = importr('BiocGenerics')
    except ImportError:
        logger.error("BiocGenerics package not found.")
        raise RuntimeError("BiocGenerics package is required.")

    return deseq2

def _load_discovery_file(file_path: Path) -> pd.DataFrame:
    """
    Load a discovery set CSV and validate its structure.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        DataFrame with gene expression data.
        
    Raises:
        ValueError: If file is not a discovery set or missing columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Discovery file not found: {file_path}")
    
    # Strict check for discovery set naming
    if not str(file_path).endswith("_discovery_set.csv"):
        raise ValueError(
            f"Data Leakage Prevention: Input file '{file_path}' "
            f"does not end with '_discovery_set.csv'. "
            f"DE analysis must ONLY run on discovery sets."
        )

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV {file_path}: {e}")

    # Validate required columns
    required_cols = {'gene_symbol', 'response'}
    # Check if gene symbols are in columns or if rows are genes
    # Assuming standard format: rows=genes, columns=samples OR rows=samples, columns=genes+metadata
    # Based on T020 output description: "Save distinct CSV/Parquet files to data/processed/{tumor_type}_discovery_set.csv"
    # Typically for DE: Rows = Samples, Columns = Genes + Metadata (gene_symbol, response)
    
    if 'gene_symbol' not in df.columns:
        # Try to infer if it's the first column and unnamed
        if df.columns[0] == 'gene_symbol' or df.columns[0] == 'Gene':
            df = df.rename(columns={df.columns[0]: 'gene_symbol'})
        else:
            raise ValueError(f"Missing 'gene_symbol' column in {file_path}. Found: {df.columns.tolist()}")

    if 'response' not in df.columns:
        raise ValueError(f"Missing 'response' column in {file_path}. Found: {df.columns.tolist()}")

    return df

def _prepare_deseq2_input(df: pd.DataFrame) -> Tuple[Any, Any]:
    """
    Prepare count matrix and colData for DESeq2.
    
    Args:
        df: DataFrame with gene symbols as a column and samples as rows.
            
    Returns:
        Tuple of (count_matrix_r, coldata_r)
    """
    # Separate metadata and expression
    # Assume 'gene_symbol' and 'response' are metadata, rest are counts
    meta_cols = ['gene_symbol', 'response']
    expression_cols = [c for c in df.columns if c not in meta_cols]
    
    if len(expression_cols) == 0:
        raise ValueError("No expression columns found in discovery set.")

    # Pivot to standard DE format: Rows = Genes, Columns = Samples
    # Input: Rows=Samples, Cols=Genes
    # We need: Rows=Genes, Cols=Samples for DESeq2
    count_matrix = df.set_index('gene_symbol')[expression_cols].T
    count_matrix.columns.name = 'sample_id'
    
    # Ensure counts are integers (DESeq2 requirement)
    count_matrix = count_matrix.astype(int)
    
    # Create colData
    col_data = df[['response']].copy()
    col_data.index = count_matrix.columns
    
    # Convert response to factor (Response vs Non-Response)
    # Assuming binary: 1/0 or 'Responder'/'NonResponder'
    # DESeq2 expects factors
    if not pd.api.types.is_numeric_dtype(col_data['response']):
        col_data['response'] = col_data['response'].astype('category')
    else:
        # If numeric, treat as factor levels
        col_data['response'] = col_data['response'].astype('category')

    return count_matrix, col_data

def run_deseq2_analysis(
    tumor_type: str,
    discovery_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Run DESeq2 Wald test on a single tumor type's discovery set.
    
    Args:
        tumor_type: Name of the tumor type.
        discovery_path: Path to the _discovery_set.csv file.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing analysis results and metadata.
    """
    logger.info(f"Starting DESeq2 analysis for {tumor_type}...")
    
    # Load data
    df = _load_discovery_file(discovery_path)
    logger.info(f"Loaded {len(df)} samples for {tumor_type}.")

    # Prepare R objects
    count_matrix, col_data = _prepare_deseq2_input(df)
    
    # Filter low count genes (basic pre-filtering for DESeq2 stability)
    # Keep genes with at least 10 counts in at least 2 samples
    row_sums = count_matrix.sum(axis=1)
    count_matrix = count_matrix[row_sums > 10]
    if count_matrix.empty:
        raise ValueError(f"No genes passed pre-filtering for {tumor_type}.")
    
    # Update col_data to match
    col_data = col_data.loc[count_matrix.columns]

    # Run DESeq2
    try:
        with localconverter(ro.default_converter + pandas2ri.converter):
          # Convert to R DataFrame
          r_count_matrix = ro.conversion.py2rpy(count_matrix)
          r_col_data = ro.conversion.py2rpy(col_data)
          
          # Create DESeqDataSet
          # dds <- DESeqDataSetFromMatrix(countData = count_matrix, colData = col_data, design = ~ response)
          dds = ro.r('DESeqDataSetFromMatrix')(
              countData = r_count_matrix,
              colData = r_col_data,
              design = ro.StrVector(['~', 'response'])
          )
          
          # Run DESeq
          # dds <- DESeq(dds)
          dds = ro.r('DESeq')(dds)
          
          # Get results
          # res <- results(dds, alpha = FDR_THRESHOLD)
          res = ro.r('results')(dds, alpha=FDR_THRESHOLD)
          
          # Convert back to pandas
          res_df = ro.conversion.rpy2py(res)
          
    except RRuntimeError as e:
        logger.error(f"R error during DESeq2 execution for {tumor_type}: {e}")
        raise RuntimeError(f"DESeq2 failed for {tumor_type}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during DESeq2 execution for {tumor_type}: {e}")
        raise

    # Process results
    # res_df typically has: baseMean, log2FoldChange, lfcSE, stat, pvalue, padj
    # Filter by FDR and log2FC
    if 'padj' not in res_df.columns:
        raise ValueError("DESeq2 results missing 'padj' column.")
    if 'log2FoldChange' not in res_df.columns:
        raise ValueError("DESeq2 results missing 'log2FoldChange' column.")

    significant_genes = res_df[
        (res_df['padj'] < FDR_THRESHOLD) & 
        (abs(res_df['log2FoldChange']) > LOG2FC_THRESHOLD)
    ]
    
    # Reset index to get gene names as a column if they were the index
    if significant_genes.index.name == 'gene':
        significant_genes = significant_genes.reset_index()
        significant_genes = significant_genes.rename(columns={'gene': 'gene_symbol'})
    elif 'gene_symbol' not in significant_genes.columns:
        # Assume index is gene symbol
        significant_genes = significant_genes.reset_index()
        significant_genes = significant_genes.rename(columns={'index': 'gene_symbol'})

    # Save results
    output_file = output_dir / f"{tumor_type}_deseq2_results.csv"
    significant_genes.to_csv(output_file, index=False)
    
    logger.info(f"Saved {len(significant_genes)} significant genes to {output_file}")

    return {
        "tumor_type": tumor_type,
        "total_samples": len(df),
        "genes_tested": len(count_matrix),
        "significant_genes_count": len(significant_genes),
        "fdr_threshold": FDR_THRESHOLD,
        "log2fc_threshold": LOG2FC_THRESHOLD,
        "output_file": str(output_file)
    }

def process_tumor_type_discovery(
    tumor_type: str,
    processed_dir: Path,
    results_dir: Path
) -> Dict[str, Any]:
    """
    Wrapper to process a single tumor type discovery set.
    
    Args:
        tumor_type: Name of the tumor type.
        processed_dir: Directory containing processed discovery sets.
        results_dir: Directory to save DE results.
        
    Returns:
        Result dictionary from run_deseq2_analysis.
    """
    discovery_file = processed_dir / f"{tumor_type}_discovery_set.csv"
    
    if not discovery_file.exists():
        logger.warning(f"Discovery file not found for {tumor_type}: {discovery_file}")
        return {
            "tumor_type": tumor_type,
            "status": "skipped",
            "reason": "discovery_file_not_found"
        }

    return run_deseq2_analysis(tumor_type, discovery_file, results_dir)

def main():
    """
    Main entry point for differential expression analysis.
    Iterates over all available discovery sets in data/processed/.
    """
    setup_logging()
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "results" / "meta_analysis"
    ensure_directories([results_dir])

    logger.info("Initializing Differential Expression Analysis...")
    
    # Setup R
    try:
        setup_r_environment()
    except Exception as e:
        logger.critical(f"R environment setup failed: {e}")
        sys.exit(1)

    # Identify available discovery sets
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    if not discovery_files:
        logger.warning("No discovery set files found in data/processed/.")
        sys.exit(0)

    tumor_types = [f.stem.replace("_discovery_set", "") for f in discovery_files]
    logger.info(f"Found {len(tumor_types)} tumor types to process: {tumor_types}")

    results = []
    for tumor_type in tumor_types:
        try:
            result = process_tumor_type_discovery(tumor_type, processed_dir, results_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {tumor_type}: {e}")
            results.append({
                "tumor_type": tumor_type,
                "status": "failed",
                "error": str(e)
            })

    # Save summary
    summary_file = results_dir / "de_analysis_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"DE analysis complete. Summary saved to {summary_file}")

if __name__ == "__main__":
    main()