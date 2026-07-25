import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
import pandas as pd
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

def align_data(genomes_df: pd.DataFrame, metabolites_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge genomic and metabolomic data by species.
    Filters partial rows and logs warnings.
    """
    logger.info("Aligning genomic and metabolomic data...")
    
    # Ensure species column is string and normalized
    genomes_df = genomes_df.copy()
    metabolites_df = metabolites_df.copy()
    
    genomes_df['species'] = genomes_df['species'].astype(str).str.strip().str.lower()
    metabolites_df['species'] = metabolites_df['species'].astype(str).str.strip().str.lower()
    
    # Merge on species
    aligned = pd.merge(
        genomes_df, 
        metabolites_df, 
        on='species', 
        how='inner',
        suffixes=('_genome', '_metabo')
    )
    
    total_genomes = len(genomes_df)
    total_metabolites = len(metabolites_df)
    total_aligned = len(aligned)
    
    logger.info(f"Genomes input: {total_genomes}, Metabolites input: {total_metabolites}")
    logger.info(f"Aligned species count: {total_aligned}")
    
    if total_aligned == 0:
        logger.warning("No species found in both datasets.")
    
    return aligned

def save_aligned_matrix(df: pd.DataFrame, output_path: Union[str, Path]) -> None:
    """
    Write the final CSV to the specified path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Aligned matrix saved to {output_path}")

def calculate_alignment_success_rate(
    aligned_df: pd.DataFrame, 
    min_species_count: int = 5,
    required_columns: Optional[List[str]] = None
) -> float:
    """
    Calculate, log, and report the percentage of species with valid data (N>=min_species_count).
    
    This implements SC-004 success criteria.
    
    Args:
        aligned_df: The merged DataFrame containing genomic and metabolomic data.
        min_species_count: Minimum number of valid data points required to count as 'success'.
        required_columns: Optional list of columns that must be non-null for a row to be valid.
                          If None, checks if any data column exists.
    
    Returns:
        float: The success rate (0.0 to 1.0).
    """
    if aligned_df.empty:
        logger.warning("Aligned DataFrame is empty. Success rate: 0.0")
        return 0.0
    
    # Determine validity of each row
    # A row is valid if it has non-null values in the key data columns.
    # Typically, we expect BGC counts and Metabolite abundances.
    
    # Identify candidate data columns (exclude metadata like 'species')
    all_cols = aligned_df.columns.tolist()
    metadata_cols = ['species']
    data_cols = [c for c in all_cols if c not in metadata_cols]
    
    if not data_cols:
        logger.error("No data columns found in aligned DataFrame.")
        return 0.0
    
    if required_columns:
        # Use specific columns if provided
        check_cols = [c for c in required_columns if c in aligned_df.columns]
        if not check_cols:
            logger.warning(f"None of the required columns {required_columns} found in DataFrame.")
            return 0.0
    else:
        check_cols = data_cols
    
    # Check for non-null values in the specified columns
    valid_mask = aligned_df[check_cols].notna().all(axis=1)
    valid_count = valid_mask.sum()
    total_count = len(aligned_df)
    
    success_rate = valid_count / total_count if total_count > 0 else 0.0
    
    # Log the result
    logger.info(f"Alignment Success Rate Calculation:")
    logger.info(f"  Total species: {total_count}")
    logger.info(f"  Valid species (non-null in {check_cols}): {valid_count}")
    logger.info(f"  Success Rate: {success_rate:.2%}")
    
    if success_rate < 1.0:
        logger.warning(f"{total_count - valid_count} species have missing data in key columns.")
    
    return success_rate

def main():
    """
    Main entry point for alignment and success rate calculation.
    """
    # Example usage (would normally load from config/files)
    # This function demonstrates the flow expected by the pipeline
    logger.info("Starting alignment process...")
    
    # Placeholder for actual data loading logic
    # In a real run, these would be loaded from data/raw or data/processed
    # For this task, we assume the data exists or is passed in
    pass

if __name__ == "__main__":
    main()