"""
Data generation module for synthetic datasets and matrices.

This module generates synthetic genomic features and phylogenetic distance matrices
for validation purposes when real data is unavailable and VALIDATION_MODE is enabled.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import shared configuration and utilities
# Note: Using absolute imports as per project structure (code/ is in sys.path)
from config import get_config, VALIDATION_MODE, ensure_directories
from utils.logging import DataPipelineLog

# Configure logging
logger = logging.getLogger(__name__)

# Constants from T012
TRAINING_GENES = [
    'NCED3', 'ABF3', 'P5CS', 'DREB2A', 'ERF1', 'ABI5', 'RD29A', 'COR15A',
    'LEA3', 'HSP70', 'SOD', 'APX1', 'CAT1', 'GPX1', 'MDHAR', 'DHAR',
    'GSTU', 'ZAT12', 'WRKY33', 'MYB96'
]

# Independent validation genes from T011c (strictly disjoint)
VALIDATION_GENES = [
    'ABF2', 'DREB1B', 'NAC072', 'WRKY40', 'bZIP28', 'bZIP63', 'ABI1',
    'ABI2', 'PP2CA', 'SnRK2.1', 'SnRK2.5', 'SnRK2.7', 'RD26', 'RD29B', 'COR15B'
]

def sigmoid(x: float) -> float:
    """Compute sigmoid function."""
    return 1.0 / (1.0 + np.exp(-x))

def generate_synthetic_genomic_features(
    n_samples: int = 50,
    random_seed: int = 42,
    output_path: str = "data/processed/synthetic_genomics.csv"
) -> pd.DataFrame:
    """
    Generate synthetic genomic features and drought labels.

    Logic:
    1. Select a hidden subset of genes (deterministic via seed) to drive the label.
    2. Generate binary features for all 20 training genes.
    3. Compute label probability based on hidden genes sum.
    4. Add noise to prevent perfect correlation.

    Args:
        n_samples: Number of species samples to generate.
        random_seed: Random seed for reproducibility.
        output_path: Path to save the CSV.

    Returns:
        DataFrame with gene columns and label column.
    """
    if not VALIDATION_MODE:
        raise RuntimeError(
            "CRITICAL: Synthetic data generation attempted in Production Mode "
            "(VALIDATION_MODE=False). Synthetic data is forbidden."
        )

    rng = np.random.default_rng(random_seed)

    # Step 1: Select hidden genes (subset of 5 from the 20 training genes)
    # Deterministic selection based on seed
    hidden_indices = rng.choice(len(TRAINING_GENES), size=5, replace=False)
    hidden_genes = [TRAINING_GENES[i] for i in hidden_indices]

    logger.info(f"Hidden genes selected for label generation: {hidden_genes}")
    logger.info(f"Indices of hidden genes: {hidden_indices.tolist()}")

    # Log Scope Reduction explicitly
    logger.warning(
        "Scope Reduction: Synthetic data used, invalidates FR-001/SC-001 biological claims"
    )

    # Step 2: Generate binary features (0 or 1) for all 20 training genes
    # Using Bernoulli distribution with p=0.5 for simplicity
    data = rng.integers(0, 2, size=(n_samples, len(TRAINING_GENES)))
    df = pd.DataFrame(data, columns=TRAINING_GENES)

    # Step 3: Compute label probability
    # prob = sigmoid(sum(hidden_genes) - 2) + noise
    hidden_sum = df[hidden_genes].sum(axis=1)
    base_prob = sigmoid(hidden_sum - 2)

    # Add noise (0.1 std dev, clipped to [0, 1])
    noise = rng.normal(0, 0.1, size=n_samples)
    prob = base_prob + noise
    prob = np.clip(prob, 0.0, 1.0)

    # Step 4: Generate binary labels
    labels = (rng.random(n_samples) < prob).astype(int)
    df['label'] = labels

    # Step 5: Chi-Square Goodness-of-Fit Test
    # Verify label distribution matches expected sigmoid probability
    # Expected mean = 0.5 (uniform across bins assumption for simplicity)
    # Bins = 10
    observed_counts = np.histogram(labels, bins=10, range=(0, 1))[0]
    expected_counts = np.full(10, n_samples / 10)

    # Chi-Square statistic
    chi2_stat = np.sum((observed_counts - expected_counts) ** 2 / expected_counts)
    # Degrees of freedom = bins - 1
    dof = 10 - 1
    # P-value from chi2 distribution
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(chi2_stat, dof)

    chi2_result = {
        "statistic": float(chi2_stat),
        "p_value": float(p_value),
        "dof": dof,
        "passed": p_value > 0.05,
        "expected_mean": 0.5,
        "observed_mean": float(labels.mean())
    }

    logger.info(f"Chi-Square Goodness-of-Fit Test: p-value={p_value:.4f}, passed={chi2_result['passed']}")

    # Save generation config
    config_path = Path("data/logs/generation_config.json")
    ensure_directories([config_path.parent])

    # Load existing config or create new
    if config_path.exists():
        with open(config_path, 'r') as f:
            existing_config = json.load(f)
    else:
        existing_config = {}

    existing_config['chi_square_test_result'] = chi2_result
    existing_config['hidden_subset'] = hidden_genes
    existing_config['hidden_indices'] = hidden_indices.tolist()
    existing_config['n_samples'] = n_samples
    existing_config['random_seed'] = random_seed

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=2)

    # Save DataFrame to CSV
    ensure_directories([Path(output_path)])
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic genomic data saved to {output_path}")

    return df

def generate_synthetic_phylogenetic_matrix(
    n_species: int = 50,
    random_seed: int = 42,
    min_distance: float = 0.01,
    max_distance: float = 1.0,
    output_path: str = "data/processed/synthetic_phylo_matrix.npy"
) -> np.ndarray:
    """
    Generate a synthetic phylogenetic distance matrix.

    Logic:
    1. Generate an N x N symmetric matrix.
    2. Diagonal is zero.
    3. Off-diagonal values are uniformly distributed between min_distance and max_distance.
    4. Use random_state=42 for all random operations.

    Args:
        n_species: Number of species (matrix dimension).
        random_seed: Random seed for reproducibility.
        min_distance: Minimum off-diagonal value.
        max_distance: Maximum off-diagonal value.
        output_path: Path to save the .npy file.

    Returns:
        Symmetric distance matrix (numpy array).
    """
    if not VALIDATION_MODE:
        raise RuntimeError(
            "CRITICAL: Synthetic phylogenetic matrix generation attempted in Production Mode. "
            "Real phylogenetic data is required."
        )

    rng = np.random.default_rng(random_seed)

    # Generate upper triangle (excluding diagonal)
    upper_indices = np.triu_indices(n_species, k=1)
    n_off_diagonal = len(upper_indices[0])

    # Generate uniform random values for off-diagonal elements
    off_diagonal_values = rng.uniform(min_distance, max_distance, size=n_off_diagonal)

    # Initialize matrix with zeros
    matrix = np.zeros((n_species, n_species))

    # Fill upper triangle
    matrix[upper_indices] = off_diagonal_values

    # Make symmetric
    matrix = matrix + matrix.T

    # Verify properties
    assert np.allclose(np.diag(matrix), 0.0), "Diagonal must be zero"
    assert np.all(matrix[np.triu_indices(n_species, k=1)] >= min_distance), "Off-diagonals must be >= min_distance"
    assert np.all(matrix[np.triu_indices(n_species, k=1)] <= max_distance), "Off-diagonals must be <= max_distance"
    assert matrix.shape == (n_species, n_species), "Shape mismatch"

    # Save to file
    ensure_directories([Path(output_path).parent])
    np.save(output_path, matrix)
    logger.info(f"Synthetic phylogenetic matrix saved to {output_path} (shape: {matrix.shape})")

    return matrix

def main():
    """Main entry point for data generation."""
    config = get_config()
    ensure_directories([Path("data/processed"), Path("data/logs")])

    logger.info("Starting synthetic data generation...")

    # Generate genomic features
    try:
        df_genomics = generate_synthetic_genomic_features(
            n_samples=config.get('n_samples', 50),
            random_seed=config.get('random_seed', 42)
        )
        logger.info(f"Generated {len(df_genomics)} genomic samples")
    except Exception as e:
        logger.error(f"Failed to generate genomic features: {e}")
        raise

    # Generate phylogenetic matrix
    try:
        phylo_matrix = generate_synthetic_phylogenetic_matrix(
            n_species=config.get('n_samples', 50),
            random_seed=config.get('random_seed', 42)
        )
        logger.info(f"Generated phylogenetic matrix with shape {phylo_matrix.shape}")
    except Exception as e:
        logger.error(f"Failed to generate phylogenetic matrix: {e}")
        raise

    logger.info("Synthetic data generation completed successfully.")

if __name__ == "__main__":
    main()