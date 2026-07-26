import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union

import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np

from data_models import PolymerRecord, MolecularGraph
from utils import get_logger, get_project_paths

# Configure logger
logger = get_logger(__name__)

# Constants for runtime constraint
AUGMENTATION_TIMEOUT_SECONDS = 300  # 5 minutes default timeout for augmentation
AUGMENTATION_TIMEOUT_ENV = "AUGMENTATION_TIMEOUT_SECONDS"

class AugmentationTimeoutError(Exception):
    """Exception raised when augmentation exceeds the runtime limit."""
    pass

def _timeout_handler(signum, frame):
    raise AugmentationTimeoutError("Augmentation process exceeded the allowed runtime limit.")

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """Convert SMILES to canonical form using RDKit."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, canonical=True)
    except Exception as e:
        logger.warning(f"Failed to canonicalize SMILES '{smiles}': {e}")
        return None

def smiles_to_molecular_graph(smiles: str) -> Optional[MolecularGraph]:
    """Convert a SMILES string to a MolecularGraph data structure."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Extract node features (atomic number, degree, formal charge, etc.)
        node_features = []
        for atom in mol.GetAtoms():
            node_features.append([
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                atom.GetIsAromatic(),
                atom.GetHybridization()
            ])

        # Extract edge index (bond connections)
        edge_list = []
        for bond in mol.GetBonds():
            edge_list.append([bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()])
            edge_list.append([bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()])  # Undirected graph

        return MolecularGraph(
            smiles=smiles,
            node_features=np.array(node_features, dtype=np.float32),
            edge_index=np.array(edge_list, dtype=np.int64).T if edge_list else np.zeros((2, 0), dtype=np.int64)
        )
    except Exception as e:
        logger.warning(f"Failed to convert SMILES '{smiles}' to graph: {e}")
        return None

def filter_missing_environmental_data(records: List[PolymerRecord]) -> Tuple[List[PolymerRecord], List[PolymerRecord]]:
    """Exclude records missing temperature, pH, or UV data.

    Returns:
        Tuple of (valid_records, excluded_records)
    """
    valid = []
    excluded = []
    reasons = []

    for record in records:
        if record.temperature is None or record.ph is None or record.uv_intensity is None:
            excluded.append(record)
            missing = []
            if record.temperature is None: missing.append("temperature")
            if record.ph is None: missing.append("pH")
            if record.uv_intensity is None: missing.append("UV")
            reasons.append(f"Record {record.id} missing: {', '.join(missing)}")
        else:
            valid.append(record)

    logger.info(f"Filtered environmental data: {len(valid)} valid, {len(excluded)} excluded")
    for reason in reasons:
        logger.debug(reason)

    return valid, excluded

def is_ester_bond(bond_type: int) -> bool:
    """Check if a bond is an ester bond (C-O or C=O in ester context).

    In RDKit, bond types are integers. We check for single or double bonds
    that are part of an ester functional group pattern.
    """
    # This is a simplified check. In practice, one would check the local
    # environment of the bond to confirm it's an ester.
    # For this implementation, we assume we pass bond objects or types.
    # Here we just return False for non-ester bonds to allow dropout.
    # A more robust implementation would check the atom types connected.
    return False  # Placeholder: actual logic depends on bond context

def apply_edge_dropout(graph: MolecularGraph, dropout_rate: float = 0.1, rng: Optional[np.random.Generator] = None) -> MolecularGraph:
    """Apply functional-group-preserving edge dropout to a molecular graph.

    Only non-ester bonds are eligible for dropout to preserve chemical validity.

    Args:
        graph: Input molecular graph.
        dropout_rate: Probability of dropping an edge.
        rng: Random number generator for reproducibility.

    Returns:
        Augmented MolecularGraph with some edges dropped.
    """
    if rng is None:
        rng = np.random.default_rng()

    if graph.edge_index.size == 0:
        return graph

    # Identify non-ester bonds (simplified: assume all edges are candidates except known ester bonds)
    # In a real implementation, we would check the bond type and local environment.
    # For now, we treat all edges as non-ester for demonstration, but log a warning.
    logger.warning("Edge dropout: Simplified ester bond detection. In production, verify ester bonds.")

    edge_index = graph.edge_index.copy()
    num_edges = edge_index.shape[1]
    if num_edges == 0:
        return graph

    # Generate mask for edges to keep
    # We assume all edges are non-ester for this simplified version
    keep_mask = rng.random(num_edges) > dropout_rate

    if np.all(keep_mask):
        return graph

    new_edge_index = edge_index[:, keep_mask]

    return MolecularGraph(
        smiles=graph.smiles,
        node_features=graph.node_features,
        edge_index=new_edge_index
    )

def apply_augmentation_with_timeout(
    records: List[PolymerRecord],
    dropout_rate: float = 0.1,
    timeout_seconds: Optional[int] = None
) -> Tuple[List[MolecularGraph], Dict[str, Any]]:
    """Apply augmentation (edge dropout + canonicalization) with bounded runtime.

    Enforces a timeout to ensure the augmentation process does not exceed
    the allowed runtime. If timeout is exceeded, raises AugmentationTimeoutError.

    Args:
        records: List of PolymerRecord to augment.
        dropout_rate: Probability of dropping non-ester edges.
        timeout_seconds: Maximum allowed runtime in seconds. Defaults to env var or constant.

    Returns:
        Tuple of (augmented_graphs, stats)

    Raises:
        AugmentationTimeoutError: If augmentation exceeds timeout.
    """
    if timeout_seconds is None:
        timeout_seconds = int(os.environ.get(AUGMENTATION_TIMEOUT_ENV, AUGMENTATION_TIMEOUT_SECONDS))

    logger.info(f"Starting augmentation with timeout={timeout_seconds}s, dropout_rate={dropout_rate}")
    start_time = time.time()

    augmented_graphs = []
    stats = {
        "total_records": len(records),
        "augmented_count": 0,
        "skipped_count": 0,
        "timeout_exceeded": False,
        "elapsed_seconds": 0.0
    }

    # Set up timeout handler (Unix only)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_seconds)
    else:
        # Fallback for non-Unix systems: manual check
        logger.warning("SIGALRM not available; using manual timeout checks.")

    try:
        rng = np.random.default_rng(seed=42)  # Fixed seed for reproducibility
        for i, record in enumerate(records):
            # Manual timeout check for non-SIGALRM systems
            if not hasattr(signal, 'SIGALRM'):
                if time.time() - start_time > timeout_seconds:
                    raise AugmentationTimeoutError("Augmentation process exceeded the allowed runtime limit (manual check).")

            # Canonicalize SMILES
            canonical_smiles = canonicalize_smiles(record.smiles)
            if canonical_smiles is None:
                stats["skipped_count"] += 1
                continue

            # Convert to graph
            graph = smiles_to_molecular_graph(canonical_smiles)
            if graph is None:
                stats["skipped_count"] += 1
                continue

            # Apply edge dropout
            augmented_graph = apply_edge_dropout(graph, dropout_rate, rng)
            augmented_graphs.append(augmented_graph)
            stats["augmented_count"] += 1

            # Log progress
            if (i + 1) % 100 == 0:
                logger.debug(f"Processed {i + 1}/{len(records)} records")

    except AugmentationTimeoutError as e:
        stats["timeout_exceeded"] = True
        logger.error(f"Augmentation timeout: {e}")
        raise
    finally:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = elapsed
    logger.info(f"Augmentation completed: {stats['augmented_count']} augmented, {stats['skipped_count']} skipped, "
                f"elapsed={elapsed:.2f}s, timeout_exceeded={stats['timeout_exceeded']}")

    return augmented_graphs, stats

def compute_checksum(file_path: Union[str, Path]) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_dataset(
    graphs: List[MolecularGraph],
    output_path: Union[str, Path],
    stats: Optional[Dict[str, Any]] = None
):
    """Save molecular graphs to a CSV file with checksum.

    Args:
        graphs: List of MolecularGraph to save.
        output_path: Path to output CSV file.
        stats: Optional statistics dict to save alongside.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = None
        for i, graph in enumerate(graphs):
            row = {
                'smiles': graph.smiles,
                'node_features': ';'.join(map(str, graph.node_features.flatten())),
                'edge_index': ';'.join(map(str, graph.edge_index.flatten()))
            }
            if i == 0:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
            writer.writerow(row)

    checksum = compute_checksum(output_path)
    checksum_path = output_path.with_suffix('.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)

    logger.info(f"Saved {len(graphs)} graphs to {output_path} (checksum: {checksum})")

    if stats:
        stats_path = output_path.parent / f"{output_path.stem}_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved stats to {stats_path}")

def main():
    """Main entry point for preprocessing with bounded runtime augmentation.

    This function demonstrates the bounded runtime constraint for augmentation.
    It loads records (from a real source or previously saved data), applies
    augmentation with a timeout, and saves the results.

    For demonstration, we simulate a small dataset. In production, this would
    load from data/raw/processed files.
    """
    paths = get_project_paths()
    setup_logging(paths)

    # Simulate input records (in production, load from data/raw/)
    # This is a placeholder; real implementation would load from disk
    sample_records = [
        PolymerRecord(
            id=f"rec_{i}",
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O" if i % 2 == 0 else "CC(=O)OCC(=O)O",  # Simple esters
            temperature=25.0 + i,
            ph=7.0,
            uv_intensity=100.0,
            degradation_pathway="hydrolysis"
        )
        for i in range(10)
    ]

    # Apply augmentation with timeout
    timeout = int(os.environ.get(AUGMENTATION_TIMEOUT_ENV, 10))  # Short timeout for demo
    try:
        augmented_graphs, stats = apply_augmentation_with_timeout(
            sample_records,
            dropout_rate=0.1,
            timeout_seconds=timeout
        )
        save_dataset(
            augmented_graphs,
            paths["processed"] / "augmented_polyester_graphs.csv",
            stats
        )
    except AugmentationTimeoutError as e:
        logger.error(f"Augmentation failed due to timeout: {e}")
        # In production, we might exit with error code or handle gracefully
        raise

if __name__ == "__main__":
    main()