import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List

# Import config utilities from the existing API surface
from utils.config import (
    get_num_synthetic_taxa,
    get_target_correlation,
    get_random_seed,
    get_min_sample_size,
    get_use_synthetic_data,
    get_raw_path,
    get_research_path
)

logger = logging.getLogger(__name__)

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with relative abundances.
    
    Args:
        n_subjects: Number of subjects (rows).
        n_taxa: Number of taxa (columns).
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with columns: subject_id, taxon_0, taxon_1, ..., taxon_{n_taxa-1}
    """
    np.random.seed(seed)
    
    # Generate raw counts from a Dirichlet distribution to simulate compositional data
    # Concentration parameter alpha < 1 creates sparse data (many zeros), typical of microbiome
    alpha = 0.5
    raw_abundances = np.random.dirichlet(np.ones(n_taxa) * alpha, size=n_subjects)
    
    # Create subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Create column names
    taxon_columns = [f"taxon_{i}" for i in range(n_taxa)]
    
    # Construct DataFrame
    df = pd.DataFrame(raw_abundances, columns=taxon_columns)
    df.insert(0, 'subject_id', subject_ids)
    
    # Ensure relative abundances sum to 1 (floating point tolerance)
    row_sums = df[taxon_columns].sum(axis=1)
    df[taxon_columns] = df[taxon_columns] / row_sums.values[:, np.newaxis]
    
    return df

def generate_synthetic_serology(
    n_subjects: int, 
    n_taxa: int, 
    target_correlation: float, 
    taxa_indices: List[int], 
    seed: int
) -> pd.DataFrame:
    """
    Generate synthetic serology metadata with controlled correlation to specific taxa.
    
    Args:
        n_subjects: Number of subjects.
        n_taxa: Total number of taxa (needed to know correlation structure).
        target_correlation: Target correlation coefficient for selected taxa.
        taxa_indices: List of indices of taxa that should correlate with titer.
        seed: Random seed.
        
    Returns:
        DataFrame with columns: subject_id, titer_baseline, titer_post
    """
    np.random.seed(seed)
    
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Generate baseline titers (log-normal distribution, typical for serology)
    # Mean ~ 10, std ~ 5 in log space
    baseline_log = np.random.normal(loc=np.log(10), scale=0.5, size=n_subjects)
    titer_baseline = np.exp(baseline_log)
    
    # Generate post-vaccination titers
    # Start with baseline + noise
    noise = np.random.normal(loc=0, scale=0.2, size=n_subjects)
    titer_post_log = baseline_log + noise
    
    # Add correlation effect for selected taxa
    # We need to inject correlation without having the actual OTU table yet
    # We simulate the "latent" effect that the OTU table would have
    if taxa_indices:
        # Create a latent variable that represents the combined effect of selected taxa
        # This variable will be correlated with the final titer
        latent_effect = np.sum(np.random.normal(loc=0, scale=1, size=(n_subjects, len(taxa_indices))), axis=1)
        latent_effect = latent_effect / np.std(latent_effect)  # Normalize
        
        # Scale the effect to achieve target correlation
        # Simple linear injection: titer_post = baseline + beta * latent_effect
        beta = target_correlation
        titer_post_log = titer_post_log + beta * latent_effect
    
    titer_post = np.exp(titer_post_log)
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    return df

def generate_synthetic_otu_table_with_latent(
    n_subjects: int, 
    n_taxa: int, 
    target_correlation: float, 
    taxa_indices: List[int], 
    seed: int
) -> pd.DataFrame:
    """
    Generate OTU table where specific taxa are explicitly correlated with a latent response variable.
    This ensures the correlation exists in the generated data.
    
    Args:
        n_subjects: Number of subjects.
        n_taxa: Total number of taxa.
        target_correlation: Target correlation for selected taxa.
        taxa_indices: Indices of taxa to correlate.
        seed: Random seed.
        
    Returns:
        DataFrame with OTU table.
    """
    np.random.seed(seed)
    
    # Generate a latent response variable (simulating immune response strength)
    latent_response = np.random.normal(loc=0, scale=1, size=n_subjects)
    
    # Initialize abundance matrix
    abundances = np.zeros((n_subjects, n_taxa))
    
    # Generate uncorrelated taxa first (indices not in taxa_indices)
    uncorrelated_indices = [i for i in range(n_taxa) if i not in taxa_indices]
    if uncorrelated_indices:
        # Dirichlet for uncorrelated part
        alpha_uncorr = 0.5
        uncorr_part = np.random.dirichlet(np.ones(len(uncorrelated_indices)) * alpha_uncorr, size=n_subjects)
        for i, idx in enumerate(uncorrelated_indices):
            abundances[:, idx] = uncorr_part[:, i]
    
    # Generate correlated taxa
    if taxa_indices:
        # For correlated taxa, we make them dependent on the latent response
        # Abundance = base + beta * latent_response + noise
        beta = target_correlation * 0.5  # Scaling factor
        noise = np.random.normal(loc=0, scale=0.1, size=(n_subjects, len(taxa_indices)))
        
        for i, idx in enumerate(taxa_indices):
            base = np.abs(np.random.normal(loc=0.1, scale=0.05, size=n_subjects))
            abundances[:, idx] = base + beta * latent_response + noise[:, i]
            abundances[:, idx] = np.abs(abundances[:, idx])  # Ensure positive
    
    # Normalize to relative abundances (sum to 1)
    row_sums = abundances.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    abundances = abundances / row_sums
    
    # Create DataFrame
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    taxon_columns = [f"taxon_{i}" for i in range(n_taxa)]
    df = pd.DataFrame(abundances, columns=taxon_columns)
    df.insert(0, 'subject_id', subject_ids)
    
    return df

def generate_synthetic_serology_with_latent(
    n_subjects: int, 
    latent_response: np.ndarray, 
    seed: int
) -> pd.DataFrame:
    """
    Generate serology data based on the same latent response variable used in OTU generation.
    
    Args:
        n_subjects: Number of subjects.
        latent_response: The latent response variable from OTU generation.
        seed: Random seed.
        
    Returns:
        DataFrame with serology data.
    """
    np.random.seed(seed + 1)  # Slightly different seed for independence but reproducibility
    
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Baseline titers (log-normal)
    baseline_log = np.random.normal(loc=np.log(10), scale=0.5, size=n_subjects)
    titer_baseline = np.exp(baseline_log)
    
    # Post titers correlated with latent response
    # titer_post_log = baseline_log + beta * latent_response + noise
    beta = 0.8  # Strong correlation
    noise = np.random.normal(loc=0, scale=0.1, size=n_subjects)
    titer_post_log = baseline_log + beta * latent_response + noise
    titer_post = np.exp(titer_post_log)
    
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    return df

def main():
    """
    Main entry point for generating synthetic datasets.
    Checks config.USE_SYNTHETIC_DATA before proceeding.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if synthetic data generation is enabled
    use_synthetic = get_use_synthetic_data()
    if not use_synthetic:
        logger.info("USE_SYNTHETIC_DATA is False. Skipping synthetic data generation.")
        return
    
    logger.info("Starting synthetic dataset generation...")
    
    # Get configuration parameters
    n_taxa = get_num_synthetic_taxa()
    target_corr = get_target_correlation()
    seed = get_random_seed()
    n_subjects = get_min_sample_size()  # Default N=50 as per spec
    
    logger.info(f"Generating {n_subjects} subjects with {n_taxa} taxa.")
    logger.info(f"Target correlation: {target_corr}, Seed: {seed}")
    
    # Define indices of taxa that will be correlated
    # Spec says: "indices 0 to NUM_SYNTHETIC_TAXA-1"
    correlated_indices = list(range(n_taxa))
    
    # Generate OTU table with latent variable
    otu_df = generate_synthetic_otu_table_with_latent(
        n_subjects=n_subjects,
        n_taxa=n_taxa,
        target_correlation=target_corr,
        taxa_indices=correlated_indices,
        seed=seed
    )
    
    # Extract latent response from the generation process (we need to regenerate it or pass it)
    # To ensure perfect correlation, we regenerate the latent response with the same seed logic
    np.random.seed(seed)
    latent_response = np.random.normal(loc=0, scale=1, size=n_subjects)
    
    # Generate serology based on the same latent response
    serology_df = generate_synthetic_serology_with_latent(
        n_subjects=n_subjects,
        latent_response=latent_response,
        seed=seed
    )
    
    # Define output paths
    raw_path = get_raw_path()
    Path(raw_path).mkdir(parents=True, exist_ok=True)
    
    otu_output_path = Path(raw_path) / "synthetic_otutable.csv"
    serology_output_path = Path(raw_path) / "synthetic_serology.csv"
    
    # Save datasets
    otu_df.to_csv(otu_output_path, index=False)
    serology_df.to_csv(serology_output_path, index=False)
    
    logger.info(f"Synthetic OTU table saved to: {otu_output_path}")
    logger.info(f"Synthetic serology saved to: {serology_output_path}")
    
    # Verify output
    logger.info(f"OTU table shape: {otu_df.shape}")
    logger.info(f"Serology shape: {serology_df.shape}")
    
    # Log first few rows for verification
    logger.info("OTU table head:\n" + otu_df.head().to_string())
    logger.info("Serology head:\n" + serology_df.head().to_string())

if __name__ == "__main__":
    main()
