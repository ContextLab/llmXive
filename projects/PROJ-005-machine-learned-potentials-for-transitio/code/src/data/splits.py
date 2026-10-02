"""
Data splitting module implementing Leave-Ligand-Scaffold-Out (LLSO) strategy.

This module generates train/val/test splits ensuring that no ligand scaffold
(represented by SMILES string) appears in both training and test sets.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd

# Conditional import for RDKit - will fail loudly if not available when needed
try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    Chem = None
    rdMolDescriptors = None

from src.utils.config import get_project_root
from src.utils.logging import get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[3]

def load_graphs_for_splitting(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed graphs parquet file for splitting.

    Args:
        graphs_path: Optional path to the graphs file. If None, uses default path.

    Returns:
        DataFrame containing graph data with required attributes.

    Raises:
        FileNotFoundError: If the graphs file does not exist.
        ValueError: If required columns are missing.
    """
    if graphs_path is None:
        graphs_path = get_project_root() / "data" / "processed" / "graphs.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")

    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)

    required_columns = ['ligand_class', 'metal_center', 'nodes', 'edges']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in graphs file: {missing_cols}")

    logger.info(f"Loaded {len(df)} graphs for splitting")
    return df

def _extract_coordination_sphere_smiles(nodes: Dict[str, Any]) -> str:
    """
    Extract SMILES string of the coordination sphere ligands from graph nodes.

    This function parses the node data to identify ligand atoms and constructs
    a SMILES representation of the coordination sphere.

    Args:
        nodes: Dictionary containing node attributes from the graph.

    Returns:
        SMILES string representing the coordination sphere, or empty string if
        extraction fails.
    """
    if not HAS_RDKIT:
        raise ImportError("RDKit is required for SMILES extraction. Install with: pip install rdkit")

    try:
        # Extract atomic numbers and positions from nodes
        atomic_numbers = nodes.get('atomic_numbers', [])
        positions = nodes.get('positions', [])
        is_ligand = nodes.get('is_ligand', [])

        if not atomic_numbers or not positions:
            return ""

        # Create RDKit molecule from atomic data
        mol = Chem.RWMol()

        for i, (atomic_num, pos) in enumerate(zip(atomic_numbers, positions)):
            atom = Chem.Atom(atomic_num)
            atom.SetProp("is_ligand", str(is_ligand[i]) if i < len(is_ligand) else "0")
            mol.AddAtom(atom)

        # Create bonds between adjacent atoms (assuming edges contain connectivity)
        # Note: This is a simplified approach; actual implementation may need edge data
        # For now, we'll return a canonical SMILES based on ligand atoms only
        ligand_atoms = [i for i, flag in enumerate(is_ligand) if flag]

        if not ligand_atoms:
            return ""

        # Create a fragment from ligand atoms
        # In a real implementation, we'd use edge data to build proper connectivity
        # Here we create a simple representation
        fragment = Chem.RWMol()
        for idx in ligand_atoms:
            atom = mol.GetAtomWithIdx(idx)
            fragment.AddAtom(Chem.Atom(atom.GetAtomicNum()))

        # Generate canonical SMILES
        smiles = Chem.MolToSmiles(fragment)
        return smiles if smiles else ""

    except Exception as e:
        logger.warning(f"Failed to extract SMILES from nodes: {e}")
        return ""

def _compute_scaffold_id(row: pd.Series) -> str:
    """
    Compute a unique scaffold ID for a graph based on its coordination sphere.

    Args:
        row: DataFrame row containing graph data.

    Returns:
        Unique scaffold ID string.
    """
    if not HAS_RDKIT:
        raise ImportError("RDKit is required for scaffold computation. Install with: pip install rdkit")

    try:
        # Extract nodes from the row
        nodes = row.get('nodes', {})
        if not nodes:
            return "unknown_scaffold"

        # Extract SMILES of coordination sphere
        smiles = _extract_coordination_sphere_smiles(nodes)

        if not smiles:
            return "unknown_scaffold"

        # Generate a canonical SMILES and use it as scaffold ID
        # Apply canonicalization to ensure consistency
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "invalid_scaffold"

        canonical_smiles = Chem.MolToSmiles(mol)
        return canonical_smiles

    except Exception as e:
        logger.warning(f"Failed to compute scaffold ID: {e}")
        return "error_scaffold"

def compute_scaffold_clusters(df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Group samples by unique ligand scaffold (SMILES string).

    Args:
        df: DataFrame containing graph data.

    Returns:
        Dictionary mapping scaffold SMILES to list of sample indices.
    """
    logger.info("Computing scaffold clusters...")

    if not HAS_RDKIT:
        raise ImportError("RDKit is required for scaffold clustering. Install with: pip install rdkit")

    # Compute scaffold ID for each sample
    df['scaffold_id'] = df.apply(_compute_scaffold_id, axis=1)

    # Group by scaffold ID
    scaffold_groups = df.groupby('scaffold_id').indices

    # Convert to dictionary of lists
    clusters = {scaffold: indices.tolist() for scaffold, indices in scaffold_groups.items()}

    logger.info(f"Found {len(clusters)} unique ligand scaffolds")

    return clusters

def generate_llso_splits(
    df: pd.DataFrame,
    clusters: Dict[str, List[int]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[int], List[int], List[int]]:
    """
    Generate train/val/test splits using Leave-Ligand-Scaffold-Out strategy.

    Ensures that no scaffold (SMILES string) appears in both train and test sets.

    Args:
        df: DataFrame containing graph data.
        clusters: Dictionary mapping scaffold SMILES to list of sample indices.
        train_ratio: Fraction of scaffolds for training.
        val_ratio: Fraction of scaffolds for validation.
        test_ratio: Fraction of scaffolds for testing.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_indices, val_indices, test_indices).

    Raises:
        ValueError: If ratios don't sum to 1.0 or if clustering fails.
    """
    np.random.seed(seed)

    # Validate ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")

    # Get list of scaffolds
    scaffolds = list(clusters.keys())
    np.random.shuffle(scaffolds)

    # Split scaffolds into train, val, test
    n_scaffolds = len(scaffolds)
    n_train = int(n_scaffolds * train_ratio)
    n_val = int(n_scaffolds * val_ratio)

    train_scaffolds = set(scaffolds[:n_train])
    val_scaffolds = set(scaffolds[n_train:n_train + n_val])
    test_scaffolds = set(scaffolds[n_train + n_val:])

    logger.info(f"Scaffold split: {len(train_scaffolds)} train, {len(val_scaffolds)} val, {len(test_scaffolds)} test")

    # Assign samples to splits based on their scaffold
    train_indices = []
    val_indices = []
    test_indices = []

    for scaffold, indices in clusters.items():
        if scaffold in train_scaffolds:
            train_indices.extend(indices)
        elif scaffold in val_scaffolds:
            val_indices.extend(indices)
        else:
            test_indices.extend(indices)

    # Sort indices for consistency
    train_indices = sorted(train_indices)
    val_indices = sorted(val_indices)
    test_indices = sorted(test_indices)

    logger.info(f"Sample split: {len(train_indices)} train, {len(val_indices)} val, {len(test_indices)} test")

    # Verify no scaffold overlap between train and test
    train_scaffold_set = set(df.iloc[train_indices]['scaffold_id'].unique())
    test_scaffold_set = set(df.iloc[test_indices]['scaffold_id'].unique())

    overlap = train_scaffold_set.intersection(test_scaffold_set)
    if overlap:
        raise ValueError(f"Scaffold overlap detected between train and test: {overlap}")

    return train_indices, val_indices, test_indices

def save_splits_to_json(
    splits: Tuple[List[int], List[int], List[int]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save split indices to JSON file.

    Args:
        splits: Tuple of (train_indices, val_indices, test_indices).
        output_path: Optional output path. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "splits.json"

    train_indices, val_indices, test_indices = splits

    splits_data = {
        "train": train_indices,
        "val": val_indices,
        "test": test_indices,
        "metadata": {
            "train_count": len(train_indices),
            "val_count": len(val_indices),
            "test_count": len(test_indices),
            "total_count": len(train_indices) + len(val_indices) + len(test_indices)
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(splits_data, f, indent=2)

    logger.info(f"Saved splits to {output_path}")
    logger.info(f"  Train: {len(train_indices)} samples")
    logger.info(f"  Val: {len(val_indices)} samples")
    logger.info(f"  Test: {len(test_indices)} samples")

    return output_path

def run_split_generation(
    graphs_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Path:
    """
    Run the complete split generation pipeline.

    Args:
        graphs_path: Path to the graphs file.
        output_path: Path for the output splits file.
        train_ratio: Fraction of scaffolds for training.
        val_ratio: Fraction of scaffolds for validation.
        test_ratio: Fraction of scaffolds for testing.
        seed: Random seed.

    Returns:
        Path to the saved splits file.
    """
    logger.info("Starting LLSO split generation")

    # Load graphs
    df = load_graphs_for_splitting(graphs_path)

    # Compute scaffold clusters
    clusters = compute_scaffold_clusters(df)

    # Generate splits
    splits = generate_llso_splits(
        df, clusters,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed
    )

    # Save splits
    output_path = save_splits_to_json(splits, output_path)

    logger.info("Split generation completed successfully")
    return output_path

def generate_splits() -> Path:
    """
    Main entry point for generating splits.

    This function loads the processed graphs, computes scaffold clusters,
    generates Leave-Ligand-Scaffold-Out splits, and saves them to disk.

    Returns:
        Path to the generated splits file.

    Raises:
        ImportError: If RDKit is not installed.
        FileNotFoundError: If the graphs file is not found.
        ValueError: If data is invalid for splitting.
    """
    return run_split_generation()

def main():
    """Command-line entry point for split generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate LLSO train/val/test splits")
    parser.add_argument("--graphs-path", type=str, help="Path to graphs file")
    parser.add_argument("--output-path", type=str, help="Path for splits output")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Training ratio")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation ratio")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Test ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    graphs_path = Path(args.graphs_path) if args.graphs_path else None
    output_path = Path(args.output_path) if args.output_path else None

    run_split_generation(
        graphs_path=graphs_path,
        output_path=output_path,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )

if __name__ == "__main__":
    main()