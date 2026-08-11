import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from mygene import MyGeneInfo

from src.config import get_project_root, ensure_directories
from src.utils import calculate_checksum, setup_logging

# Configure logging
logger = setup_logging("preprocessing")

# Constants
MIN_HGNC_COVERAGE = 0.95
FEASIBILITY_GATE_PATH = "data/feasibility_gate.json"


def load_processed_data(file_path: str) -> pd.DataFrame:
    """
    Load a processed dataset CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        DataFrame with gene expression data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Loaded dataset is empty: {file_path}")
        
    # Expected columns: sample_id, tumor_type, response_label, expression_vector (or gene columns)
    # We assume the first column is sample_id/metadata and the rest are gene expression values
    # or that there is a specific 'gene_id' column. 
    # Based on context of T017/T016, we expect a matrix where rows are samples and columns are genes.
    # However, for harmonization, we need a mapping of current IDs to HGNC.
    # If the data is a matrix (samples x genes), the columns are gene IDs.
    # If the data is a long format (sample, gene, value), we need to pivot.
    # Assuming standard wide format: index=sample, columns=GeneIDs
    
    if 'gene_id' in df.columns:
        # Long format: pivot to wide
        # Expecting: sample_id, gene_id, expression_value
        if 'sample_id' not in df.columns or 'expression_value' not in df.columns:
            raise ValueError("Long format data missing required columns: sample_id, gene_id, expression_value")
        df = df.pivot(index='sample_id', columns='gene_id', values='expression_value')
        df = df.reset_index()
        
    return df


def harmonize_gene_ids(df: pd.DataFrame, gene_column: Optional[str] = None) -> Tuple[pd.DataFrame, float, List[str]]:
    """
    Harmonize Ensembl/Entrez IDs to HGNC symbols using mygene.info.
    
    Args:
        df: DataFrame containing gene expression data. Columns should be gene IDs
            or contain a 'gene_id' column if long format.
        gene_column: Name of the column containing gene IDs. If None, assumes 
                     columns (excluding 'sample_id', 'tumor_type', 'response_label') are gene IDs.
                     
    Returns:
        Tuple of (DataFrame with HGNC symbols, coverage_percentage, list of excluded genes)
        
    Raises:
        RuntimeError: If mygene query fails completely.
    """
    if df.empty:
        raise ValueError("Cannot harmonize empty DataFrame")

    # Identify gene columns
    exclude_cols = {'sample_id', 'tumor_type', 'response_label'}
    if gene_column:
        gene_cols = [gene_column]
    else:
        # Assume all columns except metadata are gene IDs
        gene_cols = [col for col in df.columns if col not in exclude_cols]

    if not gene_cols:
        logger.warning("No gene columns found in dataset.")
        return df, 1.0, []

    total_genes = len(gene_cols)
    if total_genes == 0:
        return df, 1.0, []

    # Prepare query list
    query_ids = gene_cols
    mg = MyGeneInfo()
    
    # Batch query mygene (max 1000 per request usually, but we can do chunked)
    # mygene.getgenes supports multiple IDs
    logger.info(f"Querying mygene.info for {total_genes} gene IDs...")
    
    # Split into chunks to avoid timeout/size limits
    chunk_size = 1000
    results_map = {}
    
    for i in range(0, len(query_ids), chunk_size):
        chunk = query_ids[i:i+chunk_size]
        try:
            # querytype can be 'entrez', 'ensembl', 'symbol', etc. We try to detect or default to 'symbol'
            # If the IDs look like Ensembl (ENSG...), we might need to specify. 
            # mygene usually auto-detects or accepts a list.
            # We will try to query without specifying type first, let it infer, 
            # or we assume the input is Ensembl/Entrez as per task description.
            # To be safe, we query all and map the 'symbol' field.
            res = mg.getgenes(chunk, fields='symbol', as_dataframe=False)
            
            for item in res:
                if 'query' in item:
                    original_id = item['query']
                    symbol = item.get('symbol', None)
                    if symbol:
                        results_map[original_id] = symbol
                    else:
                        # No symbol found
                        pass
        except Exception as e:
            logger.error(f"Error querying mygene for chunk {i}: {e}")
            # Continue with partial results, but log critical warning
            continue

    if not results_map:
        logger.critical("Failed to retrieve any gene symbols from mygene.info.")
        # If we can't map anything, coverage is 0%
        return df, 0.0, query_ids

    # Map original IDs to HGNC symbols
    new_columns = []
    excluded_genes = []
    mapped_count = 0

    for col in gene_cols:
        if col in results_map:
            new_name = results_map[col]
            # Handle duplicates: if multiple Ensembl IDs map to same HGNC, we might need to sum or keep first
            # For simplicity in this step, we rename. If duplicate column names occur, pandas will handle or we can aggregate.
            # We'll assume unique mapping for now, but if duplicates happen, we rename to 'Symbol_1', etc.
            if new_name in new_columns:
                # Conflict resolution: append original ID
                new_name = f"{new_name}_{col}"
            new_columns.append(new_name)
            mapped_count += 1
        else:
            excluded_genes.append(col)
            new_columns.append(col) # Keep original if not found, or drop? 
            # Task says: "filter if coverage <95%". It implies we keep what we can map and check coverage.
            # If not mapped, it's excluded from the *valid* set for coverage calc.
            # We will keep the column but mark it as unmapped? 
            # Better: Drop unmapped columns for the harmonized dataset? 
            # The task says "Harmonize... filter if coverage <95%".
            # Let's keep the unmapped columns but they won't count towards the "mapped" coverage.
            # Actually, if coverage < 95%, we exclude the *dataset*. 
            # So we need to know the ratio of successfully mapped genes.
            pass

    # Create the new DataFrame
    # Rename columns
    df_harmonized = df.copy()
    
    # We need to map the columns in the dataframe
    # The columns in df are the original IDs. We want to replace them with HGNC symbols.
    # But we must preserve metadata columns.
    
    # Create a mapping dict for rename
    rename_map = {}
    final_columns = []
    
    for old_col, new_col in zip(gene_cols, new_columns):
        rename_map[old_col] = new_col
        
    df_harmonized = df_harmonized.rename(columns=rename_map)
    
    # Reorder columns to put metadata first? Not strictly necessary but good practice.
    # Calculate coverage
    coverage = mapped_count / total_genes if total_genes > 0 else 0.0
    
    logger.info(f"Harmonization complete. Mapped {mapped_count}/{total_genes} genes ({coverage:.2%}).")
    
    return df_harmonized, coverage, excluded_genes


def filter_low_coverage_dataset(df: pd.DataFrame, coverage: float, dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Filter dataset if harmonization coverage is below threshold.
    
    Args:
        df: Harmonized DataFrame.
        coverage: The coverage percentage calculated.
        dataset_name: Name of the dataset for logging.
        
    Returns:
        DataFrame if coverage >= 95%, None otherwise.
    """
    if coverage < MIN_HGNC_COVERAGE:
        excluded_count = int(len(df.columns) * (1 - coverage))
        logger.critical(
            f"Dataset '{dataset_name}' has low harmonization coverage: {coverage:.2%} "
            f"({excluded_count} genes excluded). Threshold is {MIN_HGNC_COVERAGE:.0%}."
        )
        return None
    
    logger.info(f"Dataset '{dataset_name}' passed harmonization filter with {coverage:.2%} coverage.")
    return df


def write_feasibility_gate_partial_failure(dataset_name: str, coverage: float, excluded_count: int):
    """
    Write partial failure to feasibility gate JSON.
    
    Args:
        dataset_name: Name of the dataset that failed.
        coverage: The coverage percentage.
        excluded_count: Number of excluded genes.
    """
    gate_data = {
        "status": "partial_failure",
        "reason": "low_harmonization_coverage",
        "dataset": dataset_name,
        "coverage_percentage": coverage,
        "excluded_genes_count": excluded_count,
        "details": f"Coverage {coverage:.2%} is below threshold {MIN_HGNC_COVERAGE:.0%}"
    }
    
    project_root = get_project_root()
    gate_path = project_root / FEASIBILITY_GATE_PATH
    
    # Ensure directory exists
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write atomically
    temp_path = gate_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(gate_data, f, indent=2)
    temp_path.rename(gate_path)
    
    logger.info(f"Written partial failure to {gate_path}")


def process_tumor_type_harmonization(df: pd.DataFrame, tumor_type: str) -> Optional[pd.DataFrame]:
    """
    Process a single tumor type dataset: harmonize and check coverage.
    
    Args:
        df: DataFrame for a single tumor type.
        tumor_type: Name of the tumor type.
        
    Returns:
        Processed DataFrame if successful, None if coverage is too low.
    """
    harmonized_df, coverage, excluded_genes = harmonize_gene_ids(df)
    
    if coverage < MIN_HGNC_COVERAGE:
        write_feasibility_gate_partial_failure(
            tumor_type, 
            coverage, 
            len(excluded_genes)
        )
        return None
        
    return harmonized_df


def main():
    """
    Main entry point for T015: Harmonize gene IDs for all processed datasets.
    """
    logger.info("Starting T015: Gene ID Harmonization")
    project_root = get_project_root()
    ensure_directories()
    
    # Find all processed discovery sets
    processed_dir = project_root / "data" / "processed"
    if not processed_dir.exists():
        logger.error("Processed data directory not found. Run data acquisition first.")
        sys.exit(1)
        
    discovery_files = list(processed_dir.glob("*_discovery_set.csv"))
    
    if not discovery_files:
        logger.warning("No discovery set files found. Skipping harmonization.")
        sys.exit(0)
        
    processed_datasets = {}
    failed_datasets = []
    
    for file_path in discovery_files:
        try:
            logger.info(f"Processing {file_path.name}...")
            df = load_processed_data(str(file_path))
            
            # Extract tumor type from filename (e.g., "BRCA_discovery_set.csv" -> "BRCA")
            tumor_type = file_path.stem.replace("_discovery_set", "")
            
            harmonized_df = process_tumor_type_harmonization(df, tumor_type)
            
            if harmonized_df is None:
                failed_datasets.append(tumor_type)
                # Do not save, do not proceed with this dataset
                continue
                
            # Save harmonized data
            output_path = processed_dir / f"{tumor_type}_harmonized_discovery_set.csv"
            harmonized_df.to_csv(output_path, index=False)
            logger.info(f"Saved harmonized data to {output_path}")
            processed_datasets[tumor_type] = output_path
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            failed_datasets.append(tumor_type)
            
    if failed_datasets:
        logger.warning(f"Failed harmonization for datasets: {failed_datasets}")
        # If all failed, we might want to halt, but task says "exclude specific dataset"
        # We proceed with the ones that passed.
        
    logger.info("T015 Harmonization Complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
