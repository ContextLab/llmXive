import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure the code directory is in the path for imports if running as script
code_root = Path(__file__).resolve().parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import (
    get_num_synthetic_taxa,
    get_target_correlation,
    get_random_seed,
    get_use_synthetic_data,
    get_min_sample_size
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with controlled correlation structure.
    
    Creates n_taxa columns named 'taxon_0' through 'taxon_{n_taxa-1}'.
    The first `n_taxa` taxa (all of them in this context) are correlated 
    with a latent variable that will drive the serology response.
    
    Args:
        n_subjects: Number of subjects (rows).
        n_taxa: Number of taxa (columns).
        seed: Random seed for reproducibility.
        
    Returns:
        pd.DataFrame: OTU table with subject_id and taxon columns.
    """
    np.random.seed(seed)
    
    # Generate a latent variable Z that drives the correlation
    Z = np.random.normal(0, 1, n_subjects)
    
    # Generate taxa abundances
    # We want taxa to be correlated with Z and with each other to some degree
    # to simulate a realistic microbiome structure.
    # Abundances must be positive.
    
    # Base abundances (log-normal distribution is common for microbiome)
    base_abundances = np.random.lognormal(mean=0, sigma=1, size=(n_subjects, n_taxa))
    
    # Introduce correlation with Z
    # We add a component of Z to the log-abundance before exponentiating
    # This ensures the resulting abundance is correlated with Z
    correlation_strength = 0.5 # Moderate correlation
    log_abundances = np.log(base_abundances) + correlation_strength * Z[:, np.newaxis]
    
    # Add some noise
    noise = np.random.normal(0, 0.1, size=(n_subjects, n_taxa))
    log_abundances += noise
    
    abundances = np.exp(log_abundances)
    
    # Convert to relative abundances (sum to 1 per row)
    row_sums = abundances.sum(axis=1, keepdims=True)
    relative_abundances = abundances / row_sums
    
    # Create DataFrame
    taxon_cols = [f'taxon_{i}' for i in range(n_taxa)]
    df = pd.DataFrame(relative_abundances, columns=taxon_cols)
    df.insert(0, 'subject_id', [f'SUBJ_{i:04d}' for i in range(n_subjects)])
    
    return df

def generate_synthetic_serology(n_subjects: int, n_taxa: int, target_corr: float, seed: int) -> pd.DataFrame:
    """
    Generate synthetic serology metadata with controlled correlation to taxa.
    
    The post-vaccination titer is generated to have a correlation of `target_corr`
    with the latent variable Z used in OTU generation.
    
    Args:
        n_subjects: Number of subjects.
        n_taxa: Number of taxa (used to determine which columns correlate).
        target_corr: Target correlation coefficient between latent variable and log_titer.
        seed: Random seed for reproducibility.
        
    Returns:
        pd.DataFrame: Serology data with subject_id, titer_baseline, titer_post.
    """
    np.random.seed(seed)
    
    # Generate latent variable Z (same seed logic as OTU table to ensure correlation)
    # Note: In a real scenario, we'd pass Z from the OTU generator, 
    # but for modularity, we regenerate with same seed if n_subjects matches.
    # A more robust way is to pass Z, but here we assume seed consistency.
    Z = np.random.normal(0, 1, n_subjects)
    
    # Generate baseline titers (log-normal, typical for antibody titers)
    # HAI titers are often powers of 2, but we'll use continuous log-normal for simplicity
    baseline_mean = np.log(20) # Mean around 20
    baseline_sigma = 0.5
    titer_baseline = np.exp(np.random.normal(baseline_mean, baseline_sigma, n_subjects))
    
    # Generate post-vaccination titers
    # We want log(titer_post) to correlate with Z
    # log(titer_post) = mu + beta * Z + noise
    # Correlation = beta * std(Z) / std(log(titer_post))
    
    # Let's set up the relationship
    # target_corr = corr(Z, log_titer_post)
    # log_titer_post = mu + target_corr * Z + sqrt(1-target_corr^2) * noise
    # (assuming Z and noise are standard normal)
    
    noise = np.random.normal(0, 1, n_subjects)
    log_titer_post_mean = np.log(40) # Mean around 40
    
    # Construct log_titer_post to have the desired correlation with Z
    # We scale Z by target_corr and noise by sqrt(1 - target_corr^2)
    # Then shift and scale to have the desired mean
    std_target = 0.5 # Standard deviation of log_titer_post
    log_titer_post = (
        log_titer_post_mean + 
        target_corr * std_target * Z + 
        np.sqrt(1 - target_corr**2) * std_target * noise
    )
    
    titer_post = np.exp(log_titer_post)
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': [f'SUBJ_{i:04d}' for i in range(n_subjects)],
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    
    return df

def generate_synthetic_otu_table_with_latent(n_subjects: int, n_taxa: int, seed: int) -> tuple:
    """
    Generate OTU table and return the latent variable Z for consistent serology generation.
    
    Args:
        n_subjects: Number of subjects.
        n_taxa: Number of taxa.
        seed: Random seed.
        
    Returns:
        tuple: (df_otu, Z)
    """
    np.random.seed(seed)
    Z = np.random.normal(0, 1, n_subjects)
    base_abundances = np.random.lognormal(mean=0, sigma=1, size=(n_subjects, n_taxa))
    correlation_strength = 0.5
    log_abundances = np.log(base_abundances) + correlation_strength * Z[:, np.newaxis]
    noise = np.random.normal(0, 0.1, size=(n_subjects, n_taxa))
    log_abundances += noise
    abundances = np.exp(log_abundances)
    row_sums = abundances.sum(axis=1, keepdims=True)
    relative_abundances = abundances / row_sums
    taxon_cols = [f'taxon_{i}' for i in range(n_taxa)]
    df = pd.DataFrame(relative_abundances, columns=taxon_cols)
    df.insert(0, 'subject_id', [f'SUBJ_{i:04d}' for i in range(n_subjects)])
    return df, Z

def generate_synthetic_serology_with_latent(n_subjects: int, Z: np.ndarray, target_corr: float, seed: int) -> pd.DataFrame:
    """
    Generate serology using a provided latent variable Z.
    
    Args:
        n_subjects: Number of subjects.
        Z: Latent variable array.
        target_corr: Target correlation.
        seed: Random seed.
        
    Returns:
        pd.DataFrame: Serology data.
    """
    np.random.seed(seed)
    noise = np.random.normal(0, 1, n_subjects)
    log_titer_post_mean = np.log(40)
    std_target = 0.5
    log_titer_post = (
        log_titer_post_mean + 
        target_corr * std_target * Z + 
        np.sqrt(1 - target_corr**2) * std_target * noise
    )
    titer_post = np.exp(log_titer_post)
    baseline_mean = np.log(20)
    baseline_sigma = 0.5
    titer_baseline = np.exp(np.random.normal(baseline_mean, baseline_sigma, n_subjects))
    
    df = pd.DataFrame({
        'subject_id': [f'SUBJ_{i:04d}' for i in range(n_subjects)],
        'titer_baseline': titer_baseline,
        'titer_post': titer_post
    })
    return df

def main():
    """
    Main entry point to generate synthetic dataset.
    Reads configuration from utils.config and writes to data/raw/.
    """
    logger.info("Starting synthetic data generation task T011b")
    
    # Check if synthetic data is enabled
    if not get_use_synthetic_data():
        logger.warning("USE_SYNTHETIC_DATA is False. Skipping synthetic data generation.")
        return
    
    # Get configuration parameters
    n_taxa = get_num_synthetic_taxa()
    target_corr = get_target_correlation()
    seed = get_random_seed()
    n_subjects = get_min_sample_size() # Use minimum sample size as target
    
    logger.info(f"Generating synthetic data: N={n_subjects}, Taxa={n_taxa}, Target_Corr={target_corr}, Seed={seed}")
    
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OTU table and latent variable
    df_otu, Z = generate_synthetic_otu_table_with_latent(n_subjects, n_taxa, seed)
    
    # Generate serology using the same latent variable
    df_serology = generate_synthetic_serology_with_latent(n_subjects, Z, target_corr, seed + 1)
    
    # Save to CSV
    otu_path = output_dir / "synthetic_otutable.csv"
    serology_path = output_dir / "synthetic_serology.csv"
    
    df_otu.to_csv(otu_path, index=False)
    df_serology.to_csv(serology_path, index=False)
    
    logger.info(f"Successfully generated {otu_path}")
    logger.info(f"Successfully generated {serology_path}")
    
    # Verification
    assert len(df_otu) == n_subjects, f"Expected {n_subjects} rows in OTU table, got {len(df_otu)}"
    assert len(df_serology) == n_subjects, f"Expected {n_subjects} rows in serology, got {len(df_serology)}"
    assert list(df_otu.columns[:1]) == ['subject_id'], "First column must be subject_id"
    assert list(df_serology.columns[:1]) == ['subject_id'], "First column must be subject_id"
    assert len([c for c in df_otu.columns if c.startswith('taxon_')]) == n_taxa, f"Expected {n_taxa} taxon columns"
    
    logger.info("Synthetic data generation completed and verified.")

if __name__ == "__main__":
    main()
