"""
Generate synthetic LoRA adapters with clustered base weights and save to Parquet.

This script creates a synthetic dataset of LoRA adapters with:
- Ranks ranging from 1 to 256
- Clustered base weights to inject correlations
- Deterministic random seed management for reproducibility

Output:
- data/raw/adapters.parquet: Parquet file containing adapter metadata and weights
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import sparse

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_logger, setup_logging
from utils.seeds import set_global_seed, validate_seed
from data.schema import AdapterSchema, validate_adapter_dataframe
from utils.exceptions import SimulationError

# Constants
DEFAULT_NUM_ADAPTERS = 1000
DEFAULT_RANK_MIN = 1
DEFAULT_RANK_MAX = 256
DEFAULT_NUM_CLUSTERS = 10
DEFAULT_WEIGHT_DIM = 768  # Hidden dimension for base weights
DEFAULT_OUTPUT_PATH = "data/raw/adapters.parquet"
DEFAULT_SEED = 42

def generate_clustered_base_weights(
    num_clusters: int,
    weight_dim: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generate clustered base weight vectors.

    Creates `num_clusters` base weight vectors with intentional correlations
    within clusters. Each cluster shares a common direction with added noise.

    Args:
        num_clusters: Number of weight clusters
        weight_dim: Dimension of each weight vector
        rng: NumPy random generator

    Returns:
        Array of shape (num_clusters, weight_dim) containing base weights
    """
    # Generate cluster centers
    cluster_centers = rng.standard_normal((num_clusters, weight_dim))
    # Normalize centers
    cluster_centers = cluster_centers / np.linalg.norm(cluster_centers, axis=1, keepdims=True)

    return cluster_centers

def generate_adapter_weights(
    adapter_id: int,
    rank: int,
    cluster_assignment: int,
    base_weights: np.ndarray,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate LoRA adapter weight matrices (A and B) with cluster-based correlations.

    Args:
        adapter_id: Unique adapter identifier
        rank: LoRA rank (1-256)
        cluster_assignment: Which cluster this adapter belongs to
        base_weights: Pre-generated cluster base weights
        rng: NumPy random generator

    Returns:
        Tuple of (A_matrix, B_matrix) as numpy arrays
    """
    weight_dim = base_weights.shape[1]
    cluster_center = base_weights[cluster_assignment]

    # Generate A matrix (rank x weight_dim) with cluster influence
    # Add cluster-specific bias to create correlation
    a_noise = rng.standard_normal((rank, weight_dim)) * 0.1
    a_matrix = cluster_center[:weight_dim] * 0.5 + a_noise

    # Generate B matrix (weight_dim x rank)
    b_matrix = rng.standard_normal((weight_dim, rank)) * 0.1

    # Ensure matrices are normalized for stability
    a_matrix = a_matrix / (np.linalg.norm(a_matrix) + 1e-8)
    b_matrix = b_matrix / (np.linalg.norm(b_matrix) + 1e-8)

    return a_matrix, b_matrix

def generate_adapters(
    num_adapters: int,
    rank_min: int,
    rank_max: int,
    num_clusters: int,
    weight_dim: int,
    seed: int,
    output_path: str
) -> pd.DataFrame:
    """
    Generate synthetic LoRA adapters and save to Parquet.

    Args:
        num_adapters: Number of adapters to generate
        rank_min: Minimum LoRA rank
        rank_max: Maximum LoRA rank
        num_clusters: Number of weight clusters
        weight_dim: Dimension of weight vectors
        seed: Random seed for reproducibility
        output_path: Path to save the Parquet file

    Returns:
        DataFrame containing adapter information
    """
    # Validate inputs
    validate_seed(seed)
    if rank_min < 1 or rank_max > 1024:
        raise SimulationError(f"Rank must be between 1 and 1024, got {rank_min}-{rank_max}")
    if num_adapters < 1:
        raise SimulationError(f"Number of adapters must be positive, got {num_adapters}")

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info(f"Starting adapter generation: {num_adapters} adapters, "
               f"ranks {rank_min}-{rank_max}, {num_clusters} clusters, seed={seed}")

    # Initialize random generator
    rng = set_global_seed(seed)

    # Generate cluster base weights
    logger.info(f"Generating {num_clusters} cluster base weights of dimension {weight_dim}")
    base_weights = generate_clustered_base_weights(num_clusters, weight_dim, rng)

    # Generate adapters
    logger.info(f"Generating {num_adapters} adapters...")
    adapters = []

    for i in range(num_adapters):
        # Random rank for this adapter
        rank = rng.integers(rank_min, rank_max + 1)

        # Assign to a cluster (with some randomness to create overlap)
        cluster_assignment = rng.integers(0, num_clusters)

        # Generate weight matrices
        a_matrix, b_matrix = generate_adapter_weights(
            i, rank, cluster_assignment, base_weights, rng
        )

        # Compute adapter properties
        adapter_size = a_matrix.size + b_matrix.size
        sparsity = float(np.mean(np.abs(a_matrix) < 0.01) + np.mean(np.abs(b_matrix) < 0.01)) / 2

        adapters.append({
            "adapter_id": i,
            "rank": int(rank),
            "cluster_id": int(cluster_assignment),
            "weight_dim": weight_dim,
            "a_shape": f"{a_matrix.shape[0]}x{a_matrix.shape[1]}",
            "b_shape": f"{b_matrix.shape[0]}x{b_matrix.shape[1]}",
            "a_matrix": a_matrix,
            "b_matrix": b_matrix,
            "adapter_size": int(adapter_size),
            "sparsity": float(sparsity)
        })

        if (i + 1) % 100 == 0:
            logger.debug(f"Generated {i + 1}/{num_adapters} adapters")

    # Create DataFrame
    df = pd.DataFrame(adapters)

    # Validate schema
    logger.info("Validating generated data against schema...")
    try:
        validate_adapter_dataframe(df)
        logger.info("Schema validation passed")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise SimulationError(f"Generated data failed schema validation: {e}")

    # Save to Parquet
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving {len(df)} adapters to {output_path}")
    # Store matrices as object arrays for Parquet
    df.to_parquet(output_path, engine='pyarrow', index=False)

    logger.info(f"Successfully saved adapters to {output_path}")
    logger.info(f"Summary: {len(df)} adapters, "
               f"ranks {df['rank'].min()}-{df['rank'].max()}, "
               f"avg size: {df['adapter_size'].mean():.0f} params")

    return df

def main():
    """Main entry point for adapter generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic LoRA adapters with clustered weights"
    )
    parser.add_argument(
        "--num-adapters",
        type=int,
        default=DEFAULT_NUM_ADAPTERS,
        help=f"Number of adapters to generate (default: {DEFAULT_NUM_ADAPTERS})"
    )
    parser.add_argument(
        "--rank-min",
        type=int,
        default=DEFAULT_RANK_MIN,
        help=f"Minimum LoRA rank (default: {DEFAULT_RANK_MIN})"
    )
    parser.add_argument(
        "--rank-max",
        type=int,
        default=DEFAULT_RANK_MAX,
        help=f"Maximum LoRA rank (default: {DEFAULT_RANK_MAX})"
    )
    parser.add_argument(
        "--num-clusters",
        type=int,
        default=DEFAULT_NUM_CLUSTERS,
        help=f"Number of weight clusters (default: {DEFAULT_NUM_CLUSTERS})"
    )
    parser.add_argument(
        "--weight-dim",
        type=int,
        default=DEFAULT_WEIGHT_DIM,
        help=f"Dimension of weight vectors (default: {DEFAULT_WEIGHT_DIM})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output path for Parquet file (default: {DEFAULT_OUTPUT_PATH})"
    )

    args = parser.parse_args()

    try:
        df = generate_adapters(
            num_adapters=args.num_adapters,
            rank_min=args.rank_min,
            rank_max=args.rank_max,
            num_clusters=args.num_clusters,
            weight_dim=args.weight_dim,
            seed=args.seed,
            output_path=args.output
        )
        print(f"Generated {len(df)} adapters successfully")
        return 0
    except Exception as e:
        print(f"Error generating adapters: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
