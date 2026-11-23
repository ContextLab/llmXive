import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, Formula
from rpy2.robjects.packages import importr

from src.config import get_project_root
from src.utils import ensure_path_exists, setup_logging

# Setup logging
logger = logging.getLogger(__name__)
setup_logging()

def setup_r_environment():
    """Initialize R environment and load necessary packages."""
    try:
        # Activate pandas conversion
        pandas2ri.activate()
        
        # Load R packages
        utils = importr('utils')
        # Try to load BiocManager, install DESeq2 if needed
        try:
            biocmanager = importr('BiocManager')
        except ImportError:
            # If BiocManager not found, try installing it via utils
            utils.install_packages('BiocManager')
            biocmanager = importr('BiocManager')
        
        # Install DESeq2 if not present
        if not biocmanager.is_installed('DESeq2'):
            logger.info("Installing DESeq2 via BiocManager...")
            biocmanager.install('DESeq2', update=False, ask=False)
        
        deseq2 = importr('DESeq2')
        return deseq2
    except Exception as e:
        logger.error(f"Failed to setup R environment: {e}")
        raise

def load_discovery_set(tumor_type: str, project_root: Path) -> pd.DataFrame:
    """
    Load the discovery set CSV for a specific tumor type.
    Expected file: data/processed/{tumor_type}_discovery_set.csv
    
    Returns a DataFrame with:
    - index: gene identifiers (will be set as rownames for DESeq2)
    - columns: sample IDs
    - metadata columns (e.g., 'response_label', 'tumor_type')
    """
    input_path = project_root / "data" / "processed" / f"{tumor_type}_discovery_set.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Discovery set file not found: {input_path}")
    
    # Load CSV
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['response_label']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    # Assume first column is gene_id if not named 'gene_id'
    # Check if there's a 'gene_id' column, otherwise assume index or first col
    if 'gene_id' not in df.columns:
        # Try to infer: if first column looks like gene IDs (strings), use it
        if df.iloc[:, 0].dtype == object or all(isinstance(x, str) for x in df.iloc[:, 0]):
            df = df.rename(columns={df.columns[0]: 'gene_id'})
        else:
            raise ValueError(f"Could not identify gene_id column in {input_path}")
    
    # Ensure response_label is present
    if 'response_label' not in df.columns:
        raise ValueError(f"Missing 'response_label' column in {input_path}")
    
    return df

def run_deseq2_analysis(df: pd.DataFrame, tumor_type: str, dds_name: str = "dds") -> pd.DataFrame:
    """
    Run DESeq2 Wald test on the provided DataFrame.
    
    Input DataFrame structure:
    - Rows: genes
    - Columns: samples (expression values) + metadata columns (response_label)
    
    Returns a DataFrame with DE results: gene_id, log2FoldChange, pvalue, padj
    """
    # Prepare data for DESeq2
    # Separate expression matrix and metadata
    # Assume all columns except 'gene_id' and 'response_label' are samples
    expression_cols = [c for c in df.columns if c not in ['gene_id', 'response_label']]
    
    if len(expression_cols) < 2:
        raise ValueError(f"Not enough sample columns for DE analysis in {tumor_type}")
    
    # Create count matrix (genes x samples)
    count_matrix = df.set_index('gene_id')[expression_cols].T  # Transpose to samples x genes
    
    # Create colData (metadata)
    col_data = df.set_index('gene_id')[['response_label']].T  # samples x metadata
    col_data.index.name = 'sample_id'
    
    # Convert to R objects
    counts_r = pandas2ri.py2rpy(count_matrix.values.astype(int))
    colnames_r = pandas2ri.py2rpy(col_data.index.tolist())
    rownames_r = pandas2ri.py2rpy(count_matrix.columns.tolist())
    
    # Create DESeqDataSet
    dds = ro.r['new']
    
    # Use R code to create DESeqDataSetFromMatrix
    r_code = f"""
    counts <- matrix({list(count_matrix.values.astype(int).flatten())}, 
                     nrow={len(count_matrix.index)}, 
                     ncol={len(count_matrix.columns)},
                     dimnames=list({list(count_matrix.columns)}, {list(count_matrix.index)}))
    colData <- data.frame(response_label={list(col_data['response_label'].tolist())},
                          row.names={list(col_data.index.tolist())})
    dds <- DESeqDataSetFromMatrix(countData = counts,
                                  colData = colData,
                                  design = ~ response_label)
    """
    
    try:
        ro.r(r_code)
        
        # Run DESeq
        ro.r('dds <- DESeq(dds)')
        
        # Get results
        res = ro.r('results(dds)')
        
        # Convert back to pandas
        res_df = pandas2ri.rpy2py(res)
        
        # Reset index to get gene_id as column
        res_df = res_df.reset_index()
        res_df = res_df.rename(columns={'index': 'gene_id'})
        
        # Filter significant genes (FDR < 0.05, |log2FC| > 1.0)
        significant = res_df[
            (res_df['padj'] < 0.05) & 
            (abs(res_df['log2FoldChange']) > 1.0)
        ].copy()
        
        logger.info(f"DESeq2 analysis for {tumor_type}: {len(significant)} significant genes found")
        
        return significant
        
    except Exception as e:
        logger.error(f"DESeq2 analysis failed for {tumor_type}: {e}")
        raise

def process_tumor_type(tumor_type: str, project_root: Path) -> Dict[str, Any]:
    """
    Process a single tumor type: load discovery set, run DESeq2, save results.
    
    Returns a dict with status and output path.
    """
    output_path = project_root / "data" / "processed" / f"{tumor_type}_de_results.csv"
    
    try:
        # Load discovery set
        df = load_discovery_set(tumor_type, project_root)
        
        # Check sample count
        sample_count = len(df.columns) - 2  # Subtract gene_id and response_label
        if sample_count < 10:
            logger.warning(f"Skipping {tumor_type}: only {sample_count} samples (minimum 10 required)")
            return {
                'status': 'skipped',
                'reason': f'insufficient_samples ({sample_count})',
                'output_path': str(output_path)
            }
        
        # Run DESeq2
        results_df = run_deseq2_analysis(df, tumor_type)
        
        # Save results
        results_df.to_csv(output_path, index=False)
        
        return {
            'status': 'completed',
            'gene_count': len(results_df),
            'output_path': str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Failed to process {tumor_type}: {e}")
        return {
            'status': 'failed',
            'reason': str(e),
            'output_path': str(output_path)
        }

def aggregate_results(project_root: Path) -> None:
    """
    Aggregate all DE results into a single static file.
    Scans data/processed/ for {tumor_type}_de_results.csv files.
    """
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "static_aggregated_results.csv"
    
    # Find all DE result files
    de_files = sorted(processed_dir.glob("*_de_results.csv"))
    
    if not de_files:
        logger.warning("No DE result files found for aggregation")
        # Create empty file
        pd.DataFrame(columns=['gene_id', 'log2FoldChange', 'pvalue', 'padj', 'tumor_type']).to_csv(output_file, index=False)
        return
    
    # Load and concatenate
    all_results = []
    for file_path in de_files:
        tumor_type = file_path.stem.replace('_de_results', '')
        df = pd.read_csv(file_path)
        df['tumor_type'] = tumor_type
        all_results.append(df)
    
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        combined.to_csv(output_file, index=False)
        logger.info(f"Aggregated DE results from {len(de_files)} tumor types to {output_file}")
    else:
        # Create empty file
        pd.DataFrame(columns=['gene_id', 'log2FoldChange', 'pvalue', 'padj', 'tumor_type']).to_csv(output_file, index=False)

def main():
    """Main entry point for T023: Per-Tumor-Type DE on Full Discovery Set."""
    project_root = get_project_root()
    
    # Setup R environment
    deseq2 = setup_r_environment()
    
    # Get list of tumor types from discovery set files
    processed_dir = project_root / "data" / "processed"
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    if not discovery_files:
        logger.error("No discovery set files found in data/processed/")
        sys.exit(1)
    
    # Extract tumor types from filenames
    tumor_types = [f.stem.replace('_discovery_set', '') for f in discovery_files]
    tumor_types = sorted(set(tumor_types))  # Unique and sorted
    
    logger.info(f"Processing DE for {len(tumor_types)} tumor types: {tumor_types}")
    
    # Process each tumor type
    results = []
    for tumor_type in tumor_types:
        result = process_tumor_type(tumor_type, project_root)
        results.append(result)
        logger.info(f"Processed {tumor_type}: {result['status']}")
    
    # Aggregate results
    aggregate_results(project_root)
    
    # Log summary
    completed = sum(1 for r in results if r['status'] == 'completed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    logger.info(f"DE Analysis Summary: {completed} completed, {skipped} skipped, {failed} failed")
    
    if failed > 0:
        logger.warning(f"{failed} tumor types failed DE analysis")
    
    return results

if __name__ == "__main__":
    main()
