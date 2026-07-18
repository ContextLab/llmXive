"""
Preprocessing module for harmonizing gene identifiers and filtering low-expression genes.

This module implements:
1. Harmonization of Ensembl/Entrez IDs to HGNC symbols using mygene
2. Filtering of genes with low coverage (<95% HGNC mapping)
3. Filtering of low-expression genes (CPM < 1 in >80% samples)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from mygene import MyGeneInfo

# Import project utilities
from src.config import ensure_directories
from src.utils import setup_logging, calculate_checksum

# Configure logging
logger = setup_logging(__name__)

# Constants
MIN_HGNC_COVERAGE = 0.95  # FR-003: Filter if coverage < 95%
CPM_THRESHOLD = 1.0       # FR-004: CPM threshold
LOW_EXPR_FRACTION = 0.80  # FR-004: Filter if CPM < 1 in >80% samples

def load_processed_data(tumor_type: str, data_dir: Path) -> pd.DataFrame:
    """
    Load processed TCGA/GEO data for a specific tumor type.
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD')
        data_dir: Path to the data directory
        
    Returns:
        DataFrame with gene expression data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist
    """
    # Expected path based on T012/T013 output
    file_path = data_dir / "raw" / f"{tumor_type}_expression.csv"
    
    if not file_path.exists():
        # Try alternative path from acquisition
        file_path = data_dir / f"{tumor_type}_expression.csv"
        
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found for {tumor_type}: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    return df

def harmonize_gene_ids(df: pd.DataFrame, id_column: str = 'gene_id') -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Harmonize Ensembl/Entrez IDs to HGNC symbols using mygene.
    
    Implements FR-003: Map gene identifiers and filter if coverage < 95%.
    
    Args:
        df: DataFrame with gene expression data
        id_column: Name of the column containing gene identifiers
        
    Returns:
        Tuple of (DataFrame with HGNC symbols, coverage statistics per source)
        
    Raises:
        ValueError: If HGNC coverage is below 95%
    """
    logger.info(f"Starting gene ID harmonization for {len(df)} genes")
    
    # Get unique IDs to query
    unique_ids = df[id_column].dropna().unique().tolist()
    total_ids = len(unique_ids)
    
    if total_ids == 0:
        raise ValueError("No gene IDs found in input data")
    
    logger.info(f"Querying {total_ids} unique gene IDs via mygene")
    
    # Use mygene to fetch HGNC symbols
    mg = MyGeneInfo()
    
    # Query in batches to avoid rate limiting
    batch_size = 100
    results = []
    
    for i in range(0, len(unique_ids), batch_size):
        batch = unique_ids[i:i+batch_size]
        try:
            batch_results = mg.querymany(
                batch,
                scopes='entrezgene,ensembl.gene',
                fields='symbol,species',
                species='human',
                returnall=False
            )
            results.extend(batch_results)
        except Exception as e:
            logger.warning(f"Batch query failed: {e}. Retrying with single queries...")
            # Fallback to individual queries if batch fails
            for gene_id in batch:
                try:
                    single_result = mg.querymany(
                        [gene_id],
                        scopes='entrezgene,ensembl.gene',
                        fields='symbol,species',
                        species='human'
                    )
                    if single_result:
                        results.extend(single_result)
                except Exception as single_err:
                    logger.warning(f"Single query failed for {gene_id}: {single_err}")
    
    # Create mapping dictionary
    id_to_hgnc = {}
    mapped_count = 0
    
    for result in results:
        if 'symbol' in result and result.get('symbol'):
            original_id = result.get('query')
            hgnc_symbol = result['symbol']
            if original_id and hgnc_symbol:
                id_to_hgnc[original_id] = hgnc_symbol
                mapped_count += 1
    
    coverage = mapped_count / total_ids if total_ids > 0 else 0
    logger.info(f"Gene ID mapping coverage: {coverage:.2%} ({mapped_count}/{total_ids})")
    
    # FR-003: Check coverage threshold
    if coverage < MIN_HGNC_COVERAGE:
        error_msg = (
            f"HGNC mapping coverage ({coverage:.2%}) is below threshold "
            f"({MIN_HGNC_COVERAGE:.0%}). Aborting preprocessing."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Map IDs in DataFrame
    df = df.copy()
    df['hgnc_symbol'] = df[id_column].map(id_to_hgnc)
    
    # Count genes that couldn't be mapped
    unmapped = df[df['hgnc_symbol'].isna()]
    if len(unmapped) > 0:
        logger.warning(f"Found {len(unmapped)} genes without HGNC symbol mapping")
    
    # Filter out unmapped genes
    df = df.dropna(subset=['hgnc_symbol'])
    
    # Remove duplicate HGNC symbols (keep first occurrence or aggregate)
    if df['hgnc_symbol'].duplicated().any():
        logger.warning("Duplicate HGNC symbols found. Keeping first occurrence.")
        df = df.drop_duplicates(subset=['hgnc_symbol'], keep='first')
    
    logger.info(f"Final gene count after harmonization: {len(df)}")
    
    return df, {'total_mapped': mapped_count, 'coverage': coverage}

def filter_low_expression_genes(df: pd.DataFrame, expression_column: str = 'expression', 
                               sample_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter genes with low expression (CPM < 1 in >80% samples).
    
    Implements FR-004: Filter low-expression genes.
    
    Args:
        df: DataFrame with gene expression data (already harmonized)
        expression_column: Column containing expression values (assumed to be CPM or similar)
        sample_columns: List of sample column names. If None, all numeric columns are used.
        
    Returns:
        Filtered DataFrame
    """
    logger.info("Starting low-expression gene filtering")
    
    if sample_columns is None:
        # Assume all columns except gene identifiers are samples
        sample_columns = [col for col in df.columns if col not in ['gene_id', 'hgnc_symbol']]
    
    if len(sample_columns) == 0:
        logger.warning("No sample columns found for expression filtering")
        return df
    
    # Calculate fraction of samples with CPM < threshold
    low_expr_mask = df[sample_columns].lt(CPM_THRESHOLD).mean(axis=1) > LOW_EXPR_FRACTION
    
    genes_to_remove = low_expr_mask.sum()
    genes_to_keep = (~low_expr_mask).sum()
    
    logger.info(f"Removing {genes_to_remove} genes with low expression "
               f"(CPM < {CPM_THRESHOLD} in >{LOW_EXPR_FRACTION:.0%} of samples)")
    logger.info(f"Keeping {genes_to_keep} genes")
    
    filtered_df = df[~low_expr_mask].copy()
    
    return filtered_df

def save_filtered_data(df: pd.DataFrame, tumor_type: str, output_dir: Path) -> str:
    """
    Save filtered and harmonized data to disk.
    
    Args:
        df: Filtered DataFrame
        tumor_type: Tumor type identifier
        output_dir: Directory to save output files
        
    Returns:
        Path to saved file
    """
    ensure_directories([output_dir])
    
    output_path = output_dir / f"{tumor_type}_harmonized_filtered.csv"
    
    df.to_csv(output_path, index=False)
    
    # Generate checksum
    checksum = calculate_checksum(output_path)
    
    logger.info(f"Saved filtered data to {output_path}")
    logger.info(f"Checksum: {checksum}")
    
    return str(output_path)

def process_tumor_type(tumor_type: str, data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single tumor type: harmonize IDs and filter low-expression genes.
    
    Args:
        tumor_type: Tumor type identifier
        data_dir: Path to raw data directory
        output_dir: Path to output directory
        
    Returns:
        Dictionary with processing results and metadata
    """
    logger.info(f"Processing tumor type: {tumor_type}")
    
    try:
        # Load data
        df = load_processed_data(tumor_type, data_dir)
        
        # Harmonize gene IDs
        df_harmonized, mapping_stats = harmonize_gene_ids(df)
        
        # Filter low-expression genes
        df_filtered = filter_low_expression_genes(df_harmonized)
        
        # Save results
        output_path = save_filtered_data(df_filtered, tumor_type, output_dir)
        
        result = {
            'tumor_type': tumor_type,
            'status': 'success',
            'initial_genes': len(df),
            'genes_after_harmonization': len(df_harmonized),
            'genes_after_filtering': len(df_filtered),
            'hgnc_coverage': mapping_stats['coverage'],
            'output_path': output_path
        }
        
        logger.info(f"Processing complete for {tumor_type}: "
                   f"{result['initial_genes']} -> {result['genes_after_filtering']} genes")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process {tumor_type}: {e}")
        return {
            'tumor_type': tumor_type,
            'status': 'failed',
            'error': str(e)
        }

def main():
    """Main entry point for preprocessing pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess gene expression data')
    parser.add_argument('--tumor-types', nargs='+', required=True,
                      help='List of tumor types to process')
    parser.add_argument('--data-dir', type=str, default='data',
                      help='Root data directory')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Output directory for processed data')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    ensure_directories([output_dir])
    
    results = []
    for tumor_type in args.tumor_types:
        result = process_tumor_type(tumor_type, data_dir, output_dir)
        results.append(result)
    
    # Save summary
    summary_path = output_dir / 'preprocessing_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Preprocessing complete. Summary saved to {summary_path}")
    
    # Exit with error if any processing failed
    failed = [r for r in results if r['status'] == 'failed']
    if failed:
        logger.error(f"{len(failed)} tumor types failed to process")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()