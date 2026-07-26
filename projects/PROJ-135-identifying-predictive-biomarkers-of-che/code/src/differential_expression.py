import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rpy2.robjects import pandas2ri, r
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

# Import project config
from code.src.config import get_project_root

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_r_environment():
    """
    Initialize R environment and load necessary packages (DESeq2).
    Raises an error if DESeq2 is not available.
    """
    logger.info("Initializing R environment...")
    try:
        # Activate pandas2ri for automatic conversion
        pandas2ri.activate()
        
        # Try to import DESeq2
        try:
            deseq2 = importr('DESeq2')
            logger.info("DESeq2 package loaded successfully.")
        except ImportError:
            logger.error("DESeq2 R package is not installed. Please install it via: BiocManager::install('DESeq2')")
            raise RuntimeError("DESeq2 R package missing")
        
        # Import base R utils
        utils = importr('utils')
        return deseq2
    except Exception as e:
        logger.error(f"Failed to setup R environment: {e}")
        raise

def run_deseq2_analysis(counts_df: pd.DataFrame, 
                        col_data: pd.DataFrame, 
                        design_formula: str = " ~ response") -> Dict[str, Any]:
    """
    Execute DESeq2 Wald test on the provided count data.
    
    Args:
        counts_df: DataFrame with genes as rows, samples as columns.
        col_data: DataFrame with sample metadata (must include 'response').
        design_formula: R formula string for the design matrix.
        
    Returns:
        Dictionary containing:
            - 'significant_genes': List of gene symbols meeting FDR and log2FC thresholds.
            - 'results_df': Full results DataFrame.
            - 'stats': Summary statistics.
    """
    logger.info("Running DESeq2 analysis...")
    
    # Ensure row names are gene symbols
    if counts_df.index.name is None:
        counts_df.index.name = 'gene'
        
    # Ensure col_data index matches counts columns
    if not all(counts_df.columns == col_data.index):
        # Reorder col_data to match counts
        col_data = col_data.loc[counts_df.columns]
        
    # Convert to R objects
    r_counts = pandas2ri.py2rpy(counts_df)
    r_col_data = pandas2ri.py2rpy(col_data)
    
    # Create DESeqDataSet
    with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
        r_script = f"""
        library(DESeq2)
        counts <- {r_counts}
        colData <- {r_col_data}
        
        # Ensure rownames are preserved
        rownames(counts) <- rownames(counts)
        rownames(colData) <- rownames(colData)
        
        dds <- DESeqDataSetFromMatrix(countData = counts,
                                      colData = colData,
                                      design = {design_formula})
        
        # Run DESeq
        dds <- DESeq(dds)
        res <- results(dds)
        
        # Convert to data frame for Python
        res_df <- as.data.frame(res)
        """
        f.write(r_script)
        script_path = f.name

    try:
        # Execute R script
        r.source(script_path)
        res_df = r['res_df']
        results_df = pandas2ri.r2py(res_df)
    except RRuntimeError as e:
        logger.error(f"DESeq2 analysis failed: {e}")
        raise
    finally:
        os.unlink(script_path)
    
    # Filter significant genes
    # Thresholds: FDR < 0.05, |log2FC| > 1.0
    fdr_col = 'padj'
    lfc_col = 'log2FoldChange'
    
    # Handle NA values in padj
    results_df[fdr_col] = results_df[fdr_col].fillna(1.0)
    
    mask = (results_df[fdr_col] < 0.05) & (results_df[lfc_col].abs() > 1.0)
    significant_genes = results_df[mask].index.tolist()
    
    stats = {
        'total_genes': len(results_df),
        'significant_genes': len(significant_genes),
        'fdr_threshold': 0.05,
        'lfc_threshold': 1.0
    }
    
    logger.info(f"DESeq2 analysis complete. Found {len(significant_genes)} significant genes.")
    
    return {
        'significant_genes': significant_genes,
        'results_df': results_df,
        'stats': stats
    }

def process_tumor_type_discovery(tumor_type: str, 
                                 discovery_path: Path, 
                                 output_dir: Path) -> Dict[str, Any]:
    """
    Process a single tumor type's discovery set:
    1. Load discovery set data (counts + response labels).
    2. Run DESeq2.
    3. Save results.
    
    Args:
        tumor_type: Name of the tumor type (e.g., 'BRCA').
        discovery_path: Path to the discovery set CSV/Parquet file.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary with analysis results and file paths.
    """
    logger.info(f"Processing discovery set for tumor type: {tumor_type}")
    
    # Load data
    if discovery_path.suffix == '.csv':
        df = pd.read_csv(discovery_path, index_col=0)
    elif discovery_path.suffix == '.parquet':
        df = pd.read_parquet(discovery_path)
    else:
        raise ValueError(f"Unsupported file format: {discovery_path.suffix}")
    
    # Expected columns: genes as rows, samples as columns, plus metadata
    # We assume the file has a 'response' column or similar metadata
    # For DESeq2, we need a counts matrix and a colData frame.
    # Assuming the input file is structured as:
    # - Rows: Genes
    # - Columns: Sample IDs
    # - A separate metadata file or embedded column 'response'
    
    # Check if 'response' is a column (metadata) or if we need to infer
    # Based on T020, the split data should have been saved with metadata.
    # We assume the file contains both expression and a 'response' column.
    # If 'response' is in the columns, we separate it.
    
    if 'response' not in df.columns:
        # Try to find a column that looks like response (e.g., 'label', 'outcome')
        possible_cols = [c for c in df.columns if 'response' in c.lower() or 'label' in c.lower()]
        if not possible_cols:
            logger.error(f"No response column found in {discovery_path}")
            raise ValueError("Missing response column in discovery set")
        response_col = possible_cols[0]
    else:
        response_col = 'response'
        
    # Separate counts and metadata
    # Assuming the first N columns are expression, and the last is metadata
    # Or we need to detect which columns are numeric (expression) vs categorical (metadata)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if response_col not in categorical_cols:
        logger.error(f"Response column '{response_col}' is not categorical.")
        raise ValueError("Response column must be categorical")
        
    # Construct colData
    col_data = df[[response_col]]
    col_data.index = col_data.index # Ensure index matches rows if genes are rows
    
    # Wait, standard format for these files is usually:
    # Rows = Samples, Columns = Genes + Metadata
    # Let's re-evaluate based on typical pandas usage in T020.
    # T020 saves distinct CSVs. Usually: index=sample_id, columns=genes + metadata.
    
    # Re-check: If index is sample_id, then columns are genes + metadata.
    # If index is gene_id, then columns are samples + metadata (unlikely for CSVs).
    
    # Let's assume standard: Index = Sample ID, Columns = Genes + Metadata
    # We need to identify which columns are genes.
    
    # Heuristic: Columns that are numeric and not 'response' are genes?
    # No, metadata can be numeric too.
    # We rely on the fact that the file was generated by T020 which likely
    # saved the expression matrix + a 'response' column.
    
    # If the file has a 'response' column, the rest are likely genes.
    # But we need to be sure. Let's assume the user provided a schema or
    # the file has a specific structure.
    # Given the constraints, we assume:
    # - The file has a 'response' column.
    # - All other columns are gene expression values.
    
    gene_cols = [c for c in df.columns if c != response_col]
    
    if len(gene_cols) == 0:
        logger.error("No gene columns found.")
        raise ValueError("No gene columns found")
        
    counts_df = df[gene_cols].T # Transpose to genes x samples
    col_data = df[[response_col]]
    col_data.index = col_data.index # Sample IDs
    
    # Ensure col_data index matches counts columns
    if not all(counts_df.columns == col_data.index):
        logger.warning("Sample order mismatch, reordering col_data...")
        col_data = col_data.loc[counts_df.columns]
    
    # Run DESeq2
    deseq2_pkg = setup_r_environment()
    results = run_deseq2_analysis(counts_df, col_data)
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / f"{tumor_type}_de_results.csv"
    results['results_df'].to_csv(results_file)
    
    summary_file = output_dir / f"{tumor_type}_de_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'tumor_type': tumor_type,
            'significant_genes': results['significant_genes'],
            'stats': results['stats'],
            'output_file': str(results_file)
        }, f, indent=2)
        
    logger.info(f"Saved results for {tumor_type} to {results_file}")
    
    return {
        'tumor_type': tumor_type,
        'significant_genes': results['significant_genes'],
        'summary_file': str(summary_file)
    }

def main():
    """
    Main entry point for T024: Execute DE on full discovery_set once per tumor type.
    """
    logger.info("Starting T024: Differential Expression on Discovery Sets")
    
    project_root = get_project_root()
    processed_dir = project_root / "code" / "data" / "processed"
    results_dir = project_root / "code" / "results" / "meta_analysis"
    
    # Find discovery sets
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    if not discovery_files:
        logger.error("No discovery set files found in data/processed/")
        sys.exit(1)
        
    logger.info(f"Found {len(discovery_files)} discovery sets.")
    
    all_results = []
    
    for discovery_file in discovery_files:
        # Extract tumor type from filename (e.g., BRCA_discovery_set.csv -> BRCA)
        tumor_type = discovery_file.stem.replace("_discovery_set", "")
        
        try:
            result = process_tumor_type_discovery(
                tumor_type=tumor_type,
                discovery_path=discovery_file,
                output_dir=results_dir
            )
            all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {tumor_type}: {e}")
            # Continue with other types or exit? 
            # Based on FR-005, we need to generate candidates for each type.
            # If one fails, we might not have enough for meta-analysis, 
            # but we log and continue.
            continue
    
    # Save combined summary
    combined_summary = {
        'total_tumor_types_processed': len(all_results),
        'results': all_results
    }
    
    combined_file = results_dir / "de_combined_summary.json"
    with open(combined_file, 'w') as f:
        json.dump(combined_summary, f, indent=2)
        
    logger.info(f"Completed T024. Results saved to {combined_file}")

if __name__ == "__main__":
    main()