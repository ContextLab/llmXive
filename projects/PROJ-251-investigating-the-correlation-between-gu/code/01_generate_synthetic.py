import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

from utils.config import get_random_seed, get_use_synthetic_data, get_min_sample_size, ensure_directories
from utils.logging_config import get_logger

# Ensure we can import from code/
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

logger = get_logger(__name__)

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generate a synthetic OTU table with controlled correlations.
    
    - 5 taxa have a controlled correlation with a hidden response variable.
    - Remaining taxa are noise.
    - Relative abundances sum to 1.0 per subject.
    """
    rng = np.random.default_rng(seed)
    
    # Generate subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(1, n_subjects + 1)]
    
    # Taxa names
    taxa_names = [f"Taxon_{chr(65 + i)}" for i in range(n_taxa)]
    
    # Generate base abundances (Dirichlet-like distribution for compositional data)
    # Use alpha parameters to create some dominant and some rare taxa
    alpha = np.ones(n_taxa) * 0.5
    raw_abundances = rng.dirichlet(alpha, size=n_subjects)
    
    # Introduce controlled correlation for first 5 taxa
    # Create a hidden response variable that correlates with specific taxa
    hidden_response = rng.normal(0, 1, n_subjects)
    
    # Adjust first 5 taxa to correlate with hidden response
    correlation_strength = 0.5
    for i in range(min(5, n_taxa)):
        noise = rng.normal(0, 0.1, n_subjects)
        raw_abundances[:, i] = raw_abundances[:, i] * (1 + correlation_strength * hidden_response) + noise
    
    # Ensure non-negative values
    raw_abundances = np.maximum(raw_abundances, 0)
    
    # Normalize to relative abundances (sum to 1)
    row_sums = raw_abundances.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    relative_abundances = raw_abundances / row_sums
    
    # Create DataFrame
    df = pd.DataFrame(relative_abundances, columns=taxa_names)
    df.insert(0, 'subject_id', subject_ids)
    
    return df

def generate_synthetic_serology(n_subjects: int, seed: int, otu_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic serology metadata with controlled correlations to microbiome.
    
    - Baseline titers: log-normal distribution
    - Post-vaccination titers: correlated with baseline and specific taxa
    """
    rng = np.random.default_rng(seed + 1)  # Different seed for serology
    
    subject_ids = otu_df['subject_id'].values
    
    # Generate baseline titers (log-normal)
    baseline_log_mean = 2.0
    baseline_log_std = 0.5
    baseline_titers = np.exp(rng.normal(baseline_log_mean, baseline_log_std, n_subjects))
    baseline_titers = np.maximum(baseline_titers, 1.0)  # Ensure positive values
    
    # Generate post-vaccination titers
    # Correlate with baseline and specific taxa (first 5)
    post_titers = baseline_titers.copy()
    
    # Add effect from microbiome (first 5 taxa)
    microbiome_effect = np.zeros(n_subjects)
    for i in range(min(5, len(otu_df.columns) - 1)):
        taxon_col = otu_df.columns[i + 1]  # Skip subject_id
        microbiome_effect += otu_df[taxon_col].values * (0.3 + rng.uniform(-0.1, 0.1, n_subjects))
    
    # Add random variation and ensure positive values
    post_titers = post_titers * (1 + 0.5 * microbiome_effect + rng.normal(0, 0.2, n_subjects))
    post_titers = np.maximum(post_titers, 1.0)
    
    # Create DataFrame
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': baseline_titers,
        'titer_post': post_titers
    })
    
    return df

def main():
    """
    Main function to generate synthetic datasets.
    """
    logger.info("Starting synthetic data generation")
    
    # Check if synthetic data is enabled
    if not get_use_synthetic_data():
        logger.warning("USE_SYNTHETIC_DATA is False. Skipping synthetic data generation.")
        return
    
    # Get configuration
    seed = get_random_seed()
    min_sample_size = get_min_sample_size()
    
    # Use default parameters for synthetic data
    n_subjects = max(min_sample_size, 100)  # Generate at least 100 samples
    n_taxa = 50  # 50 taxa in the synthetic dataset
    
    logger.info(f"Generating synthetic data: {n_subjects} subjects, {n_taxa} taxa, seed={seed}")
    
    # Ensure directories exist
    ensure_directories()
    
    # Generate OTU table
    otu_df = generate_synthetic_otu_table(n_subjects, n_taxa, seed)
    otu_path = Path("data/raw/synthetic_otutable.csv")
    otu_df.to_csv(otu_path, index=False)
    logger.info(f"Generated OTU table: {otu_path} ({len(otu_df)} rows)")
    
    # Generate serology metadata
    serology_df = generate_synthetic_serology(n_subjects, seed, otu_df)
    serology_path = Path("data/raw/synthetic_serology.csv")
    serology_df.to_csv(serology_path, index=False)
    logger.info(f"Generated serology data: {serology_path} ({len(serology_df)} rows)")
    
    # Verify outputs
    assert otu_path.exists(), f"Failed to create OTU table: {otu_path}"
    assert serology_path.exists(), f"Failed to create serology data: {serology_path}"
    
    logger.info("Synthetic data generation completed successfully")

if __name__ == "__main__":
    main()
