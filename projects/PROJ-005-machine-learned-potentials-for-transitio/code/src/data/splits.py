"""
Module: splits.py
Purpose: Implement Leave-Ligand-Scaffold-Out (LLSO) cross-validation strategy.

This module provides the infrastructure to generate train/validation/test splits
where the test set contains ligand scaffolds that were NOT present in the training set.
This ensures the model's generalizability is evaluated across distinct chemical scaffolds.

References:
- Research Question: Generalizability of predictive models across distinct chemical scaffolds.
- Method: Leave-Ligand-Scaffold-Out (LLSO) Cross-Validation.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set

import numpy as np
import pandas as pd

from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_project_root() -> Path:
    """
    Returns the project root directory (code/).
    Assumes this script is run from within the code/ directory or via python -m.
    """
    # Standard assumption for this project structure:
    # The script is located at code/src/data/splits.py
    # The root is code/
    current_file = Path(__file__).resolve()
    # Navigate up two levels: src/data -> src -> code
    return current_file.parent.parent.parent


def load_graphs_for_splitting() -> pd.DataFrame:
    """
    Loads the processed graphs dataframe required for splitting.
    Expects the file to be at: code/data/processed/graphs.parquet

    Returns:
        pd.DataFrame: The loaded graph data containing at least 'ligand_scaffold' column.

    Raises:
        FileNotFoundError: If the graphs file does not exist.
        ValueError: If required columns are missing.
    """
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(
            f"Graphs file not found at {graphs_path}. "
            "Please run data ingestion and graph construction tasks first."
        )

    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)

    required_cols = ['ligand_scaffold', 'reaction_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in graphs data: {missing_cols}. "
            "Ensure graph construction includes ligand scaffold classification."
        )

    logger.info(f"Loaded {len(df)} graphs for splitting.")
    return df


def compute_scaffold_clusters(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Computes clusters of reaction IDs grouped by their unique ligand scaffold.
    This is the core of the LLSO strategy: all reactions sharing a scaffold
    must be kept together in a single fold.

    Args:
        df (pd.DataFrame): The graphs dataframe.

    Returns:
        Dict[str, List[str]]: Mapping of scaffold_name -> list of reaction_ids.
    """
    logger.info("Computing scaffold clusters...")
    clusters = df.groupby('ligand_scaffold')['reaction_id'].apply(list).to_dict()
    logger.info(f"Found {len(clusters)} unique ligand scaffolds.")
    return clusters


def generate_llso_splits(
    clusters: Dict[str, List[str]],
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, Set[str]]]:
    """
    Generates N-Fold Leave-Ligand-Scaffold-Out splits.

    Logic:
    1. Randomly shuffle the list of unique scaffolds.
    2. Distribute scaffolds into N folds.
    3. For each fold i:
       - Test set = reactions belonging to scaffolds in fold i.
       - Train set = reactions belonging to scaffolds NOT in fold i.
       - (Optional) Val set can be derived from the Train set or a separate hold-out
         of scaffolds if a 3-way split is strictly required. For standard K-Fold CV,
         we usually return Train/Test pairs. This implementation returns Train/Test sets.

    Args:
        clusters (Dict[str, List[str]]): Scaffold to reaction_id mapping.
        n_folds (int): Number of folds (default 5).
        seed (int): Random seed for reproducibility.

    Returns:
        List[Dict[str, Set[str]]]: List of dicts with keys 'train_ids', 'test_ids'.
    """
    logger.info(f"Generating {n_folds}-fold LLSO splits...")
    rng = np.random.default_rng(seed)

    scaffolds = list(clusters.keys())
    rng.shuffle(scaffolds)

    # Split scaffolds into n_folds groups
    fold_scaffolds = np.array_split(scaffolds, n_folds)

    splits = []
    for i in range(n_folds):
        test_scaffolds = set(fold_scaffolds[i])
        train_scaffolds = set(scaffolds) - test_scaffolds

        test_ids = set()
        train_ids = set()

        for scaffold, ids in clusters.items():
            if scaffold in test_scaffolds:
                test_ids.update(ids)
            else:
                train_ids.update(ids)

        splits.append({
            'train_ids': train_ids,
            'test_ids': test_ids,
            'fold_index': i,
            'num_train': len(train_ids),
            'num_test': len(test_ids)
        })
        logger.info(f"Fold {i}: Train={len(train_ids)}, Test={len(test_ids)} (Scaffolds: {len(test_scaffolds)})")

    return splits


def save_splits_to_json(splits: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Saves the generated splits to a JSON file.

    Args:
        splits (List[Dict]): The list of split dictionaries.
        output_path (Path, optional): Path to save the JSON. Defaults to code/data/processed/splits.json.

    Returns:
        Path: The path to the saved file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "splits.json"

    # Convert sets to lists for JSON serialization
    serializable_splits = []
    for split in splits:
        serializable_splits.append({
            'fold_index': split['fold_index'],
            'train_ids': list(split['train_ids']),
            'test_ids': list(split['test_ids']),
            'num_train': split['num_train'],
            'num_test': split['num_test']
        })

    logger.info(f"Saving splits to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(serializable_splits, f, indent=2)

    return output_path


def run_split_generation(n_folds: int = 5, seed: int = 42) -> Path:
    """
    Main entry point to generate and save LLSO splits.

    Args:
        n_folds (int): Number of folds.
        seed (int): Random seed.

    Returns:
        Path: Path to the saved splits file.
    """
    df = load_graphs_for_splitting()
    clusters = compute_scaffold_clusters(df)
    splits = generate_llso_splits(clusters, n_folds, seed)
    return save_splits_to_json(splits)


def main():
    """
    CLI entry point for generating splits.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate LLSO splits")
    parser.add_argument('--n_folds', type=int, default=5, help="Number of folds")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    args = parser.parse_args()

    try:
        output_path = run_split_generation(n_folds=args.n_folds, seed=args.seed)
        logger.info(f"Successfully generated splits at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate splits: {e}")
        raise


if __name__ == "__main__":
    main()