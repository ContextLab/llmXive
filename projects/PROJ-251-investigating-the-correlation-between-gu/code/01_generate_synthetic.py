import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Import config utilities to check the flag
# We assume the project structure puts utils in code/utils/
# and we need to add code to the path if running as script
sys.path.insert(0, str(Path(__file__).parent))
from utils.config import get_raw_path, get_random_seed, get_min_sample_size
from utils.logging_config import get_logger

# Constants for synthetic generation
NUM_SUBJECTS = 50
NUM_TAXA = 20
RANDOM_SEED = 42

def generate_synthetic_otu_table(n_subjects: int, n_taxa: int, seed: int) -> pd.DataFrame:
    """
    Generates a synthetic OTU table with relative abundances.
    Ensures rows sum to 1.0 (relative abundance) and adds controlled noise.
    """
    rng = np.random.default_rng(seed)
    
    # Generate base abundances using a Dirichlet distribution to ensure they sum to 1
    # alpha values control the sparsity; lower alpha = more zeros/sparsity
    alpha = 0.5
    raw_abundances = rng.dirichlet(np.ones(n_taxa) * alpha, size=n_subjects)
    
    # Add some small random noise to make it look less perfectly Dirichlet
    noise = rng.normal(0, 0.01, raw_abundances.shape)
    noisy_abundances = raw_abundances + noise
    
    # Re-normalize to ensure they sum to 1 and handle negatives
    noisy_abundances = np.clip(noisy_abundances, 0, None)
    row_sums = noisy_abundances.sum(axis=1, keepdims=True)
    final_abundances = noisy_abundances / row_sums
    
    # Create column names
    taxon_names = [f"Taxon_{i:03d}" for i in range(n_taxa)]
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    df = pd.DataFrame(final_abundances, columns=taxon_names)
    df.insert(0, 'subject_id', subject_ids)
    
    return df

def generate_synthetic_serology(n_subjects: int, seed: int, otu_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates synthetic serology data with a controlled correlation to one specific taxon.
    This ensures the pipeline has something to find during correlation analysis.
    """
    rng = np.random.default_rng(seed + 1) # Different seed offset
    
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    # Pick a "signal" taxon to correlate with the titer
    signal_taxon_idx = 5
    signal_taxon_name = f"Taxon_{signal_taxon_idx:03d}"
    
    signal_values = otu_df[signal_taxon_name].values
    
    # Generate baseline titers (log-normal distribution)
    # Typical HAI baseline might be around 10-40
    baseline_log = rng.normal(2.5, 0.5, n_subjects)
    baseline_titers = np.exp(baseline_log)
    
    # Generate post-vaccination titers
    # Base effect: add a small random boost
    boost = rng.normal(5, 2, n_subjects)
    
    # Add the signal: if signal taxon is high, titer is higher
    # Normalize signal to 0-1 range roughly
    signal_normalized = (signal_values - signal_values.min()) / (signal_values.max() - signal_values.min() + 1e-6)
    signal_effect = signal_normalized * 15 # Max 15 unit increase from signal
    
    noise = rng.normal(0, 3, n_subjects)
    post_titers = baseline_titers + boost + signal_effect + noise
    
    # Ensure titers are positive
    post_titers = np.maximum(post_titers, 1.0)
    
    # Add some values below Limit of Detection (LOD) = 5
    # Let's force 10% of post-titers to be below LOD to test LOD handling
    lod = 5.0
    num_below_lod = int(n_subjects * 0.1)
    below_lod_indices = rng.choice(n_subjects, size=num_below_lod, replace=False)
    post_titers[below_lod_indices] = rng.uniform(0.5, lod - 0.1, num_below_lod)
    
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'titer_baseline': baseline_titers,
        'titer_post': post_titers
    })
    
    return df

def main():
    logger = get_logger("synthetic_generator")
    logger.info("Starting synthetic dataset generation.")
    
    # Check config flag
    # Since we are generating synthetic, we assume USE_SYNTHETIC_DATA is effectively True
    # or this script is only called when needed.
    
    raw_path = get_raw_path()
    logger.info(f"Output directory: {raw_path}")
    
    seed = get_random_seed()
    min_samples = get_min_sample_size()
    
    n_subjects = max(NUM_SUBJECTS, min_samples)
    
    logger.info(f"Generating {n_subjects} subjects with {NUM_TAXA} taxa.")
    
    # 1. Generate OTU Table
    otu_df = generate_synthetic_otu_table(n_subjects, NUM_TAXA, seed)
    otu_path = raw_path / "synthetic_otutable.csv"
    otu_df.to_csv(otu_path, index=False)
    logger.info(f"Written OTU table to {otu_path}")
    
    # 2. Generate Serology
    sero_df = generate_synthetic_serology(n_subjects, seed, otu_df)
    sero_path = raw_path / "synthetic_serology.csv"
    sero_df.to_csv(sero_path, index=False)
    logger.info(f"Written serology data to {sero_path}")
    
    # 3. Verification
    logger.info("Verification: Loading generated files to check integrity.")
    loaded_otu = pd.read_csv(otu_path)
    loaded_sero = pd.read_csv(sero_path)
    
    assert len(loaded_otu) == n_subjects, "OTU row count mismatch"
    assert len(loaded_sero) == n_subjects, "Serology row count mismatch"
    assert set(loaded_otu['subject_id']) == set(loaded_sero['subject_id']), "Subject ID mismatch"
    
    # Check sums
    taxon_cols = [c for c in loaded_otu.columns if c.startswith('Taxon_')]
    sums = loaded_otu[taxon_cols].sum(axis=1)
    assert np.allclose(sums, 1.0, atol=1e-6), "OTU rows do not sum to 1.0"
    
    logger.info("Synthetic dataset generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
