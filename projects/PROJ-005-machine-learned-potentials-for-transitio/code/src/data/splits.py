"""
src/data/splits.py

Implements 5-Fold Leave-Ligand-Scaffold-Out (LLSO) cross-validation logic.
This module groups graphs by their ligand scaffold and ensures that graphs
sharing the same scaffold are not present in both training and test sets
simultaneously.

Dependencies:
  - pandas: for data manipulation
  - numpy: for randomization
  - json: for saving split configurations
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd

# Import logging utility from project
from src.utils.logging import get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parents[3]

def load_graphs_for_splitting(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the processed graphs from parquet file.
    Expects a DataFrame with at least:
      - 'ligand_scaffold': string identifier for the scaffold
      - 'graph_id': unique identifier for the graph (optional, but recommended)
    """
    if graphs_path is None:
        graphs_path = get_project_root() / "data" / "processed" / "graphs.parquet"
    
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}. "
                                "Ensure T016 (graph_construction) has been run.")
    
    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)
    
    required_cols = ['ligand_scaffold']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in graphs file: {missing}")
    
    return df

def compute_scaffold_clusters(df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Groups graph indices by their ligand scaffold.
    
    Returns:
      Dict mapping scaffold_id -> list of row indices belonging to that scaffold
    """
    logger.info("Computing scaffold clusters for LLSO...")
    
    # Group by scaffold and collect indices
    clusters = df.groupby('ligand_scaffold').indices
    
    # Convert to a serializable format (dict of lists)
    cluster_map = {k: list(v) for k, v in clusters.items()}
    
    logger.info(f"Found {len(cluster_map)} unique ligand scaffolds.")
    return cluster_map

def generate_llso_splits(
    cluster_map: Dict[str, List[int]],
    n_folds: int = 5,
    seed: int = 42
) -> List[Dict[str, List[int]]]:
    """
    Generates 5-Fold Leave-Ligand-Scaffold-Out splits.
    
    Logic:
      1. Shuffle the list of unique scaffolds.
      2. Assign each scaffold to a fold.
      3. For each fold i:
         - Test set: all graphs belonging to scaffolds assigned to fold i.
         - Train set: all graphs belonging to scaffolds NOT in fold i.
    
    Args:
      cluster_map: Output from compute_scaffold_clusters
      n_folds: Number of folds (default 5)
      seed: Random seed for reproducibility
    
    Returns:
      List of dicts, each containing 'train_indices' and 'test_indices'
    """
    logger.info(f"Generating {n_folds}-fold LLSO splits...")
    
    scaffolds = list(cluster_map.keys())
    rng = np.random.default_rng(seed)
    rng.shuffle(scaffolds)
    
    n_scaffolds = len(scaffolds)
    fold_assignments = {}
    
    # Assign scaffolds to folds
    for i, scaffold in enumerate(scaffolds):
        fold_idx = i % n_folds
        fold_assignments[scaffold] = fold_idx
    
    splits = []
    for fold_i in range(n_folds):
        test_scaffolds = [s for s, f in fold_assignments.items() if f == fold_i]
        train_scaffolds = [s for s, f in fold_assignments.items() if f != fold_i]
        
        test_indices = []
        train_indices = []
        
        for scaffold in test_scaffolds:
            test_indices.extend(cluster_map[scaffold])
        
        for scaffold in train_scaffolds:
            train_indices.extend(cluster_map[scaffold])
        
        # Sort indices for consistency
        train_indices.sort()
        test_indices.sort()
        
        splits.append({
            "fold": fold_i,
            "train_indices": train_indices,
            "test_indices": test_indices,
            "train_scaffolds": train_scaffolds,
            "test_scaffolds": test_scaffolds
        })
        
        logger.info(f"Fold {fold_i}: Train={len(train_indices)}, Test={len(test_indices)}")
    
    return splits

def save_splits_to_json(
    splits: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Saves the generated splits to a JSON file.
    
    Args:
      splits: List of split dictionaries
      output_path: Path to save the JSON file. Defaults to data/processed/splits.json
    
    Returns:
      Path to the saved file
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "splits.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving splits to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)
    
    return output_path

def main():
    """
    Main entry point to generate and save LLSO splits.
    """
    try:
        # 1. Load graphs
        df = load_graphs_for_splitting()
        
        # 2. Compute clusters
        cluster_map = compute_scaffold_clusters(df)
        
        if len(cluster_map) < 5:
            logger.warning(f"Only {len(cluster_map)} unique scaffolds found. "
                           "Cannot perform 5-fold split effectively. Proceeding anyway.")
        
        # 3. Generate splits
        splits = generate_llso_splits(cluster_map, n_folds=5, seed=42)
        
        # 4. Save splits
        save_path = save_splits_to_json(splits)
        
        logger.info(f"Successfully generated {len(splits)} folds. Saved to {save_path}")
        
        # Log summary
        for split in splits:
            logger.info(f"Fold {split['fold']}: Train={len(split['train_indices'])}, "
                        f"Test={len(split['test_indices'])}")
            
    except Exception as e:
        logger.error(f"Failed to generate splits: {e}")
        raise

if __name__ == "__main__":
    main()
