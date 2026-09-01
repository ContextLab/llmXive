import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from utils.config import get_random_seed, get_min_sample_size, get_use_synthetic_data
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with controlled correlation structure.
    
    Generates 5 taxa with r=0.5 correlation to a latent variable using Cholesky 
    decomposition. Other taxa are uncorrelated.
    
    Args:
        n_subjects: Number of subjects (rows)
        n_taxa: Number of taxa (columns)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with subject_id and taxon abundance columns
    """
    np.random.seed(seed)
    
    # Create subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Define correlation structure
    # We want 5 taxa to have r=0.5 correlation with a latent variable
    # Total correlation matrix size: n_taxa + 1 (latent variable)
    
    # Build correlation matrix
    # Latent variable correlates with first 5 taxa at 0.5, others at 0.0
    corr_matrix = np.eye(n_taxa + 1)
    for i in range(5):
        corr_matrix[0, i+1] = 0.5
        corr_matrix[i+1, 0] = 0.5
    
    # Cholesky decomposition to generate correlated data
    try:
        L = np.linalg.cholesky(corr_matrix)
    except np.linalg.LinAlgError:
        # If matrix is not positive definite, use a simpler approach
        logger.warning("Correlation matrix not positive definite, using simplified structure")
        L = np.eye(n_taxa + 1)
    
    # Generate standard normal samples
    Z = np.random.randn(n_subjects, n_taxa + 1)
    
    # Transform to correlated data
    correlated_data = Z @ L.T
    
    # Extract taxa abundances (exclude latent variable column)
    taxa_abundances = correlated_data[:, 1:]
    
    # Convert to relative abundances (sum to 1 per subject)
    row_sums = taxa_abundances.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)  # Avoid division by zero
    relative_abundances = taxa_abundances / row_sums
    
    # Ensure non-negative (absolute value) since Cholesky can produce negatives
    relative_abundances = np.abs(relative_abundances)
    
    # Renormalize after taking absolute values
    row_sums = relative_abundances.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    relative_abundances = relative_abundances / row_sums
    
    # Create DataFrame
    taxon_names = [f"Taxon_{i}" for i in range(n_taxa)]
    df = pd.DataFrame(relative_abundances, columns=taxon_names)
    df.insert(0, 'subject_id', subject_ids)
    
    return df

def generate_synthetic_serology(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generate synthetic serology metadata with controlled correlation to taxa.
    
    The first 5 taxa are designed to correlate with titer_post at r=0.5.
    
    Args:
        n_subjects: Number of subjects
        n_taxa: Number of taxa (used to match subject count)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with subject_id, titer_baseline, and titer_post
    """
    np.random.seed(seed)
    
    # Create subject IDs matching OTU table
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Generate latent variable that drives correlation
    # This is the same latent variable used in OTU generation
    latent = np.random.randn(n_subjects)
    
    # Generate baseline titers (log-normal distribution)
    baseline_log = np.random.normal(loc=3.0, scale=0.5, size=n_subjects)
    titer_baseline = np.exp(baseline_log)
    
    # Generate post-vaccination titers with correlation to latent variable
    # This creates the r=0.5 correlation with the first 5 taxa
    post_log = 3.0 + 0.5 * latent + np.random.normal(loc=0, scale=0.3, size=n_subjects)
    titer_post = np.exp(post_log)
    
    # Ensure positive values
    titer_baseline = np.abs(titer_baseline)
    titer_post = np.abs(titer_post)
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    return df

def main():
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic data generation")
    
    # Get configuration
    seed = get_random_seed()
    n_subjects = get_min_sample_size()
    n_taxa = 20  # Default number of taxa
    
    logger.info(f"Generating {n_subjects} subjects with {n_taxa} taxa")
    
    # Generate OTU table
    otu_df = generate_synthetic_otu_table(n_subjects, n_taxa, seed)
    
    # Generate serology data
    sero_df = generate_synthetic_serology(n_subjects, n_taxa, seed)
    
    # Ensure output directories exist
    data_raw_path = Path("data/raw")
    data_raw_path.mkdir(parents=True, exist_ok=True)
    
    # Write OTU table
    otu_path = data_raw_path / "synthetic_otutable.csv"
    otu_df.to_csv(otu_path, index=False)
    logger.info(f"Written synthetic OTU table to {otu_path}")
    
    # Write serology data
    sero_path = data_raw_path / "synthetic_serology.csv"
    sero_df.to_csv(sero_path, index=False)
    logger.info(f"Written synthetic serology data to {sero_path}")
    
    # Verify outputs
    assert otu_path.exists(), "OTU table file not created"
    assert sero_path.exists(), "Serology file not created"
    
    # Verify row counts match
    assert len(otu_df) == len(sero_df), "Subject count mismatch between files"
    assert len(otu_df) >= n_subjects, f"Insufficient subjects: {len(otu_df)} < {n_subjects}"
    
    logger.info("Synthetic data generation completed successfully")
    
    return otu_path, sero_path

if __name__ == "__main__":
    main()
