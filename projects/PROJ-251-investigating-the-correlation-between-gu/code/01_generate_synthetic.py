import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_use_synthetic_data, get_random_seed, get_min_sample_size, get_lod_value
from utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with relative abundances.
    
    - Taxa abundances sum to a constant (10000 reads) per subject.
    - Introduces controlled correlations: 5 specific taxa correlate with a hidden 'response' variable.
    - Uses Cholesky decomposition to induce correlation structure.
    """
    np.random.seed(seed)
    
    # Generate base abundances (Log-normal distribution typical for microbiome)
    # Mean and std for log-space
    mu = 2.0
    sigma = 1.5
    
    # Create a correlation matrix
    # We want 5 taxa to be correlated with a latent variable, and others independent
    # Let's create a correlation matrix where the first 5 taxa have a correlation of 0.5 with each other
    # and 0.0 with the rest.
    
    corr_matrix = np.eye(n_taxa)
    target_indices = list(range(5)) # First 5 taxa are the 'signal'
    
    for i in target_indices:
        for j in target_indices:
            if i != j:
                corr_matrix[i, j] = 0.5
    
    # Ensure positive semi-definite (cholesky might fail if not)
    try:
        L = np.linalg.cholesky(corr_matrix)
    except np.linalg.LinAlgError:
        logger.warning("Correlation matrix not positive definite. Using identity.")
        L = np.eye(n_taxa)
    
    # Generate correlated standard normal variables
    Z = np.random.standard_normal((n_subjects, n_taxa))
    correlated_Z = Z @ L.T
    
    # Convert to log-normal abundances
    abundances_log = correlated_Z * sigma + mu
    abundances = np.exp(abundances_log)
    
    # Normalize to sum to a constant (e.g., 10,000 reads)
    row_sums = abundances.sum(axis=1, keepdims=True)
    relative_abundances = (abundances / row_sums) * 10000
    
    # Create column names
    taxon_names = [f"Taxon_{i:03d}" for i in range(n_taxa)]
    
    df = pd.DataFrame(relative_abundances, columns=taxon_names)
    df.insert(0, 'subject_id', [f"SUBJ_{i:04d}" for i in range(n_subjects)])
    
    return df

def generate_synthetic_serology(n_subjects: int, otu_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic serology data with controlled correlations to specific taxa.
    
    - Creates 'titer_baseline' and 'titer_post'.
    - Correlates 'titer_post' (and thus log_titer) with the first 5 taxa from the OTU table.
    - Introduces some noise.
    """
    np.random.seed(seed + 1) # Different seed for serology to avoid exact reproducibility if not desired, but fixed for consistency
    
    subject_ids = otu_df['subject_id']
    n = len(subject_ids)
    
    # Extract the 'signal' taxa (first 5)
    signal_taxa = otu_df.columns[1:6] # Skip subject_id
    
    # Create a latent response variable based on the signal taxa
    # Normalize signal taxa to 0-1 range roughly for weighting
    signal_data = otu_df[signal_taxa].values
    signal_mean = signal_data.mean(axis=1)
    
    # Latent variable: weighted sum of signal taxa + noise
    latent_response = signal_mean * 0.5 + np.random.normal(0, 0.5, n)
    
    # Generate baseline titers (log-normal)
    baseline_mu = 2.0
    baseline_sigma = 0.5
    titer_baseline = np.exp(np.random.normal(baseline_mu, baseline_sigma, n))
    
    # Generate post-vaccination titers
    # Stronger response for higher latent_response
    # Base increase + effect from latent_response
    titer_post = titer_baseline * (2.0 + latent_response * 2.0) + np.random.normal(0, 10.0, n)
    
    # Ensure positive
    titer_post = np.maximum(titer_post, 1.0)
    
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    return df

def main():
    """
    Main entry point to generate synthetic datasets.
    Checks config.USE_SYNTHETIC_DATA before proceeding.
    """
    if not get_use_synthetic_data():
        logger.info("Config indicates real data is available. Skipping synthetic generation.")
        return

    logger.info("Generating synthetic dataset as per config.USE_SYNTHETIC_DATA=True")
    
    n_subjects = get_min_sample_size()
    seed = get_random_seed()
    n_taxa = 50 # Default number of taxa for synthetic data
    
    logger.info(f"Generating {n_subjects} subjects with {n_taxa} taxa.")
    
    # Generate OTU Table
    otu_df = generate_synthetic_otu_table(n_subjects, n_taxa, seed)
    
    # Generate Serology
    sero_df = generate_synthetic_serology(n_subjects, otu_df, seed)
    
    # Ensure output directories exist
    data_raw_path = Path("data/raw")
    data_raw_path.mkdir(parents=True, exist_ok=True)
    
    otu_path = data_raw_path / "synthetic_otutable.csv"
    sero_path = data_raw_path / "synthetic_serology.csv"
    
    otu_df.to_csv(otu_path, index=False)
    sero_df.to_csv(sero_path, index=False)
    
    logger.info(f"Successfully wrote synthetic OTU table to {otu_path}")
    logger.info(f"Successfully wrote synthetic serology to {sero_path}")
    
    # Verify row counts
    assert len(otu_df) == n_subjects, "OTU table row count mismatch"
    assert len(sero_df) == n_subjects, "Serology row count mismatch"
    assert list(otu_df['subject_id']) == list(sero_df['subject_id']), "Subject ID mismatch"

if __name__ == "__main__":
    main()
