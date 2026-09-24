"""
Baseline Noise Generation and Distance Calculation (T023)

This module implements the generation of a synthetic Gaussian random noise baseline
matching the embedding dimensionality and calculates its Mahalanobis distance
to the benign centroid ($\mu_{benign}$) for comparison against real samples.

Requirements:
- Reads the benign statistics (mean and covariance) from the training phase.
- Generates a large set of random vectors from N(0, I) scaled to match the embedding distribution.
- Computes the Mahalanobis distance for these noise vectors.
- Saves the baseline statistics to `results/baseline_noise_stats.json`.

Note:
The task requires a "synthetic random noise baseline". This is a controlled experiment
to establish the expected distance of pure noise (no semantic content) from the
learned benign manifold. It does NOT replace real data processing but serves as
a reference point for anomaly scoring.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2

# Add project root to path if necessary (though imports should handle relative paths)
# Assuming standard project structure: code/src/models/baseline_noise.py
# We need to access stats utilities if needed, but here we calculate directly.

from src.utils.config import get_path, ensure_dir
from src.utils.stats import calculate_mahalanobis_distance, compute_benign_statistics

logger = logging.getLogger(__name__)

def generate_gaussian_noise_baseline(
    n_samples: int = 10000,
    embedding_dim: int = 384,
    seed: int = 42
) -> np.ndarray:
    """
    Generates a set of random vectors from a standard Gaussian distribution.

    Args:
        n_samples: Number of noise vectors to generate.
        embedding_dim: Dimensionality of the vectors (must match embedding output).
        seed: Random seed for reproducibility.

    Returns:
        numpy.ndarray of shape (n_samples, embedding_dim).
    """
    logger.info(f"Generating {n_samples} Gaussian noise vectors of dimension {embedding_dim}...")
    rng = np.random.default_rng(seed)
    # Generate standard normal noise: N(0, 1)
    noise_vectors = rng.standard_normal((n_samples, embedding_dim))
    logger.info(f"Generated noise baseline with shape {noise_vectors.shape}")
    return noise_vectors

def calculate_baseline_distances(
    noise_vectors: np.ndarray,
    benign_mean: np.ndarray,
    benign_cov: np.ndarray,
    output_path: Path
) -> dict:
    """
    Calculates the Mahalanobis distance of each noise vector to the benign centroid.

    Args:
        noise_vectors: Array of noise vectors (n_samples, dim).
        benign_mean: The mean vector of the benign training samples ($\mu_{benign}$).
        benign_cov: The covariance matrix of the benign training samples ($\Sigma$).
        output_path: Path to save the results JSON.

    Returns:
        Dictionary containing baseline statistics (mean, std, min, max, median).
    """
    logger.info("Calculating Mahalanobis distances for noise baseline...")
    
    # Ensure arrays are float64 for numerical stability
    benign_mean = benign_mean.astype(np.float64)
    benign_cov = benign_cov.astype(np.float64)
    noise_vectors = noise_vectors.astype(np.float64)

    distances = []
    # Calculate Mahalanobis distance for each vector
    # Using the pre-computed inverse covariance if available, or computing it here.
    # The stats module usually handles the inversion internally or returns the inverse.
    # We assume benign_cov here is the covariance matrix.
    
    try:
        # Compute inverse covariance if not already inverted
        # LedoitWolf usually returns the covariance estimate.
        cov_inv = np.linalg.inv(benign_cov)
        
        for vec in noise_vectors:
            dist = mahalanobis(vec, benign_mean, cov_inv)
            distances.append(dist)
        
        distances = np.array(distances)
    except np.linalg.LinAlgError as e:
        logger.error(f"Failed to invert covariance matrix: {e}")
        raise ValueError("Covariance matrix is singular; cannot compute Mahalanobis distance.")

    # Calculate statistics
    baseline_stats = {
        "mean": float(np.mean(distances)),
        "std": float(np.std(distances)),
        "min": float(np.min(distances)),
        "max": float(np.max(distances)),
        "median": float(np.median(distances)),
        "p95": float(np.percentile(distances, 95)),
        "p99": float(np.percentile(distances, 99)),
        "n_samples": n_samples
    }

    logger.info(f"Baseline Distance Stats: Mean={baseline_stats['mean']:.4f}, Std={baseline_stats['std']:.4f}")
    
    # Save results
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(baseline_stats, f, indent=2)
    
    logger.info(f"Baseline statistics saved to {output_path}")
    return baseline_stats

def main():
    """
    Main entry point for T023: Generate synthetic random noise baseline.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Generate Gaussian noise baseline for anomaly detection comparison.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--n-samples", type=int, default=10000, help="Number of noise samples to generate.")
    args = parser.parse_args()

    # Paths
    # We expect the benign statistics to be saved by T022/T022b in the training phase.
    # Typically saved as part of the model artifact or a specific stats file.
    # Let's assume the training script saved 'benign_stats.json' in data/ or results/.
    # Based on T022b, anomaly scores are saved to data/anomaly_scores.parquet.
    # We need the mean and covariance used there.
    
    # Convention: Training script saves stats to data/benign_stats.json
    stats_path = get_path("data/benign_stats.json")
    output_path = get_path("results/baseline_noise_stats.json")
    
    if not os.path.exists(stats_path):
        logger.error(f"Benign statistics file not found at {stats_path}. "
                     "Please ensure T022/T022b has completed and saved the benign mean/covariance.")
        sys.exit(1)

    # Load benign statistics
    logger.info(f"Loading benign statistics from {stats_path}...")
    with open(stats_path, 'r') as f:
        stats_data = json.load(f)
    
    benign_mean = np.array(stats_data['mean'])
    benign_cov = np.array(stats_data['covariance'])
    embedding_dim = benign_mean.shape[0]

    logger.info(f"Loaded benign mean (dim={embedding_dim}) and covariance.")

    # Generate noise
    noise_vectors = generate_gaussian_noise_baseline(
        n_samples=args.n_samples,
        embedding_dim=embedding_dim,
        seed=args.seed
    )

    # Calculate distances
    calculate_baseline_distances(
        noise_vectors=noise_vectors,
        benign_mean=benign_mean,
        benign_cov=benign_cov,
        output_path=output_path
    )

    logger.info("Task T023 completed successfully.")

if __name__ == "__main__":
    main()