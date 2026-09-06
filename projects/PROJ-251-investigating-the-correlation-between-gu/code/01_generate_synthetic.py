import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List

# Import configuration helpers from the existing utils module
from utils.config import (
    get_use_synthetic_data,
    get_random_seed,
    get_num_synthetic_taxa,
    get_target_correlation,
    get_min_sample_size,
    get_raw_path,
    get_research_path
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_synthetic_otu_table(
    n_subjects: int,
    n_taxa: int,
    target_correlation: float,
    seed: int
) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with controlled correlation structure.
    
    Args:
        n_subjects: Number of subjects (rows)
        n_taxa: Number of taxa columns
        target_correlation: Target correlation between first N taxa and the response
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with columns: subject_id, taxon_0, taxon_1, ..., taxon_{N-1}
    """
    np.random.seed(seed)
    
    # Generate base abundances for all taxa (relative abundances summing to 1)
    # Use Dirichlet distribution to ensure valid compositional data
    alpha = np.ones(n_taxa) * 0.5  # Sparse distribution
    raw_abundances = np.random.dirichlet(alpha, size=n_subjects)
    
    # Create subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Create DataFrame
    df = pd.DataFrame(raw_abundances, columns=[f"taxon_{i}" for i in range(n_taxa)])
    df.insert(0, 'subject_id', subject_ids)
    
    logger.info(f"Generated OTU table with {n_subjects} subjects and {n_taxa} taxa")
    return df

def generate_synthetic_serology(
    otu_df: pd.DataFrame,
    target_correlation: float,
    n_taxa_correlated: int,
    seed: int
) -> pd.DataFrame:
    """
    Generate synthetic serology data with controlled correlation to specific taxa.
    
    Args:
        otu_df: The OTU table DataFrame
        target_correlation: Target correlation value
        n_taxa_correlated: Number of taxa that should correlate with titers
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with columns: subject_id, titer_baseline, titer_post
    """
    np.random.seed(seed)
    n_subjects = len(otu_df)
    
    # Extract correlated taxa columns
    correlated_taxa_cols = [f"taxon_{i}" for i in range(n_taxa_correlated)]
    correlated_data = otu_df[correlated_taxa_cols].values
    
    # Generate a latent response variable based on correlated taxa
    # Weighted sum of correlated taxa
    weights = np.ones(n_taxa_correlated) / n_taxa_correlated
    latent_response = correlated_data @ weights
    
    # Add noise to create the desired correlation strength
    # We scale the noise to achieve the target correlation
    signal_variance = target_correlation ** 2
    noise_variance = 1 - signal_variance
    
    if noise_variance < 0:
        noise_variance = 0.01  # Fallback for numerical stability
        
    noise = np.random.normal(0, np.sqrt(noise_variance), n_subjects)
    
    # Create log-transformed titer values (more natural for biological data)
    log_titer_post = latent_response + noise
    
    # Generate baseline titers (uncorrelated with microbiome)
    log_titer_baseline = np.random.normal(2.0, 0.5, n_subjects)
    
    # Convert back to linear scale (HAI titers are typically powers of 2)
    titer_post = np.exp(log_titer_post)
    titer_baseline = np.exp(log_titer_baseline)
    
    # Ensure positive values
    titer_post = np.maximum(titer_post, 1.0)
    titer_baseline = np.maximum(titer_baseline, 1.0)
    
    # Create DataFrame
    subject_ids = otu_df['subject_id'].values
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    logger.info(f"Generated serology data with target correlation {target_correlation:.2f}")
    return df

def main():
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic data generation (Task T011b)")
    
    # Check if synthetic data should be used
    use_synthetic = get_use_synthetic_data()
    if not use_synthetic:
        logger.info("Synthetic data generation skipped: USE_SYNTHETIC_DATA is False")
        return
    
    # Get configuration parameters
    seed = get_random_seed()
    n_taxa = get_num_synthetic_taxa()
    target_corr = get_target_correlation()
    n_subjects = get_min_sample_size()
    
    # Ensure we have enough taxa for the correlation structure
    if n_taxa < 1:
        n_taxa = 5
        logger.warning(f"NUM_SYNTHETIC_TAXA too low, setting to {n_taxa}")
    
    logger.info(f"Generating {n_subjects} subjects with {n_taxa} taxa (target corr: {target_corr})")
    
    # Generate OTU table
    otu_df = generate_synthetic_otu_table(
        n_subjects=n_subjects,
        n_taxa=n_taxa,
        target_correlation=target_corr,
        seed=seed
    )
    
    # Generate serology data
    serology_df = generate_synthetic_serology(
        otu_df=otu_df,
        target_correlation=target_corr,
        n_taxa_correlated=n_taxa,
        seed=seed
    )
    
    # Define output paths
    raw_path = get_raw_path()
    raw_path.mkdir(parents=True, exist_ok=True)
    
    otu_output = raw_path / "synthetic_otutable.csv"
    serology_output = raw_path / "synthetic_serology.csv"
    
    # Write outputs
    otu_df.to_csv(otu_output, index=False)
    serology_df.to_csv(serology_output, index=False)
    
    logger.info(f"Written synthetic OTU table to: {otu_output}")
    logger.info(f"Written synthetic serology to: {serology_output}")
    
    # Verify outputs
    assert otu_output.exists(), f"Failed to write {otu_output}"
    assert serology_output.exists(), f"Failed to write {serology_output}"
    
    logger.info("Synthetic data generation completed successfully")

if __name__ == "__main__":
    main()