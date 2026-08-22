"""
Data generation module for synthetic datasets and matrices.

This module handles the creation of synthetic genomic features,
drought tolerance labels, and phylogenetic distance matrices.
"""
import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog
import random

def generate_synthetic_phylogenetic_matrix(
    species_list: List[str],
    lower_bound: float = 0.1,
    upper_bound: float = 1.0,
    random_state: Optional[int] = 42
) -> np.ndarray:
    """
    Generate a synthetic phylogenetic distance matrix for the given species list.
    
    Logic:
    - Create N x N symmetric matrix (N = species count).
    - Diagonal elements are 0.
    - Off-diagonal elements are uniformly distributed between lower_bound and upper_bound.
    
    Args:
        species_list: List of species names (strings).
        lower_bound: Lower bound for off-diagonal values.
        upper_bound: Upper bound for off-diagonal values.
        random_state: Random seed for reproducibility.
        
    Returns:
        A symmetric numpy array representing the distance matrix.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    n = len(species_list)
    if n == 0:
        return np.array([]).reshape(0, 0)
        
    # Initialize matrix with zeros
    matrix = np.zeros((n, n))
    
    # Fill upper triangle (excluding diagonal) with random values
    for i in range(n):
        for j in range(i + 1, n):
            val = np.random.uniform(lower_bound, upper_bound)
            matrix[i, j] = val
            matrix[j, i] = val  # Symmetric
            
    return matrix

def generate_synthetic_genomic_features(
    species_list: List[str],
    gene_list: List[str],
    random_state: int = 42
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generate synthetic genomic features and drought tolerance labels.
    
    Logic:
    - Generate binary expression values (0 or 1) for each gene in the gene_list.
    - Label = 1 if sum(genomic_markers) >= 12, else 0.
    
    Args:
        species_list: List of species names.
        gene_list: List of gene names (e.g., ['NCED3', 'ABF3', ...]).
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (DataFrame with features, numpy array of labels).
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    n_species = len(species_list)
    n_genes = len(gene_list)
    
    if n_species == 0 or n_genes == 0:
        return pd.DataFrame(), np.array([])
        
    # Generate random binary expression values (0 or 1)
    # Probability of 1 is roughly 0.5 to ensure variation
    expression_data = np.random.binomial(1, 0.5, size=(n_species, n_genes))
    
    # Create DataFrame
    df = pd.DataFrame(expression_data, columns=gene_list)
    df.insert(0, 'species_id', species_list)
    
    # Calculate label: 1 if sum >= 12, else 0
    row_sums = df[gene_list].sum(axis=1)
    labels = (row_sums >= 12).astype(int).values
    
    return df, labels

def main():
    """
    Main entry point for generating synthetic data artifacts.
    Produces:
    - data/processed/synthetic_phylo_matrix.npy
    - data/processed/synthetic_genomics.csv
    """
    # Initialize logger
    logger = DataPipelineLog("generate")
    logger.info("Starting synthetic data generation...")
    
    # Load configuration
    config = get_config()
    validate_config(config)
    ensure_directories(config)
    
    # Extract species list from config
    species_list = config.get('species_list', [])
    if not species_list:
        # Fallback to a default list if not in config (for robustness)
        # This should ideally be populated by T006
        species_list = [f"Species_{i}" for i in range(100)]
        
    gene_list = config.get('gene_list', [
        'NCED3', 'ABF3', 'P5CS', 'DREB2A', 'ERF1', 'ABI5', 'RD29A', 
        'COR15A', 'LEA3', 'HSP70', 'SOD', 'APX1', 'CAT1', 'GPX1', 
        'MDHAR', 'DHAR', 'GSTU', 'ZAT12', 'WRKY33', 'MYB96'
    ])
    
    random_state = config.get('random_state', 42)
    phylo_lower = config.get('phylo_lower_bound', 0.1)
    phylo_upper = config.get('phylo_upper_bound', 1.0)
    
    # 1. Generate Phylogenetic Distance Matrix (T016)
    logger.info(f"Generating phylogenetic matrix for {len(species_list)} species...")
    phylo_matrix = generate_synthetic_phylogenetic_matrix(
        species_list=species_list,
        lower_bound=phylo_lower,
        upper_bound=phylo_upper,
        random_state=random_state
    )
    
    phylo_output_path = os.path.join(config['data_processed_dir'], 'synthetic_phylo_matrix.npy')
    np.save(phylo_output_path, phylo_matrix)
    logger.info(f"Saved phylogenetic matrix to {phylo_output_path}")
    
    # 2. Generate Synthetic Genomic Features (T012)
    logger.info(f"Generating synthetic genomic features for {len(gene_list)} genes...")
    genomics_df, labels = generate_synthetic_genomic_features(
        species_list=species_list,
        gene_list=gene_list,
        random_state=random_state
    )
    
    # Add label column to DataFrame for CSV output
    genomics_df['label'] = labels
    
    genomics_output_path = os.path.join(config['data_processed_dir'], 'synthetic_genomics.csv')
    genomics_df.to_csv(genomics_output_path, index=False)
    logger.info(f"Saved synthetic genomics data to {genomics_output_path}")
    
    logger.info("Synthetic data generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
