"""
T023: Generate synthetic random noise baseline (Gaussian, same dim) and calculate its distance to mu_benign.

This script generates a Gaussian random noise baseline matching the dimensionality
of the benign embeddings. It calculates the Mahalanobis distance of these noise
vectors to the benign centroid (mu_benign) and covariance (Sigma) derived from
the training set.

The output is saved to data/baseline_noise_scores.parquet for comparison in the evaluation phase.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_path, ensure_dir, load_state
from src.utils.stats import compute_benign_statistics, calculate_mahalanobis_distance
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_gaussian_noise_baseline(
    n_samples: int,
    dimension: int,
    seed: int = 42
) -> np.ndarray:
    """
    Generate synthetic random noise baseline (Gaussian, same dim).

    Args:
        n_samples: Number of noise samples to generate.
        dimension: Dimensionality of the embedding space.
        seed: Random seed for reproducibility.

    Returns:
        np.ndarray: Array of shape (n_samples, dimension) containing Gaussian noise.
    """
    np.random.seed(seed)
    # Generate standard normal noise (mean=0, std=1)
    # This represents "random noise" in the embedding space
    noise_data = np.random.randn(n_samples, dimension)
    logger.info(f"Generated {n_samples} noise samples of dimension {dimension}")
    return noise_data


def calculate_baseline_distances(
    noise_data: np.ndarray,
    benign_mean: np.ndarray,
    benign_cov: np.ndarray,
    output_path: Path
) -> pd.DataFrame:
    """
    Calculate Mahalanobis distance for the noise baseline against benign statistics.

    Args:
        noise_data: The generated noise vectors.
        benign_mean: The centroid of benign samples (mu_benign).
        benign_cov: The covariance matrix of benign samples (Sigma).
        output_path: Path to save the results.

    Returns:
        pd.DataFrame: DataFrame containing sample_id, distance, and is_anomaly flag.
    """
    logger.info(f"Calculating Mahalanobis distances for {len(noise_data)} noise samples...")

    # Calculate distances
    distances = calculate_mahalanobis_distance(noise_data, benign_mean, benign_cov)

    # Determine anomaly threshold (chi2 distribution)
    # For a 95% confidence interval, we use the 95th percentile of chi2 with d degrees of freedom
    d = len(benign_mean)
    threshold = chi2.ppf(0.95, d)

    # Create results DataFrame
    results_df = pd.DataFrame({
        'sample_id': [f"noise_{i}" for i in range(len(noise_data))],
        'mahalanobis_distance': distances,
        'threshold_95': threshold,
        'is_anomaly': distances > threshold,
        'label': 'noise_baseline'  # Explicitly mark as noise baseline
    })

    # Save to parquet
    ensure_dir(output_path.parent)
    results_df.to_parquet(output_path, index=False)
    logger.info(f"Saved baseline noise scores to {output_path}")

    # Log summary statistics
    logger.info(f"Noise Baseline Statistics:")
    logger.info(f"  Mean Distance: {np.mean(distances):.4f}")
    logger.info(f"  Std Distance: {np.std(distances):.4f}")
    logger.info(f"  Max Distance: {np.max(distances):.4f}")
    logger.info(f"  Anomaly Rate (95% threshold): {np.mean(results_df['is_anomaly']) * 100:.2f}%")

    return results_df


def main():
    """Main entry point for T023."""
    parser = argparse.ArgumentParser(description="Generate synthetic noise baseline and calculate distances.")
    parser.add_argument("--n_samples", type=int, default=1000, help="Number of noise samples to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--input_state", type=str, default="state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml",
                        help="Path to state file containing benign statistics")
    parser.add_argument("--output_file", type=str, default="data/baseline_noise_scores.parquet",
                        help="Output path for baseline scores")
    args = parser.parse_args()

    # Load state to get benign statistics (mu and Sigma) computed in T022
    # The state file should contain the computed statistics from T022
    state_path = get_path(args.input_state)
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        sys.exit(1)

    state = load_state(state_path)

    # Retrieve benign statistics from state
    # These should have been computed in T022 and stored in the state
    if 'benign_statistics' not in state:
        logger.error("benign_statistics not found in state file. Ensure T022 has been completed.")
        sys.exit(1)

    benign_stats = state['benign_statistics']
    benign_mean = np.array(benign_stats['mean'])
    benign_cov = np.array(benign_stats['covariance'])
    dimension = len(benign_mean)

    logger.info(f"Loaded benign statistics: dimension={dimension}")

    # Generate noise baseline
    noise_data = generate_gaussian_noise_baseline(
        n_samples=args.n_samples,
        dimension=dimension,
        seed=args.seed
    )

    # Calculate distances
    output_path = get_path(args.output_file)
    results_df = calculate_baseline_distances(
        noise_data,
        benign_mean,
        benign_cov,
        output_path
    )

    logger.info("T023 Baseline Noise Generation completed successfully.")
    return results_df


if __name__ == "__main__":
    main()
