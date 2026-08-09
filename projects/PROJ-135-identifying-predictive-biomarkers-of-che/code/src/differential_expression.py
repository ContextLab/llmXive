"""
Differential Expression Analysis Module.

Implements LOO-Blind DE Analysis for cross-tumor biomarker discovery.
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import pandas as pd
import numpy as np
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, Formula, r
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.embedded import RRuntimeError

# Import project utilities and config
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, watchdog, TimeoutError

# Setup logging
logger = setup_logging("differential_expression")

def setup_r_environment():
    """Initialize R environment and load necessary packages."""
    try:
        # Activate pandas conversion
        pandas2ri.activate()
        
        # Load R packages
        utils = importr('utils')
        stats = importr('stats')
        base = importr('base')
        
        # Try to load DESeq2, install if missing
        try:
            deseq2 = importr('DESeq2')
            logger.info("DESeq2 loaded successfully")
        except ImportError:
            logger.warning("DESeq2 not found, attempting installation...")
            utils.install_packages('DESeq2', repos='https://cloud.r-project.org')
            deseq2 = importr('DESeq2')
            logger.info("DESeq2 installed and loaded")
        
        return deseq2, stats, base, utils
    except Exception as e:
        logger.error(f"Failed to setup R environment: {e}")
        raise

def load_discovery_set(tumor_type: str) -> pd.DataFrame:
    """
    Load discovery set data for a specific tumor type.
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD')
        
    Returns:
        DataFrame with expression data and response labels
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / f"{tumor_type}_discovery_set.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Discovery set not found for {tumor_type}: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['sample_id', 'response_label', 'tumor_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {tumor_type}_discovery_set.csv: {missing}")
    
    logger.info(f"Loaded discovery set for {tumor_type}: {len(df)} samples, {len(df.columns) - 3} genes")
    return df

def run_deseq2_analysis_loo(
    dds: Any, 
    tumor_type_held_out: str,
    deseq2: Any,
    stats: Any
) -> pd.DataFrame:
    """
    Run DESeq2 Wald test on the N-1 subset (excluding held-out tumor type).
    
    Args:
        dds: DESeqDataSet object
        tumor_type_held_out: The tumor type being held out
        deseq2: DESeq2 R package
        stats: R stats package
        
    Returns:
        DataFrame with DE results (gene, log2FC, pvalue, padj)
    """
    # Set design and run DESeq
    try:
        # Run DESeq2
        dds = deseq2.DESeq(dds)
        
        # Extract results for the contrast (response vs reference)
        # Assuming response_label is the condition of interest
        res = deseq2.results(dds, name="response_label_Responder_vs_NonResponder")
        
        # Convert to pandas
        res_df = pandas2ri.rpy2py_dataframe(res)
        res_df.reset_index(inplace=True)
        res_df.rename(columns={'index': 'gene_id'}, inplace=True)
        
        logger.info(f"DESeq2 analysis complete: {len(res_df)} genes tested")
        return res_df
        
    except RRuntimeError as e:
        logger.error(f"R error during DESeq2 analysis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during DESeq2 analysis: {e}")
        raise

def process_tumor_type_loo(
    tumor_type: str,
    all_discovery_data: Dict[str, pd.DataFrame],
    deseq2: Any,
    stats: Any,
    base: Any,
    output_dir: Path
) -> bool:
    """
    Process a single tumor type in LOO-Blind mode.
    
    For tumor type T:
    1. Select data from all other tumor types (N-1)
    2. Run DESeq2 on N-1 subset
    3. Save results to loo_iteration_{T}_de_results.csv
    
    Args:
        tumor_type: The tumor type to hold out
        all_discovery_data: Dict mapping tumor_type -> discovery DataFrame
        deseq2: DESeq2 R package
        stats: R stats package
        base: R base package
        output_dir: Directory to save results
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting LOO-Blind analysis for held-out type: {tumor_type}")
    
    # 1. Subset: Select data from all other tumor types (N-1)
    n_minus_1_data = []
    for other_type, df in all_discovery_data.items():
        if other_type != tumor_type:
            n_minus_1_data.append(df)
            logger.info(f"  Included {other_type}: {len(df)} samples")
    
    if not n_minus_1_data:
        logger.warning(f"No N-1 data available for {tumor_type} (only one tumor type exists)")
        return False
    
    combined_df = pd.concat(n_minus_1_data, ignore_index=True)
    logger.info(f"Combined N-1 dataset: {len(combined_df)} samples across {len(n_minus_1_data)} tumor types")
    
    # Prepare data for DESeq2
    # Expression matrix: genes as rows, samples as columns
    # Metadata: sample_id, response_label, tumor_type
    
    # Extract gene columns (everything except metadata)
    metadata_cols = ['sample_id', 'response_label', 'tumor_type']
    gene_cols = [c for c in combined_df.columns if c not in metadata_cols]
    
    if len(gene_cols) == 0:
        logger.error("No gene expression columns found in dataset")
        return False
    
    # Create count matrix (genes x samples)
    count_matrix = combined_df[gene_cols].T  # Transpose: rows=genes, cols=samples
    col_data = combined_df[metadata_cols].set_index('sample_id')
    
    # Ensure response_label is a factor
    col_data['response_label'] = col_data['response_label'].astype(str)
    
    # Convert to R objects
    r_counts = pandas2ri.py2rpy(count_matrix)
    r_col_data = pandas2ri.py2rpy(col_data)
    
    # Create DESeqDataSet in R
    try:
        # Create data frame for R
        r_col_df = base.as_data_frame(r_col_data)
        r_col_df = r.list(**r_col_df)
        
        # Create DESeqDataSet
        dds = deseq2.DESeqDataSetFromMatrix(
            countData=r_counts,
            colData=r_col_df,
            design=Formula('~ response_label')
        )
        
        logger.info("DESeqDataSet created successfully")
        
        # Run DESeq2
        output_file = output_dir / f"loo_iteration_{tumor_type}_de_results.csv"
        
        def run_analysis():
            results = run_deseq2_analysis_loo(dds, tumor_type, deseq2, stats)
            
            # Filter for significant genes (FDR < 0.05, |log2FC| > 1.0)
            significant = results[
                (results['padj'] < 0.05) & 
                (abs(results['log2FoldChange']) > 1.0)
            ].copy()
            
            # Select relevant columns
            significant = significant[['gene_id', 'log2FoldChange', 'pvalue', 'padj']]
            significant['tumor_type_held_out'] = tumor_type
            significant['n_minus_1_sample_count'] = len(combined_df)
            
            # Save results
            significant.to_csv(output_file, index=False)
            logger.info(f"Saved significant genes ({len(significant)}) to {output_file}")
            
            return True
        
        # Run with timeout watchdog
        success = watchdog(run_analysis, timeout=3600)
        return success
        
    except Exception as e:
        logger.error(f"Failed to create or process DESeqDataSet for {tumor_type}: {e}")
        return False

def run_deseq2_analysis(
    discovery_data_dir: Path = None,
    output_dir: Path = None,
    timeout_hours: float = 1.0
):
    """
    Main entry point for LOO-Blind DE Analysis.
    
    For each tumor type T:
    1. Load discovery sets for all tumor types
    2. For each T, run DE on N-1 subset
    3. Save results to loo_iteration_{T}_de_results.csv
    
    Args:
        discovery_data_dir: Directory containing *_discovery_set.csv files
        output_dir: Directory to save results
        timeout_hours: Timeout for R process
    """
    if discovery_data_dir is None:
        project_root = get_project_root()
        discovery_data_dir = project_root / "data" / "processed"
    
    if output_dir is None:
        project_root = get_project_root()
        output_dir = project_root / "data" / "processed"
    
    ensure_directories([output_dir])
    
    # Find all discovery set files
    discovery_files = list(discovery_data_dir.glob("*_discovery_set.csv"))
    if not discovery_files:
        logger.error("No discovery set files found in {discovery_data_dir}")
        sys.exit(1)
    
    # Extract tumor types
    tumor_types = []
    for f in discovery_files:
        type_name = f.stem.replace("_discovery_set", "")
        tumor_types.append(type_name)
    
    logger.info(f"Found {len(tumor_types)} tumor types: {tumor_types}")
    
    # Check minimum requirement for LOO
    if len(tumor_types) < 2:
        logger.error("LOO-Blind analysis requires at least 2 tumor types")
        sys.exit(1)
    
    # Load all discovery data
    all_discovery_data = {}
    for tt in tumor_types:
        try:
            df = load_discovery_set(tt)
            all_discovery_data[tt] = df
        except Exception as e:
            logger.error(f"Failed to load discovery set for {tt}: {e}")
            # Continue with available data
            continue
    
    if len(all_discovery_data) < 2:
        logger.error("Insufficient valid discovery sets for LOO analysis")
        sys.exit(1)
    
    # Setup R environment
    logger.info("Setting up R environment...")
    try:
        deseq2, stats, base, utils = setup_r_environment()
    except Exception as e:
        logger.error(f"Failed to setup R environment: {e}")
        sys.exit(1)
    
    # Process each tumor type in LOO mode
    success_count = 0
    for tumor_type in tumor_types:
        if tumor_type not in all_discovery_data:
            logger.warning(f"Skipping {tumor_type}: discovery set not loaded")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing LOO iteration for held-out type: {tumor_type}")
        logger.info(f"{'='*60}")
        
        success = process_tumor_type_loo(
            tumor_type=tumor_type,
            all_discovery_data=all_discovery_data,
            deseq2=deseq2,
            stats=stats,
            base=base,
            output_dir=output_dir
        )
        
        if success:
            success_count += 1
            logger.info(f"✓ Successfully completed LOO iteration for {tumor_type}")
        else:
            logger.error(f"✗ Failed LOO iteration for {tumor_type}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"LOO-Blind DE Analysis Complete")
    logger.info(f"Successful iterations: {success_count}/{len(tumor_types)}")
    logger.info(f"{'='*60}")
    
    # Verify output files
    output_files = list(output_dir.glob("loo_iteration_*_de_results.csv"))
    logger.info(f"Generated {len(output_files)} LOO result files")
    
    return len(output_files)

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LOO-Blind DE Analysis")
    parser.add_argument(
        "--discovery-dir", 
        type=str, 
        default=None,
        help="Directory containing discovery sets"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=None,
        help="Directory to save results"
    )
    parser.add_argument(
        "--timeout", 
        type=float, 
        default=1.0,
        help="Timeout in hours for R process"
    )
    
    args = parser.parse_args()
    
    discovery_dir = Path(args.discovery_dir) if args.discovery_dir else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        count = run_deseq2_analysis(
            discovery_data_dir=discovery_dir,
            output_dir=output_dir,
            timeout_hours=args.timeout
        )
        
        if count == 0:
            logger.error("No LOO result files generated")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
