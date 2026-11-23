"""
Geometry metrics computation for dimensionality reduction evaluation.

Computes Global Linearity (Trustworthiness) and Local Continuity (LCA)
on the RAW high-dimensional space (pre-log-CPM).
"""
import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import trustworthiness
from scipy.spatial.distance import cdist

# Import from config for paths and seeds
from config import Config

# Import preprocessing utilities for deterministic sampling
# Note: We import the function, not the module, to match the API surface
from preprocess import deterministic_sample_cells

logger = logging.getLogger(__name__)


class GeometryError(Exception):
    """Custom exception for geometry computation errors."""
    pass


def compute_linearity_metric(
    X_high_dim: np.ndarray,
    X_embedding: np.ndarray,
    k: int = 15,
    random_state: Optional[int] = None
) -> float:
    """
    Compute Global Linearity using the Trustworthiness metric.

    Trustworthiness measures the extent to which local neighborhoods in the
    high-dimensional space are preserved in the embedding.

    Args:
        X_high_dim: High-dimensional data matrix (n_samples, n_features).
        X_embedding: Low-dimensional embedding matrix (n_samples, n_components).
        k: Number of neighbors to consider.
        random_state: Random seed for reproducibility (used internally by sklearn).

    Returns:
        Trustworthiness score (0 to 1, higher is better).
    """
    if X_high_dim.shape[0] != X_embedding.shape[0]:
        raise GeometryError(
            f"Shape mismatch: High-dim rows {X_high_dim.shape[0]} != "
            f"Embedding rows {X_embedding.shape[0]}"
        )

    if X_high_dim.shape[0] <= k:
        logger.warning(
            f"Sample size ({X_high_dim.shape[0]}) <= k ({k}). "
            "Trustworthiness calculation may be unreliable."
        )

    try:
        # sklearn's trustworthiness expects 2D arrays
        score = trustworthiness(
            X_high_dim,
            X_embedding,
            n_neighbors=k,
            metric='euclidean',
            random_state=random_state
        )
        return float(score)
    except Exception as e:
        raise GeometryError(f"Failed to compute trustworthiness: {e}") from e


def compute_continuity_metric(
    X_high_dim: np.ndarray,
    X_embedding: np.ndarray,
    k: int = 15,
    random_state: Optional[int] = None
) -> float:
    """
    Compute Local Continuity (Continuity metric / LCA).

    Continuity is the complement of Trustworthiness computed on the embedding
    space relative to the high-dimensional space (or vice versa depending on
    specific definition, but typically: Continuity = 1 - Trustworthiness(embedding, high_dim)
    is not standard. Standard Continuity is often defined as the average fraction
    of neighbors in high-dim that are also neighbors in low-dim.

    However, sklearn's `trustworthiness` is asymmetric.
    Trustworthiness(X, Y): Neighbors of X in X-space are preserved in Y-space.
    Continuity is often defined as:
    Continuity(X, Y) = 1 - (1/|N|) * sum_{i} sum_{j in N_i(X), j not in N_i(Y)} ...

    A common approach to get Continuity is to compute Trustworthiness(Y, X)
    (i.e., neighbors in embedding are preserved in high-dim) or use a specific
    continuity implementation.

    For this implementation, we calculate Continuity as the complement of the
    "missing neighbors" penalty in the embedding relative to high-dim.
    Since sklearn only provides `trustworthiness`, and `continuity` is not
    directly available, we can compute it as:
    Continuity = 1 - (Trustworthiness of embedding wrt high-dim? No.)

    Let's use the standard definition:
    Continuity is the extent to which local neighborhoods in the EMBEDDING
    are preserved in the high-dimensional space.
    So we compute Trustworthiness(X_embedding, X_high_dim).

    Args:
        X_high_dim: High-dimensional data matrix.
        X_embedding: Low-dimensional embedding matrix.
        k: Number of neighbors.
        random_state: Random seed.

    Returns:
        Continuity score (0 to 1, higher is better).
    """
    if X_high_dim.shape[0] != X_embedding.shape[0]:
        raise GeometryError(
            f"Shape mismatch for continuity: High-dim rows {X_high_dim.shape[0]} != "
            f"Embedding rows {X_embedding.shape[0]}"
        )

    if X_high_dim.shape[0] <= k:
        logger.warning(
            f"Sample size ({X_high_dim.shape[0]}) <= k ({k}). "
            "Continuity calculation may be unreliable."
        )

    try:
        # Compute Trustworthiness of Embedding relative to High-Dim
        # This measures if neighbors in embedding are also neighbors in high-dim
        score = trustworthiness(
            X_embedding,
            X_high_dim,
            n_neighbors=k,
            metric='euclidean',
            random_state=random_state
        )
        return float(score)
    except Exception as e:
        raise GeometryError(f"Failed to compute continuity: {e}") from e


def compute_geometry_metrics(
    X_high_dim: np.ndarray,
    X_embedding: np.ndarray,
    k: int = 15,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Compute both Global Linearity and Local Continuity metrics.

    Args:
        X_high_dim: High-dimensional data matrix (RAW counts).
        X_embedding: Low-dimensional embedding matrix (PCA, t-SNE, UMAP).
        k: Number of neighbors (default 15).
        random_state: Random seed.

    Returns:
        Dictionary with 'trustworthiness' and 'continuity' scores.
    """
    if X_high_dim.ndim == 1:
        X_high_dim = X_high_dim.reshape(-1, 1)
    if X_embedding.ndim == 1:
        X_embedding = X_embedding.reshape(-1, 1)

    trust_score = compute_linearity_metric(X_high_dim, X_embedding, k, random_state)
    cont_score = compute_continuity_metric(X_high_dim, X_embedding, k, random_state)

    return {
        "trustworthiness": trust_score,
        "continuity": cont_score
    }


def run_geometry_analysis(
    accession: str,
    raw_counts_path: str,
    embedding_path: str,
    output_dir: str,
    k: int = 15
) -> Dict[str, Any]:
    """
    Run full geometry analysis for a single accession.

    1. Load raw counts.
    2. Perform deterministic sampling if n_cells > 10,000.
    3. Load corresponding embedding (must be sampled to match).
    4. Compute metrics.
    5. Save results.

    Args:
        accession: GSE accession ID.
        raw_counts_path: Path to the raw count matrix (CSV/TSV).
        embedding_path: Path to the embedding matrix (CSV/TSV).
        output_dir: Directory to save results.
        k: Number of neighbors.

    Returns:
        Dictionary containing results.
    """
    logger.info(f"Running geometry analysis for {accession}")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load raw counts
    # Assuming the raw counts are stored as a DataFrame where rows are cells
    # and columns are genes.
    try:
        df_raw = pd.read_csv(raw_counts_path, index_col=0)
    except Exception as e:
        raise GeometryError(f"Failed to load raw counts from {raw_counts_path}: {e}")

    logger.info(f"Loaded raw counts: {df_raw.shape}")

    # Deterministic sampling if n_cells > 10,000
    # Seed is derived from accession hash
    seed = int(hashlib.md5(accession.encode()).hexdigest(), 16) % (2**32)
    max_cells = 10000

    if df_raw.shape[0] > max_cells:
        logger.info(
            f"Sampling {max_cells} cells from {df_raw.shape[0]} using seed {seed}"
        )
        # We need to sample rows (cells).
        # deterministic_sample_cells from preprocess.py is designed for AnnData,
        # but here we have a DataFrame. We can implement a simple deterministic sample
        # or adapt the logic. Since the API surface shows `deterministic_sample_cells`
        # exists in `preprocess`, let's assume it can handle a DataFrame or we
        # implement the logic here to be safe and self-contained.
        # Given the constraint "import real names", and the function signature in
        # preprocess.py usually expects AnnData, let's implement a lightweight
        # sampling here to ensure we don't break if the preprocess function is
        # strictly AnnData-bound.

        # Deterministic sampling logic:
        indices = df_raw.index.tolist()
        np.random.seed(seed)
        # Shuffle indices deterministically
        shuffled_indices = np.random.permutation(indices)
        sampled_indices = shuffled_indices[:max_cells]
        df_sampled = df_raw.loc[sampled_indices]
    else:
        df_sampled = df_raw

    logger.info(f"Sampled data shape: {df_sampled.shape}")

    # Prepare X_high_dim (cells x genes)
    # Ensure numeric
    X_high_dim = df_sampled.values.astype(np.float64)

    # Load embedding
    try:
        df_emb = pd.read_csv(embedding_path, index_col=0)
    except Exception as e:
        raise GeometryError(f"Failed to load embedding from {embedding_path}: {e}")

    # The embedding file might have more rows if it wasn't sampled.
    # We must ensure the embedding matches the sampled cells.
    # If the embedding was generated from the SAME sampling process (which it should be),
    # the index should match. If not, we intersect.
    common_idx = df_sampled.index.intersection(df_emb.index)
    if len(common_idx) == 0:
        raise GeometryError(
            "No common indices between sampled raw counts and embedding. "
            "Ensure embeddings were generated from the same sampled data."
        )

    X_high_dim = X_high_dim.loc[common_idx].values
    X_embedding = df_emb.loc[common_idx].values

    logger.info(
        f"Computing metrics on {X_high_dim.shape[0]} cells, "
        f"{X_high_dim.shape[1]} genes, embedding dim {X_embedding.shape[1]}"
    )

    metrics = compute_geometry_metrics(X_high_dim, X_embedding, k=k, random_state=seed)

    result = {
        "accession": accession,
        "n_cells": int(X_high_dim.shape[0]),
        "n_genes": int(X_high_dim.shape[1]),
        "embedding_dim": int(X_embedding.shape[1]),
        "k": k,
        "seed": seed,
        "metrics": metrics
    }

    # Save results
    output_path = Path(output_dir) / f"geometry_{accession}.json"
    save_geometry_results(result, output_path)

    return result


def save_geometry_results(result: Dict[str, Any], output_path: str) -> None:
    """Save geometry results to a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Saved geometry results to {output_path}")
    except Exception as e:
        raise GeometryError(f"Failed to save results to {output_path}: {e}") from e


def main() -> None:
    """
    Main entry point for geometry analysis.
    Expects command line arguments or environment configuration.
    For now, assumes run via Snakemake or direct invocation with args.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 5:
        logger.error(
            "Usage: python geometry.py <accession> <raw_counts_path> <embedding_path> <output_dir> [k]"
        )
        sys.exit(1)

    accession = sys.argv[1]
    raw_counts_path = sys.argv[2]
    embedding_path = sys.argv[3]
    output_dir = sys.argv[4]
    k = int(sys.argv[5]) if len(sys.argv) > 5 else 15

    try:
        result = run_geometry_analysis(
            accession=accession,
            raw_counts_path=raw_counts_path,
            embedding_path=embedding_path,
            output_dir=output_dir,
            k=k
        )
        logger.info(f"Analysis complete. Metrics: {result['metrics']}")
    except GeometryError as e:
        logger.error(f"Geometry analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()