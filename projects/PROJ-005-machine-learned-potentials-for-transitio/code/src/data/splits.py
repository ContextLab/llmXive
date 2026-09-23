"""
src/data/splits.py

Implements Leave-Ligand-Scaffold-Out (LLSO) cross-validation logic.
Generates 5-Fold train/val/test splits ensuring no ligand scaffold appears
in both training and test sets.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd

from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_graphs_for_splitting(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the processed graphs dataframe required for splitting.
    Expects a parquet file containing graph data with 'ligand_scaffold' and 'graph_id' columns.
    """
    if graphs_path is None:
        # Default path based on project structure
        project_root = Path(__file__).resolve().parents[3]
        graphs_path = project_root / "data" / "processed" / "graphs.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}. "
                                "Run graph_construction.py (T016b) first.")

    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)

    required_cols = {'ligand_scaffold', 'graph_id', 'energy_dft'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns for splitting: {missing}")

    logger.info(f"Loaded {len(df)} graphs. Unique scaffolds: {df['ligand_scaffold'].nunique()}")
    return df


def compute_scaffold_clusters(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Groups graph IDs by their ligand scaffold.
    Returns a dictionary mapping scaffold_name -> list of graph_ids.
    """
    scaffold_groups = df.groupby('ligand_scaffold')['graph_id'].apply(list).to_dict()
    logger.info(f"Identified {len(scaffold_groups)} unique ligand scaffolds.")
    return scaffold_groups


def generate_llso_splits(
    scaffold_clusters: Dict[str, List[str]],
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, List[str]]]:
    """
    Generates n_folds splits using Leave-Ligand-Scaffold-Out logic.
    Ensures that for any given fold, the test set's scaffolds are disjoint
    from the training set's scaffolds.

    Returns:
        List of dicts, each containing 'train', 'val', 'test' lists of graph_ids.
    """
    np.random.seed(seed)
    unique_scaffolds = list(scaffold_clusters.keys())
    np.random.shuffle(unique_scaffolds)

    # Distribute scaffolds into n_folds buckets
    # If fewer scaffolds than folds, we adjust logic to ensure we don't crash,
    # but standard LLSO assumes enough diversity.
    n_scaffolds = len(unique_scaffolds)
    if n_scaffolds < n_folds:
        logger.warning(f"Number of scaffolds ({n_scaffolds}) is less than folds ({n_folds}). "
                       "Adjusting fold distribution.")
        # In this edge case, we might have to duplicate or just use available
        # For robustness, we'll cycle or pad if strictly necessary, but let's
        # assume typical case where n_scaffolds >= n_folds.
        # If strictly less, we can't do strict LLSO with n_folds.
        # We will proceed by assigning each scaffold to a fold 0..n-1 cyclically.
        fold_assignments = {s: i % n_folds for i, s in enumerate(unique_scaffolds)}
    else:
        fold_assignments = {s: i % n_folds for i, s in enumerate(unique_scaffolds)}

    splits = []

    for i in range(n_folds):
        test_scaffolds = [s for s, f in fold_assignments.items() if f == i]
        # Val set: usually a portion of the remaining, or a separate fold.
        # Standard 5-fold CV: Fold i is Test, Fold (i+1)%5 is Val, Rest is Train.
        # Or simply: Test = Fold i, Train+Val = Rest. Then split Rest.
        # Let's do: Test = Fold i, Val = Fold (i+1)%n_folds, Train = Rest.
        # This ensures strict separation.

        val_fold_idx = (i + 1) % n_folds
        val_scaffolds = [s for s, f in fold_assignments.items() if f == val_fold_idx]
        train_scaffolds = [s for s, f in fold_assignments.items() if f not in (i, val_fold_idx)]

        # Map back to graph IDs
        test_ids = []
        for s in test_scaffolds:
            test_ids.extend(scaffold_clusters[s])

        val_ids = []
        for s in val_scaffolds:
            val_ids.extend(scaffold_clusters[s])

        train_ids = []
        for s in train_scaffolds:
            train_ids.extend(scaffold_clusters[s])

        splits.append({
            "fold": i,
            "train": train_ids,
            "val": val_ids,
            "test": test_ids
        })

        logger.info(f"Fold {i}: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")

    return splits


def save_splits_to_json(
    splits: List[Dict[str, List[str]]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Saves the generated splits to a JSON file.
    """
    if output_path is None:
        project_root = Path(__file__).resolve().parents[3]
        output_path = project_root / "data" / "processed" / "splits.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)

    logger.info(f"Splits saved to {output_path}")
    return output_path


def run_split_generation(
    graphs_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, List[str]]]:
    """
    Main entry point to generate and save LLSO splits.
    """
    logger.info("Starting LLSO split generation...")
    df = load_graphs_for_splitting(graphs_path)
    clusters = compute_scaffold_clusters(df)
    splits = generate_llso_splits(clusters, n_folds=n_folds, seed=seed)
    save_splits_to_json(splits, output_path)
    return splits


def main():
    """
    CLI entry point for generating splits.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Generate LLSO splits")
    parser.add_argument("--graphs", type=str, default=None, help="Path to graphs.parquet")
    parser.add_argument("--output", type=str, default=None, help="Path to output splits.json")
    parser.add_argument("--folds", type=int, default=5, help="Number of folds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    run_split_generation(
        graphs_path=Path(args.graphs) if args.graphs else None,
        output_path=Path(args.output) if args.output else None,
        n_folds=args.folds,
        seed=args.seed
    )


if __name__ == "__main__":
    main()