"""
Data Alignment Module for Plant Secondary Metabolite Prediction Pipeline.

This module implements the alignment of genomic (BGC) and metabolomic data
by species, handling filtering of partial rows and logging warnings for
missing data points.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

# Import project utilities
from utils.logging import get_logger
from config import get_data_path, get_species_list

# Ensure logger is available
logger = get_logger(__name__)


def align_data(
    genomic_df: pd.DataFrame,
    metabolomic_df: pd.DataFrame,
    species_list: Optional[list] = None,
    min_features: int = 1
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Merge genomic and metabolomic data by species, filtering partial rows.

    This function performs an inner join on the 'species' column (or equivalent
    identifier) between the genomic and metabolomic DataFrames. It filters out
    rows that have missing values in either dataset and logs warnings for
    species that were dropped due to incomplete data.

    Args:
        genomic_df: DataFrame containing BGC features (columns: species, bgc_..., etc.)
        metabolomic_df: DataFrame containing metabolite abundances (columns: species, met_..., etc.)
        species_list: Optional list of species to include. If None, uses all species present in both.
        min_features: Minimum number of non-null features required in the final row.

    Returns:
        Tuple containing:
            - aligned_df: The merged and filtered DataFrame.
            - stats: Dictionary with alignment statistics (total, dropped, rate).
    """
    logger.info("Starting data alignment process...")

    # Ensure species column exists and is normalized
    # Standardize column names for joining
    genomic_df = genomic_df.copy()
    metabolomic_df = metabolomic_df.copy()

    # Identify species column (assume 'species' or 'Species' based on common conventions)
    # If the provided DFs have different casing, we handle it here.
    # We expect the input DataFrames to have a 'species' column based on T016/T015 outputs.
    if 'species' not in genomic_df.columns:
        if 'Species' in genomic_df.columns:
            genomic_df.rename(columns={'Species': 'species'}, inplace=True)
        else:
            raise ValueError("Genomic DataFrame must contain a 'species' column.")

    if 'species' not in metabolomic_df.columns:
        if 'Species' in metabolomic_df.columns:
            metabolomic_df.rename(columns={'Species': 'species'}, inplace=True)
        else:
            raise ValueError("Metabolomic DataFrame must contain a 'species' column.")

    # Normalize species names to lowercase for robust matching
    genomic_df['species'] = genomic_df['species'].astype(str).str.lower().str.strip()
    metabolomic_df['species'] = metabolomic_df['species'].astype(str).str.lower().str.strip()

    # Filter by species_list if provided
    if species_list:
        species_set = set(s.lower().strip() for s in species_list)
        genomic_df = genomic_df[genomic_df['species'].isin(species_set)]
        metabolomic_df = metabolomic_df[metabolomic_df['species'].isin(species_set)]
        logger.info(f"Filtered data to {len(species_set)} specified species.")

    # Perform Inner Join
    # This automatically drops species that are not present in BOTH datasets
    aligned_df = pd.merge(
        genomic_df,
        metabolomic_df,
        on='species',
        how='inner',
        suffixes=('_genomic', '_metabolomic')
    )

    initial_count = len(aligned_df)
    dropped_species = []

    if initial_count == 0:
        logger.warning("No species found in both genomic and metabolomic datasets.")
        return aligned_df, {
            "total_input_genomic": len(genomic_df),
            "total_input_metabolomic": len(metabolomic_df),
            "aligned_count": 0,
            "dropped_count": 0,
            "alignment_rate": 0.0
        }

    # Identify rows with missing values (NaN)
    # We drop rows where any feature column (excluding 'species') is NaN
    feature_cols = [col for col in aligned_df.columns if col != 'species']
    
    # Log initial missing value counts per column
    missing_counts = aligned_df[feature_cols].isna().sum()
    cols_with_missing = missing_counts[missing_counts > 0]
    
    if len(cols_with_missing) > 0:
        logger.warning(f"Found missing values in {len(cols_with_missing)} columns before row filtering.")
        for col, count in cols_with_missing.items():
            logger.warning(f"  - {col}: {count} missing values")

    # Drop rows with any missing values in feature columns
    # Use subset to ignore the 'species' column for NaN checking
    mask = aligned_df[feature_cols].notna().all(axis=1)
    aligned_df = aligned_df[mask]
    
    final_count = len(aligned_df)
    dropped_count = initial_count - final_count

    if dropped_count > 0:
        dropped_indices = aligned_df.index[~mask] # This is wrong logic for dropped indices, let's fix
        # Correct way to get dropped species names:
        full_df = aligned_df.copy() # We lost the dropped rows. Let's re-calculate.
        
        # Re-do the drop logic to capture names
        temp_df = pd.merge(
            genomic_df,
            metabolomic_df,
            on='species',
            how='inner'
        )
        temp_mask = temp_df[feature_cols].notna().all(axis=1)
        dropped_rows = temp_df[~temp_mask]
        dropped_species = dropped_rows['species'].tolist()
        
        for sp in dropped_species[:10]: # Log first 10
            logger.warning(f"Dropped species '{sp}' due to missing data in one or more feature columns.")
        if len(dropped_species) > 10:
            logger.warning(f"  ... and {len(dropped_species) - 10} more species.")

    # Apply min_features filter (optional, though inner join + dropna usually suffices)
    if min_features > 1:
        valid_row_count = aligned_df[feature_cols].notna().sum(axis=1)
        aligned_df = aligned_df[valid_row_count >= min_features]
        final_count = len(aligned_df)

    alignment_rate = (final_count / initial_count * 100) if initial_count > 0 else 0.0

    stats = {
        "total_input_genomic": len(genomic_df),
        "total_input_metabolomic": len(metabolomic_df),
        "aligned_count_initial": initial_count,
        "dropped_count": dropped_count,
        "aligned_count_final": final_count,
        "alignment_rate": alignment_rate,
        "dropped_species_sample": dropped_species[:5]
    }

    logger.info(f"Alignment complete. {final_count} species aligned ({alignment_rate:.1f}% of merged data).")

    return aligned_df, stats


def save_aligned_matrix(
    df: pd.DataFrame,
    output_path: str,
    index: bool = True
) -> None:
    """
    Save the aligned DataFrame to a CSV file.

    Args:
        df: The aligned DataFrame to save.
        output_path: Path to the output CSV file.
        index: Whether to save the index.
    """
    # Ensure directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=index)
    logger.info(f"Saved aligned matrix to {output_path}")


def main():
    """
    Main entry point for the alignment script.
    Reads processed genomic and metabolomic data, aligns them, and saves the result.
    """
    # Get configuration paths
    data_path = get_data_path()
    processed_path = Path(data_path) / "processed"
    
    # Define expected input files (based on previous tasks T015/T016 outputs)
    # Assuming T016 produced harmonized metabolites and T015 produced BGC mappings
    # We look for the specific files generated by the pipeline steps.
    # If these files don't exist, the script will fail loudly as per requirements.
    genomic_file = processed_path / "bgc_matrix.csv" 
    metabolomic_file = processed_path / "harmonized_metabolites.csv"
    output_file = processed_path / "aligned_matrix.csv"

    # Check if input files exist
    if not genomic_file.exists():
        logger.error(f"Input genomic file not found: {genomic_file}")
        logger.error("Please ensure T014 (BGC extraction) has been run.")
        return
    
    if not metabolomic_file.exists():
        logger.error(f"Input metabolomic file not found: {metabolomic_file}")
        logger.error("Please ensure T016 (Metabolite harmonization) has been run.")
        return

    # Load data
    logger.info(f"Loading genomic data from {genomic_file}")
    genomic_df = pd.read_csv(genomic_file)

    logger.info(f"Loading metabolomic data from {metabolomic_file}")
    metabolomic_df = pd.read_csv(metabolomic_file)

    # Get species list from config if needed (optional filter)
    species_list = get_species_list()

    # Perform alignment
    aligned_df, stats = align_data(
        genomic_df,
        metabolomic_df,
        species_list=species_list
    )

    # Save results
    save_aligned_matrix(aligned_df, output_file)

    # Log final stats
    logger.info(f"Alignment Statistics: {stats}")


if __name__ == "__main__":
    main()
