"""
Synthetic Data Generator for Gut Microbiome - Influenza Vaccination Study.

This module generates synthetic OTU tables and serology metadata when real data
is unavailable (config.USE_SYNTHETIC_DATA == True).

IMPORTANT: Synthetic data is used ONLY for CI/Code Correctness validation
and explicitly NOT for biological claims.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List
import random

# Import config utilities from the existing project structure
from utils.config import get_random_seed, get_use_synthetic_data, get_raw_path, get_min_sample_size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants for synthetic data generation
DEFAULT_N_SUBJECTS = 50
DEFAULT_TAXA_COUNT = 20
RANDOM_SEED = 42
CORRELATION_STRENGTH = 0.5
# Define 5 taxa that will have controlled correlation with log_titer
SIGNAL_TAXA_INDICES = [0, 1, 2, 3, 4]

def generate_synthetic_otu_table(n_subjects: int = DEFAULT_N_SUBJECTS, 
                                 n_taxa: int = DEFAULT_TAXA_COUNT, 
                                 seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with relative abundances.
    
    Args:
        n_subjects: Number of subjects to generate.
        n_taxa: Number of taxa (OTUs) to include.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with columns: subject_id, taxon_0, taxon_1, ..., taxon_n
    """
    logger.info(f"Generating synthetic OTU table for {n_subjects} subjects and {n_taxa} taxa")
    
    # Set seeds for reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    # Generate subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Generate base abundances using a Dirichlet distribution to ensure they sum to 1
    # This creates realistic compositional data
    alpha = np.ones(n_taxa)
    abundances = np.random.dirichlet(alpha, size=n_subjects)
    
    # Introduce controlled correlation for signal taxa
    # We'll make these taxa slightly correlated with a latent variable that will 
    # also influence serology
    latent_variable = np.random.normal(0, 1, n_subjects)
    
    for idx in SIGNAL_TAXA_INDICES:
        if idx < n_taxa:
            # Add a correlation component
            abundances[:, idx] = abundances[:, idx] * (1 + CORRELATION_STRENGTH * latent_variable)
            # Re-normalize to ensure they remain relative abundances
            row_sums = abundances.sum(axis=1, keepdims=True)
            abundances = abundances / row_sums
    
    # Create taxon column names
    taxon_columns = [f"taxon_{i}" for i in range(n_taxa)]
    
    # Create DataFrame
    df = pd.DataFrame(abundances, columns=taxon_columns)
    df.insert(0, 'subject_id', subject_ids)
    
    logger.info(f"Generated OTU table with shape: {df.shape}")
    logger.info(f"Sample subject IDs: {subject_ids[:5]}")
    
    return df

def generate_synthetic_serology(n_subjects: int = DEFAULT_N_SUBJECTS,
                                seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate synthetic serology metadata with titers.
    
    Creates baseline and post-vaccination titers with controlled correlation
    to the signal taxa defined in generate_synthetic_otu_table.
    
    Args:
        n_subjects: Number of subjects to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with columns: subject_id, titer_baseline, titer_post
    """
    logger.info(f"Generating synthetic serology data for {n_subjects} subjects")
    
    # Set seeds for reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    # Generate subject IDs (must match OTU table)
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Generate baseline titers (log10 scale, typically 1.5 - 3.0)
    baseline_titers = np.random.normal(2.0, 0.5, n_subjects)
    baseline_titers = np.clip(baseline_titers, 1.0, 3.5)  # Ensure reasonable range
    
    # Generate post-vaccination titers with correlation to latent variable
    # The latent variable is the same one used in OTU generation to create correlation
    latent_variable = np.random.normal(0, 1, n_subjects)
    
    # Post-titer = baseline + response (correlated with latent variable)
    response = 0.5 * latent_variable + np.random.normal(0, 0.3, n_subjects)
    post_titers = baseline_titers + response
    
    # Ensure post-titers are positive and reasonable
    post_titers = np.clip(post_titers, 1.0, 4.5)
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': baseline_titers,
        'titer_post': post_titers
    })
    
    logger.info(f"Generated serology data with shape: {df.shape}")
    logger.info(f"Baseline titer stats: mean={baseline_titers.mean():.2f}, std={baseline_titers.std():.2f}")
    logger.info(f"Post titer stats: mean={post_titers.mean():.2f}, std={post_titers.std():.2f}")
    
    return df

def main():
    """
    Main entry point for synthetic data generation.
    
    This function:
    1. Checks if USE_SYNTHETIC_DATA is True
    2. Generates OTU table and serology metadata
    3. Saves them to data/raw/
    """
    logger.info("Starting synthetic data generation process")
    
    # Check if synthetic data generation is enabled
    if not get_use_synthetic_data():
        logger.warning("USE_SYNTHETIC_DATA is False. Skipping synthetic data generation.")
        logger.info("This script should only run when USE_SYNTHETIC_DATA is True.")
        return
    
    # Ensure output directory exists
    raw_path = get_raw_path()
    raw_path.mkdir(parents=True, exist_ok=True)
    
    # Get parameters from config
    seed = get_random_seed()
    n_subjects = get_min_sample_size()
    
    logger.info(f"Configuration: seed={seed}, n_subjects={n_subjects}")
    
    # Generate synthetic OTU table
    otu_df = generate_synthetic_otu_table(n_subjects=n_subjects, seed=seed)
    otu_path = raw_path / "synthetic_otutable.csv"
    otu_df.to_csv(otu_path, index=False)
    logger.info(f"Saved synthetic OTU table to {otu_path}")
    
    # Generate synthetic serology
    sero_df = generate_synthetic_serology(n_subjects=n_subjects, seed=seed)
    sero_path = raw_path / "synthetic_serology.csv"
    sero_df.to_csv(sero_path, index=False)
    logger.info(f"Saved synthetic serology to {sero_path}")
    
    # Verify files exist and have content
    if otu_path.exists() and sero_path.exists():
        logger.info("SUCCESS: Synthetic data files generated and saved.")
        logger.info(f"OTU table: {otu_path.stat().st_size} bytes, {len(otu_df)} rows")
        logger.info(f"Serology: {sero_path.stat().st_size} bytes, {len(sero_df)} rows")
    else:
        logger.error("FAILED: One or more synthetic data files were not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
