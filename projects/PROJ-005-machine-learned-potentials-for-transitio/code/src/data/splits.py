"""
src/data/splits.py

Interface and skeleton for 5-Fold Leave-Ligand-Scaffold-Out (LLSO) logic.

This module defines the function signatures and data structures required for
generating cross-validation splits where entire ligand scaffolds are held out
to test generalization. The full implementation logic is deferred to T028.

Current state: Skeleton with function signatures only.
"""

from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


def compute_scaffold_clusters(
    graphs: List[Dict[str, Any]],
    ligand_column: str = "ligand_id"
) -> Dict[str, List[int]]:
    """
    Groups graph indices by their ligand scaffold identity.

    This is a skeleton function. In the full implementation (T028), this will:
    1. Extract the scaffold fingerprint (e.g., Murcko scaffold) for each ligand.
    2. Cluster ligands that share the same scaffold.
    3. Return a mapping: { scaffold_id: [graph_indices] }.

    Args:
        graphs: List of graph dictionaries containing metadata.
        ligand_column: The key in the graph dict identifying the ligand.

    Returns:
        A dictionary mapping scaffold identifiers to lists of graph indices.
        Currently returns an empty dictionary as a placeholder.
    """
    # TODO: Implement real scaffold clustering logic in T028
    # This will likely involve RDKit or similar chemistry toolkit to
    # compute Murcko scaffolds and group indices.
    return {}


def generate_llso_splits(
    scaffold_clusters: Dict[str, List[int]],
    n_folds: int = 5,
    seed: Optional[int] = None
) -> List[Dict[str, List[int]]]:
    """
    Generates 5-Fold Leave-Ligand-Scaffold-Out splits.

    This is a skeleton function. In the full implementation (T028), this will:
    1. Shuffle the unique scaffold clusters.
    2. Iterate to assign one cluster (or set of clusters) as the test set per fold.
    3. Ensure no scaffold appears in both train and test sets within the same fold.
    4. Return a list of dicts: [{'train_indices': [...], 'test_indices': [...]}].

    Args:
        scaffold_clusters: Output from compute_scaffold_clusters.
        n_folds: Number of folds (default 5).
        seed: Random seed for reproducibility.

    Returns:
        List of split dictionaries. Currently returns a list of empty dicts.
    """
    # TODO: Implement real split generation logic in T028
    # Logic must ensure strict separation of scaffolds between train and test.
    return [{"train_indices": [], "test_indices": []} for _ in range(n_folds)]


def save_splits_to_json(
    splits: List[Dict[str, List[int]]],
    output_path: str | Path
) -> None:
    """
    Saves the generated splits to a JSON file.

    This function is fully implemented as it handles I/O and serialization,
    which are stable regardless of the split logic.

    Args:
        splits: List of split dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)