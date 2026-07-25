import numpy as np
import json
import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.simulation import SyntheticDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_correlated_data(
    n: int,
    p: int,
    rho: float,
    seed: int,
    distribution_type: str = "normal"
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate synthetic high-dimensional data with controlled correlation.

    Args:
        n: Number of samples
        p: Number of features
        rho: Target correlation threshold
        seed: Random seed for reproducibility
        distribution_type: Type of distribution ('normal', 't', 'skew_normal')

    Returns:
        Tuple of (data_matrix, metadata_dict)
    """
    np.random.seed(seed)

    # Generate base correlated data
    # Construct correlation matrix with block structure for stability
    if rho == 0:
        cov_matrix = np.eye(p)
    else:
        # Simple equicorrelation structure for stability
        cov_matrix = np.full((p, p), rho * 0.1)  # Scale down to ensure positive definiteness
        np.fill_diagonal(cov_matrix, 1.0)

        # Ensure positive definiteness
        eigvals = np.linalg.eigvalsh(cov_matrix)
        if np.min(eigvals) <= 0:
            logger.warning(f"Correction applied: min eigenvalue {np.min(eigvals)}")
            cov_matrix = cov_matrix + (abs(np.min(eigvals)) + 1e-8) * np.eye(p)

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        logger.error("Cholesky decomposition failed. Matrix is not positive definite.")
        raise

    # Generate standard normal data
    Z = np.random.randn(n, p)
    X = Z @ L.T

    # Apply distribution violations if requested
    if distribution_type == "t":
        # Heavy-tailed: transform to t-distribution
        df = 4.0
        X = X / np.sqrt(np.random.chisquare(df, (n, p)) / df)
    elif distribution_type == "skew_normal":
        # Skewed: apply skew-normal transformation
        alpha = 5.0
        # Simple skewing via transformation
        X = np.where(X > 0, X, X * (1 + alpha * np.exp(-X**2)))

    metadata = {
        "n": n,
        "p": p,
        "rho": rho,
        "seed": seed,
        "distribution_type": distribution_type,
        "covariance_eigenvalues": np.linalg.eigvalsh(cov_matrix).tolist()
    }

    return X, metadata

def generate_distribution_violations(
    n: int,
    p: int,
    seed: int,
    violation_type: str = "heavy_tailed"
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate data with specific distributional violations.

    Args:
        n: Number of samples
        p: Number of features
        seed: Random seed
        violation_type: Type of violation ('heavy_tailed', 'skewed')

    Returns:
        Tuple of (data_matrix, metadata_dict)
    """
    np.random.seed(seed)

    if violation_type == "heavy_tailed":
        # Student's t-distribution with low degrees of freedom
        df = 3.0
        X = np.random.standard_t(df, size=(n, p))
    elif violation_type == "skewed":
        # Exponential distribution (highly skewed)
        X = np.random.exponential(scale=1.0, size=(n, p))
    else:
        raise ValueError(f"Unknown violation type: {violation_type}")

    metadata = {
        "n": n,
        "p": p,
        "seed": seed,
        "distribution_type": violation_type,
        "rho": 0.0
    }

    return X, metadata

def write_dataset_metadata(
    data: np.ndarray,
    metadata: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write dataset metadata and compute SHA256 hash of the data.

    Args:
        data: The generated data matrix
        metadata: Dictionary containing generation parameters
        output_path: Path to save the JSON metadata file
    """
    # Compute SHA256 hash of the data
    data_bytes = data.tobytes()
    sha256_hash = hashlib.sha256(data_bytes).hexdigest()

    # Prepare output dictionary
    output_data = {
        "sha256": sha256_hash,
        "rho": metadata.get("rho", 0.0),
        "n": metadata.get("n", 0),
        "p": metadata.get("p", 0),
        "distribution_type": metadata.get("distribution_type", "unknown"),
        "seed": metadata.get("seed", 0)
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Wrote metadata to {output_path}")
    logger.info(f"SHA256 hash: {sha256_hash}")

    # Verify file exists and hash matches
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to create file: {output_path}")

    with open(output_path, 'r') as f:
        loaded_data = json.load(f)

    if loaded_data["sha256"] != sha256_hash:
        raise RuntimeError(f"Hash mismatch: {loaded_data['sha256']} != {sha256_hash}")

    logger.info("Verification successful: file exists and SHA256 matches.")

def main():
    """
    Main entry point for generating a single dataset and its metadata.
    Example usage:
        python code/generate_data.py --n 100 --p 50 --rho 0.3 --seed 42 --out data/synthetic/42.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic dataset and metadata")
    parser.add_argument("--n", type=int, default=100, help="Number of samples")
    parser.add_argument("--p", type=int, default=50, help="Number of features")
    parser.add_argument("--rho", type=float, default=0.0, help="Correlation threshold")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dist", type=str, default="normal", choices=["normal", "t", "skew_normal"],
                        help="Distribution type")
    parser.add_argument("--out", type=str, required=True, help="Output path for metadata JSON")

    args = parser.parse_args()

    logger.info(f"Generating data: n={args.n}, p={args.p}, rho={args.rho}, seed={args.seed}, dist={args.dist}")

    data, metadata = generate_correlated_data(
        n=args.n,
        p=args.p,
        rho=args.rho,
        seed=args.seed,
        distribution_type=args.dist
    )

    write_dataset_metadata(data, metadata, args.out)

if __name__ == "__main__":
    main()
