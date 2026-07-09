"""
Module for calculating Alpha and Beta diversity metrics.

This module implements Shannon, Simpson (Alpha diversity) and Bray-Curtis 
(Beta diversity) calculations using real data from the processed cohort.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import biom
from skbio.diversity import alpha_diversity, beta_diversity
from skbio.diversity.alpha import shannon, simpson
from skbio.diversity.beta import braycurtis
from skbio import OrdinationResults
from skbio.stats.ordination import pcoa
from scipy.spatial.distance import pdist, squareform

from utils.logging_utils import get_logger
from utils.config import get_config

# Ensure the utils package can be imported if running as script
try:
    from .utils.logging_utils import get_logger
    from .utils.config import get_config
except ImportError:
    from utils.logging_utils import get_logger
    from utils.config import get_config

logger = get_logger(__name__)
config = get_config()

def load_biom_table(biom_path: str) -> biom.Table:
    """
    Load a BIOM table from disk.
    
    Args:
        biom_path: Path to the .biom file.
        
    Returns:
        biom.Table object.
    """
    if not os.path.exists(biom_path):
        raise FileNotFoundError(f"BIOM file not found: {biom_path}")
    
    logger.info(f"Loading BIOM table from {biom_path}")
    table = biom.load_table(biom_path)
    logger.info(f"Loaded BIOM table with shape: {table.shape}")
    return table

def load_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load participant metadata.
    
    Args:
        metadata_path: Path to the metadata CSV.
        
    Returns:
        DataFrame with participant metadata.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    logger.info(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    logger.info(f"Loaded metadata with {len(df)} rows")
    return df

def calculate_alpha_diversity(table: biom.Table, metric: str = 'shannon') -> pd.Series:
    """
    Calculate alpha diversity for all samples in the table.
    
    Args:
        table: BIOM table object.
        metric: Diversity metric ('shannon' or 'simpson').
        
    Returns:
        Series of diversity values indexed by sample ID.
    """
    logger.info(f"Calculating {metric} alpha diversity")
    
    # Convert BIOM table to dense matrix for skbio
    # Note: For very large datasets, sparse operations are preferred,
    # but skbio alpha_diversity expects a 2D array
    obs_matrix = table.matrix_data.toarray()
    sample_ids = table.ids(axis='sample')
    
    if metric == 'shannon':
        diversity_func = shannon
    elif metric == 'simpson':
        diversity_func = simpson
    else:
        raise ValueError(f"Unsupported alpha diversity metric: {metric}")
    
    # skbio alpha_diversity expects a list of counts per sample
    # We calculate for each sample (row in obs_matrix)
    results = []
    for i, sample_id in enumerate(sample_ids):
        counts = obs_matrix[i, :]
        # Filter out zero counts as skbio expects positive integers for some metrics
        # but shannon/simpson can handle zeros if handled correctly
        # skbio's shannon/simpson handle zeros fine
        val = diversity_func(counts)
        results.append((sample_id, val))
    
    return pd.Series(dict(results))

def calculate_beta_diversity(table: biom.Table, metric: str = 'braycurtis') -> Tuple[pd.DataFrame, List[str]]:
    """
    Calculate beta diversity matrix between all samples.
    
    Args:
        table: BIOM table object.
        metric: Distance metric ('braycurtis').
        
    Returns:
        Tuple of (distance_matrix_df, sample_ids_list).
    """
    logger.info(f"Calculating {metric} beta diversity")
    
    obs_matrix = table.matrix_data.toarray()
    sample_ids = table.ids(axis='sample')
    
    # Calculate pairwise distances
    distances = pdist(obs_matrix, metric=metric)
    square_dist = squareform(distances)
    
    # Create DataFrame
    dist_df = pd.DataFrame(square_dist, index=sample_ids, columns=sample_ids)
    
    return dist_df, sample_ids

def run_diversity_analysis(
    biom_path: str, 
    metadata_path: str, 
    output_dir: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main function to run diversity analysis and save results.
    
    Args:
        biom_path: Path to BIOM table.
        metadata_path: Path to metadata CSV.
        output_dir: Directory to save results.
        
    Returns:
        Tuple of (alpha_diversity_df, beta_diversity_df).
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    table = load_biom_table(biom_path)
    metadata = load_metadata(metadata_path)
    
    # Calculate Alpha Diversity
    shannon_div = calculate_alpha_diversity(table, 'shannon')
    simpson_div = calculate_alpha_diversity(table, 'simpson')
    
    # Merge alpha diversity with metadata
    alpha_df = pd.DataFrame({
        'sample_id': shannon_div.index,
        'shannon': shannon_div.values,
        'simpson': simpson_div.values
    })
    
    # Merge with participant metadata if sample_id matches participant_id
    # Assuming sample_id in BIOM table corresponds to participant_id in metadata
    merged_alpha = pd.merge(
        alpha_df, 
        metadata, 
        left_on='sample_id', 
        right_on='participant_id', 
        how='inner'
    )
    
    # Save Alpha Diversity results
    alpha_output_path = output_path / 'alpha_diversity.csv'
    merged_alpha.to_csv(alpha_output_path, index=False)
    logger.info(f"Saved alpha diversity to {alpha_output_path}")
    
    # Calculate Beta Diversity
    beta_dist_df, sample_ids = calculate_beta_diversity(table, 'braycurtis')
    
    # Save Beta Diversity results (distance matrix)
    beta_output_path = output_path / 'beta_diversity_distance_matrix.csv'
    beta_dist_df.to_csv(beta_output_path)
    logger.info(f"Saved beta diversity matrix to {beta_output_path}")
    
    # Generate PCoA for visualization (optional but useful)
    # We perform PCoA on the distance matrix
    from skbio.stats.ordination import pcoa
    from skbio import DistanceMatrix
    
    dm = DistanceMatrix(beta_dist_df.values, ids=sample_ids)
    pcoa_results = pcoa(dm)
    
    # Extract PCoA coordinates
    pcoa_df = pd.DataFrame(
        pcoa_results.samples, 
        columns=[f'PC{i+1}' for i in range(pcoa_results.samples.shape[1])]
    )
    pcoa_df.insert(0, 'sample_id', sample_ids)
    
    # Merge with metadata
    pcoa_merged = pd.merge(
        pcoa_df, 
        metadata, 
        left_on='sample_id', 
        right_on='participant_id', 
        how='inner'
    )
    
    pcoa_output_path = output_path / 'pcoa_coordinates.csv'
    pcoa_merged.to_csv(pcoa_output_path, index=False)
    logger.info(f"Saved PCoA coordinates to {pcoa_output_path}")
    
    return merged_alpha, beta_dist_df

def main():
    """Entry point for diversity analysis."""
    config = get_config()
    
    # Paths based on project structure
    # Assuming the cohort has been processed and saved by ingestion.py
    # We look for the processed cohort in data/processed/
    data_dir = Path(config.get('data_dir', 'data'))
    biom_file = data_dir / 'processed' / 'cohort_merged.biom'
    metadata_file = data_dir / 'processed' / 'cohort_merged.csv'
    output_dir = data_dir / 'outputs'
    
    if not biom_file.exists():
        logger.error(f"BIOM file not found at {biom_file}. Please run ingestion first.")
        return
    
    if not metadata_file.exists():
        logger.error(f"Metadata file not found at {metadata_file}. Please run ingestion first.")
        return
    
    logger.info("Starting diversity analysis...")
    alpha_df, beta_df = run_diversity_analysis(
        biom_path=str(biom_file),
        metadata_path=str(metadata_file),
        output_dir=str(output_dir)
    )
    
    logger.info(f"Diversity analysis complete. Results saved to {output_dir}")
    logger.info(f"Alpha diversity shape: {alpha_df.shape}")
    logger.info(f"Beta diversity matrix shape: {beta_df.shape}")

if __name__ == '__main__':
    main()
