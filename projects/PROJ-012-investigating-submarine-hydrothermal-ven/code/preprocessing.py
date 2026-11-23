"""
Preprocessing module for hydrothermal vent microbial data.

Handles OTU table loading, rarefaction, and alpha diversity calculation.
"""
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.stats import entropy
import json

# Configure logging
logger = logging.getLogger(__name__)

def load_otu_table(file_path: str) -> pd.DataFrame:
    """
    Load an OTU/ASV table from a CSV file.
    
    Expected format:
    - First column: sample_id
    - Subsequent columns: OTU/ASV IDs
    - Values: counts
    
    Args:
        file_path: Path to the OTU table CSV file.
        
    Returns:
        DataFrame with sample_id as index and OTU counts as columns.
    """
    logger.info(f"Loading OTU table from {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"OTU table file not found: {file_path}")
        
    df = pd.read_csv(file_path, index_col=0)
    logger.info(f"Loaded OTU table with {len(df)} samples and {len(df.columns)} OTUs")
    return df

def rarefy_otu_table(otu_table: pd.DataFrame, depth: int, seed: int = 42) -> pd.DataFrame:
    """
    Rarefy an OTU table to a specified sequencing depth.
    
    For each sample, randomly subsamples reads to the specified depth.
    If a sample has fewer reads than the depth, it is excluded.
    
    Args:
        otu_table: DataFrame with sample_id as index and OTU counts.
        depth: Target sequencing depth for rarefaction.
        seed: Random seed for reproducibility.
        
    Returns:
        Rarefied DataFrame with same structure as input.
    """
    logger.info(f"Rarefying OTU table to depth {depth} with seed {seed}")
    random.seed(seed)
    np.random.seed(seed)
    
    rarefied_data = {}
    excluded_samples = []
    
    for sample_id, row in otu_table.iterrows():
        total_reads = row.sum()
        
        if total_reads < depth:
            excluded_samples.append(sample_id)
            logger.debug(f"Sample {sample_id} has {total_reads} reads (< {depth}), excluding")
            continue
        
        # Create a list of OTUs weighted by their counts
        otu_ids = row.index.tolist()
        counts = row.values.tolist()
        
        # Perform multinomial sampling to get counts at the target depth
        # We use numpy's multinomial for efficiency
        rarefied_counts = np.random.multinomial(depth, np.array(counts) / total_reads)
        
        rarefied_data[sample_id] = dict(zip(otu_ids, rarefied_counts))
    
    if excluded_samples:
        logger.warning(f"Excluded {len(excluded_samples)} samples due to low read count: {excluded_samples[:5]}...")
    
    rarefied_df = pd.DataFrame(rarefied_data).T
    
    # Ensure all OTU columns are present (fill missing with 0)
    all_otus = set(otu_table.columns)
    for col in all_otus:
        if col not in rarefied_df.columns:
            rarefied_df[col] = 0
    
    rarefied_df = rarefied_df[sorted(all_otus)]
    
    logger.info(f"Rarefaction complete. {len(rarefied_df)} samples retained.")
    return rarefied_df

def run_rarefaction_pipeline(otu_table_path: str, output_dir: str, depths: List[int] = [5000, 10000, 20000], seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Run rarefaction at multiple depths and save results.
    
    Args:
        otu_table_path: Path to the input OTU table.
        output_dir: Directory to save rarefied tables.
        depths: List of depths to rarefy to.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary mapping depth to rarefied DataFrame.
    """
    logger.info(f"Starting rarefaction pipeline for depths {depths}")
    
    otu_table = load_otu_table(otu_table_path)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    rarefied_tables = {}
    
    for depth in depths:
        logger.info(f"Rarefying to depth {depth}")
        rarefied_df = rarefy_otu_table(otu_table, depth, seed)
        
        output_file = output_path / f"rarefied_otu_table_depth_{depth}.csv"
        rarefied_df.to_csv(output_file)
        logger.info(f"Saved rarefied table to {output_file}")
        
        rarefied_tables[depth] = rarefied_df
    
    return rarefied_tables

def calculate_shannon_diversity(rarefied_df: pd.DataFrame) -> pd.Series:
    """
    Calculate Shannon diversity index for each sample.
    
    Shannon index: H' = -sum(p_i * ln(p_i))
    where p_i is the proportion of reads belonging to OTU i.
    
    Args:
        rarefied_df: Rarefied OTU table (samples x OTUs).
        
    Returns:
        Series of Shannon diversity indices indexed by sample_id.
    """
    logger.info("Calculating Shannon diversity indices")
    
    # Filter out samples with zero total reads (should not happen after rarefaction)
    valid_samples = rarefied_df[rarefied_df.sum(axis=1) > 0]
    
    if len(valid_samples) == 0:
        logger.warning("No valid samples for Shannon diversity calculation")
        return pd.Series(dtype=float)
    
    # Calculate proportions
    proportions = valid_samples.div(valid_samples.sum(axis=1), axis=0)
    
    # Calculate Shannon index: -sum(p * ln(p))
    # Handle log(0) by setting 0 * ln(0) = 0
    shannon_indices = -1 * (proportions * np.log(proportions + 1e-10)).sum(axis=1)
    
    # Replace any NaN or infinite values with 0 (should not happen)
    shannon_indices = shannon_indices.replace([np.inf, -np.inf], 0)
    
    logger.info(f"Calculated Shannon diversity for {len(shannon_indices)} samples")
    return shannon_indices

def calculate_simpson_diversity(rarefied_df: pd.DataFrame) -> pd.Series:
    """
    Calculate Simpson diversity index (1 - D) for each sample.
    
    Simpson index: D = sum(p_i^2)
    Simpson diversity: 1 - D = 1 - sum(p_i^2)
    
    This represents the probability that two randomly selected individuals
    belong to different species.
    
    Args:
        rarefied_df: Rarefied OTU table (samples x OTUs).
        
    Returns:
        Series of Simpson diversity indices indexed by sample_id.
    """
    logger.info("Calculating Simpson diversity indices")
    
    # Filter out samples with zero total reads
    valid_samples = rarefied_df[rarefied_df.sum(axis=1) > 0]
    
    if len(valid_samples) == 0:
        logger.warning("No valid samples for Simpson diversity calculation")
        return pd.Series(dtype=float)
    
    # Calculate proportions
    proportions = valid_samples.div(valid_samples.sum(axis=1), axis=0)
    
    # Calculate Simpson index: sum(p_i^2)
    simpson_d = (proportions ** 2).sum(axis=1)
    
    # Simpson diversity: 1 - D
    simpson_diversity = 1 - simpson_d
    
    # Replace any NaN or infinite values with 0
    simpson_diversity = simpson_diversity.replace([np.inf, -np.inf], 0)
    
    logger.info(f"Calculated Simpson diversity for {len(simpson_diversity)} samples")
    return simpson_diversity

def calculate_alpha_diversity(rarefied_df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Calculate alpha diversity indices (Shannon and Simpson) for each sample.
    
    Args:
        rarefied_df: Rarefied OTU table (samples x OTUs).
        output_path: Path to save the diversity results CSV.
        
    Returns:
        DataFrame with sample_id, Shannon, and Simpson indices.
    """
    logger.info(f"Calculating alpha diversity for {len(rarefied_df)} samples")
    
    shannon = calculate_shannon_diversity(rarefied_df)
    simpson = calculate_simpson_diversity(rarefied_df)
    
    # Create results DataFrame
    diversity_df = pd.DataFrame({
        'sample_id': shannon.index,
        'shannon': shannon.values,
        'simpson': simpson.values
    })
    
    # Ensure sample_id is the index for consistency
    diversity_df.set_index('sample_id', inplace=True)
    
    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    diversity_df.to_csv(output_file)
    
    logger.info(f"Saved alpha diversity results to {output_file}")
    logger.info(f"Results: {len(diversity_df)} samples, "
               f"Shannon range: [{diversity_df['shannon'].min():.4f}, {diversity_df['shannon'].max():.4f}], "
               f"Simpson range: [{diversity_df['simpson'].min():.4f}, {diversity_df['simpson'].max():.4f}]")
    
    return diversity_df

def main():
    """
    Main entry point for alpha diversity calculation.
    
    This function:
    1. Loads the rarefied OTU table from data/processed/
    2. Calculates Shannon and Simpson diversity indices
    3. Saves results to data/processed/alpha_diversity_results.csv
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/preprocessing.log')
        ]
    )
    
    logger.info("Starting alpha diversity calculation pipeline")
    
    # Define paths
    # Assuming the rarefied OTU table is in data/processed/
    # We'll use the most recent rarefaction depth (20000) as default
    rarefied_otu_path = "data/processed/rarefied_otu_table_depth_20000.csv"
    output_path = "data/processed/alpha_diversity_results.csv"
    
    if not os.path.exists(rarefied_otu_path):
        logger.error(f"Rarefied OTU table not found: {rarefied_otu_path}")
        logger.error("Please run the rarefaction pipeline first (T019)")
        raise FileNotFoundError(f"Rarefied OTU table not found: {rarefied_otu_path}")
    
    # Load rarefied OTU table
    rarefied_df = load_otu_table(rarefied_otu_path)
    
    # Calculate alpha diversity
    diversity_df = calculate_alpha_diversity(rarefied_df, output_path)
    
    logger.info("Alpha diversity calculation completed successfully")
    
    return diversity_df

if __name__ == "__main__":
    main()