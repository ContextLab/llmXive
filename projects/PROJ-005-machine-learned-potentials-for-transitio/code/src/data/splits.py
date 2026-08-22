"""
Splitting logic for Leave-Ligand-Scaffold-Out (LLSO) cross-validation.

This module implements the 5-Fold LLSO logic required for US2.
It groups samples by ligand scaffold and ensures that all samples
sharing a scaffold are kept together in either training or test sets.
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd

# Import config utilities to find project root
from src.utils.config import get_project_root

logger = logging.getLogger(__name__)


def _hash_scaffold(scaffold_smiles: str) -> str:
    """
    Create a deterministic hash for a scaffold SMILES string.
    Used to group identical scaffolds.
    """
    if not scaffold_smiles:
        return "unknown_scaffold"
    # Normalize: strip whitespace, lowercase
    normalized = scaffold_smiles.strip().lower()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:8]


def compute_scaffold_clusters(graphs_df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Compute clusters of graph indices based on ligand scaffolds.

    Args:
        graphs_df: DataFrame containing graph data with 'scaffold_smiles' column.

    Returns:
        Dictionary mapping scaffold_hash -> list of graph indices.
    """
    if 'scaffold_smiles' not in graphs_df.columns:
        raise ValueError("Input DataFrame must contain 'scaffold_smiles' column.")

    clusters: Dict[str, List[int]] = {}

    # Iterate and group by scaffold
    for idx, row in graphs_df.iterrows():
        scaffold_hash = _hash_scaffold(row['scaffold_smiles'])
        if scaffold_hash not in clusters:
            clusters[scaffold_hash] = []
        clusters[scaffold_hash].append(idx)

    logger.info(f"Computed {len(clusters)} unique scaffold clusters.")
    return clusters


def generate_llso_splits(
    clusters: Dict[str, List[int]],
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate 5-Fold Leave-Ligand-Scaffold-Out splits.

    This function distributes scaffold clusters into folds such that:
    1. All indices belonging to a single cluster are in the same fold.
    2. Each fold serves as a test set exactly once.

    Args:
        clusters: Dictionary mapping scaffold_hash -> list of graph indices.
        n_folds: Number of folds (default 5).
        seed: Random seed for shuffling clusters.

    Returns:
        List of dictionaries, each containing 'train_indices' and 'test_indices'.
    """
    if len(clusters) < n_folds:
        logger.warning(
            f"Number of unique scaffolds ({len(clusters)}) is less than "
            f"requested folds ({n_folds}). Some folds may be empty or "
            f"contain very few samples."
        )

    # Extract cluster keys and shuffle them deterministically
    cluster_keys = list(clusters.keys())
    rng = np.random.default_rng(seed)
    rng.shuffle(cluster_keys)

    # Distribute clusters into folds
    folds: List[List[str]] = [[] for _ in range(n_folds)]
    for i, key in enumerate(cluster_keys):
        fold_idx = i % n_folds
        folds[fold_idx].append(key)

    splits = []
    total_samples = sum(len(v) for v in clusters.values())

    for i in range(n_folds):
        # Test set: all indices from clusters assigned to this fold
        test_clusters = folds[i]
        test_indices = []
        for key in test_clusters:
            test_indices.extend(clusters[key])

        # Train set: all indices from all other clusters
        train_indices = []
        for j, key_list in enumerate(folds):
            if j != i:
                for key in key_list:
                    train_indices.extend(clusters[key])

        # Sort indices for determinism
        test_indices.sort()
        train_indices.sort()

        split_info = {
            "fold": i,
            "train_indices": train_indices,
            "test_indices": test_indices,
            "train_count": len(train_indices),
            "test_count": len(test_indices),
            "test_scaffolds": test_clusters
        }
        splits.append(split_info)

        logger.info(
            f"Fold {i}: Train={len(train_indices)}, Test={len(test_indices)} "
            f"(Scaffolds: {len(test_clusters)})"
        )

    return splits


def save_splits_to_json(splits: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the generated splits to a JSON file.

    Args:
        splits: List of split dictionaries.
        output_path: Path to the output JSON file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)

    logger.info(f"Saved splits to {output_path}")


def load_graphs_for_splitting(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Helper to load processed graphs for splitting.
    Expects a parquet file with 'scaffold_smiles' column.
    """
    if graphs_path is None:
        project_root = get_project_root()
        graphs_path = project_root / "data" / "processed" / "graphs.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}")

    df = pd.read_parquet(graphs_path)
    if 'scaffold_smiles' not in df.columns:
        raise ValueError(
            f"Graphs file missing required column 'scaffold_smiles'. "
            f"Available columns: {list(df.columns)}"
        )
    return df


def main() -> None:
    """
    Main entry point to generate and save LLSO splits.
    Reads from data/processed/graphs.parquet and writes to data/processed/splits.json.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Load graphs
        logger.info("Loading graphs for splitting...")
        graphs_df = load_graphs_for_splitting()
        logger.info(f"Loaded {len(graphs_df)} graphs.")

        # 2. Compute clusters
        logger.info("Computing scaffold clusters...")
        clusters = compute_scaffold_clusters(graphs_df)

        # 3. Generate splits
        logger.info("Generating 5-Fold LLSO splits...")
        splits = generate_llso_splits(clusters, n_folds=5, seed=42)

        # 4. Save splits
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "splits.json"
        save_splits_to_json(splits, output_path)

        logger.info("LLSO splits generation completed successfully.")

    except Exception as e:
        logger.error(f"Failed to generate splits: {e}", exc_info=True)
        raise
