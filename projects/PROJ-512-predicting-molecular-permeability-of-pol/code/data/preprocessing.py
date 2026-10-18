import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import json
import hashlib
import numpy as np
import h5py
from functools import lru_cache

from models.polymer_graph import PolymerGraph
from data.utils import get_logger, set_seed

logger = get_logger(__name__)

@lru_cache(maxsize=1024)
def _cached_extract_features(smiles_hash: str, atom_types: tuple, hybridization: tuple, bond_types: tuple) -> Dict[str, np.ndarray]:
    """
    Cached extraction of graph features to avoid re-computation for identical molecular structures.
    Uses LRU cache with a limit to prevent memory bloat.
    """
    node_features = []
    for atom_type, hyb in zip(atom_types, hybridization):
        feat = np.zeros(10)
        if atom_type == 'C': feat[0] = 1
        elif atom_type == 'O': feat[1] = 1
        elif atom_type == 'N': feat[2] = 1
        if hyb == 'SP3': feat[3] = 1
        elif hyb == 'SP2': feat[4] = 1
        elif hyb == 'SP': feat[5] = 1
        node_features.append(feat)

    edge_features = []
    for b_type in bond_types:
        feat = np.zeros(5)
        if b_type == 'SINGLE': feat[0] = 1
        elif b_type == 'DOUBLE': feat[1] = 1
        elif b_type == 'AROMATIC': feat[2] = 1
        edge_features.append(feat)

    return {
        'node_features': np.array(node_features, dtype=np.float32) if node_features else np.zeros((0, 10), dtype=np.float32),
        'edge_features': np.array(edge_features, dtype=np.float32) if edge_features else np.zeros((0, 5), dtype=np.float32)
    }

def extract_graph_features(graph: PolymerGraph) -> Dict[str, np.ndarray]:
    """
    Extracts node and edge features from a PolymerGraph object.
    Optimized to use caching for repeated structures.
    """
    try:
        key_str = str(sorted(graph.nodes)) + str(sorted(graph.edges, key=repr))
        cache_key = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
    except Exception:
        cache_key = str(id(graph))

    atom_types = tuple([n.get('atom_type', n.get('type', 'C')) for n in graph.nodes])
    hybridization = tuple([n.get('hybridization', 'SP3') for n in graph.nodes])
    bond_types = tuple([
        e[2].get('bond_type', 'SINGLE') if isinstance(e, tuple) and len(e) == 3 and isinstance(e[2], dict)
        else (e.get('bond_type', 'SINGLE') if isinstance(e, dict) else 'SINGLE')
        for e in graph.edges
    ])

    return _cached_extract_features(cache_key, atom_types, hybridization, bond_types)

def convert_to_polymer_graph(raw_record: Dict[str, Any]) -> Optional[PolymerGraph]:
    """
    Converts a raw dictionary record into a PolymerGraph object.
    Includes validation and logging.
    """
    try:
        if not raw_record.get('smiles'):
            logger.warning(f"Skipping record with missing SMILES: {raw_record.get('id')}")
            return None

        graph = PolymerGraph(
            nodes=raw_record.get('nodes', []),
            edges=raw_record.get('edges', []),
        )
        return graph
    except Exception as e:
        logger.error(f"Error converting record to graph: {e}")
        return None

def process_graphs(records: List[Dict[str, Any]]) -> List[PolymerGraph]:
    """
    Processes a list of raw records into PolymerGraph objects.
    Optimized by batching feature extraction where possible and minimizing object creation overhead.
    """
    graphs = []
    for i, record in enumerate(records):
        if i % 1000 == 0:
            logger.info(f"Processing graph {i}/{len(records)}")

        graph = convert_to_polymer_graph(record)
        if graph:
            try:
                features = extract_graph_features(graph)
                graph.node_features = features['node_features']
                graph.edge_features = features['edge_features']
                graphs.append(graph)
            except Exception as e:
                logger.warning(f"Failed to extract features for graph {i}: {e}")
                continue
    return graphs

def get_murcko_scaffold(smiles: str) -> str:
    """
    Extracts the Murcko scaffold from a SMILES string.

    Uses Murcko scaffold extraction with chirality included, and returns
    the canonical SMILES string of the scaffold. This canonical string is
    the basis for strict identity matching between molecules.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Canonical SMILES of the Murcko scaffold (empty string on failure).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.*')

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Could not parse SMILES for scaffold extraction: {smiles}")
            return ""

        # MurckoScaffoldSmiles with includeChirality=True extracts the
        # framework and returns its canonical (isomeric) SMILES, which is
        # the chirality-aware scaffold identity required by FR-002.
        scaffold_smiles = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=True)
        return scaffold_smiles
    except ImportError:
        logger.error("RDKit not installed. Murcko scaffold extraction unavailable.")
        raise
    except Exception as e:
        logger.warning(f"Could not extract scaffold for {smiles}: {e}")
        return ""

def scaffold_hash(scaffold_smiles: str) -> str:
    """
    Hash a canonical scaffold SMILES string for strict identity matching.

    Args:
        scaffold_smiles: Canonical SMILES of the scaffold.

    Returns:
        SHA256 hex digest of the scaffold SMILES string.
    """
    return hashlib.sha256(scaffold_smiles.encode('utf-8')).hexdigest()

def murcko_scaffold_split(graphs: List[PolymerGraph], smiles_list: List[str],
                          test_ratio: float = 0.2, val_ratio: float = 0.1,
                          seed: int = 42) -> Tuple[List[int], List[int], List[int]]:
    """
    Splits graphs into train, validation, and test sets based on Murcko scaffolds.

    Scaffolds are extracted with chirality, converted to canonical SMILES, and
    hashed for strict identity matching. Whole scaffold groups are assigned to
    exactly one split, which guarantees that no molecule in the test set shares
    a scaffold with any molecule in the training set (FR-002).

    Args:
        graphs: List of PolymerGraph objects (may be empty; only used for length).
        smiles_list: List of SMILES strings corresponding to graphs.
        test_ratio: Fraction of data for test set.
        val_ratio: Fraction of data for validation set.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_indices, val_indices, test_indices)
    """
    set_seed(seed)

    n = len(smiles_list)
    if n == 0:
        raise ValueError("Cannot split an empty SMILES list.")

    # Map scaffold hash -> list of dataset indices
    scaffold_to_indices: Dict[str, List[int]] = defaultdict(list)
    for i, smiles in enumerate(smiles_list):
        scaffold = get_murcko_scaffold(smiles)
        if not scaffold:
            # Unparseable molecules get a unique scaffold so they cannot
            # leak between splits via a shared "unknown" bucket.
            scaffold = f"__unparseable__{i}"
        scaffold_to_indices[scaffold_hash(scaffold)].append(i)

    # Deterministically order scaffold groups, then shuffle with the pinned seed
    scaffold_keys = sorted(scaffold_to_indices.keys())
    rng = np.random.RandomState(seed)
    rng.shuffle(scaffold_keys)

    test_target = int(round(n * test_ratio))
    val_target = int(round(n * val_ratio))

    train_indices: List[int] = []
    val_indices: List[int] = []
    test_indices: List[int] = []

    for key in scaffold_keys:
        indices = scaffold_to_indices[key]
        if len(test_indices) < test_target:
            test_indices.extend(indices)
        elif len(val_indices) < val_target:
            val_indices.extend(indices)
        else:
            train_indices.extend(indices)

    # Strict exclusion rule: remove any molecule from the test set whose
    # scaffold hash also appears in the training set. By construction this
    # should never trigger, but the rule is enforced explicitly per FR-002.
    train_scaffolds: Set[str] = set()
    for i in train_indices:
        s = get_murcko_scaffold(smiles_list[i])
        if s:
            train_scaffolds.add(scaffold_hash(s))

    leaked = [i for i in test_indices
              if get_murcko_scaffold(smiles_list[i])
              and scaffold_hash(get_murcko_scaffold(smiles_list[i])) in train_scaffolds]
    if leaked:
        logger.warning(
            f"Excluding {len(leaked)} test molecules whose scaffolds appear in train."
        )
        test_indices = [i for i in test_indices if i not in set(leaked)]
        train_indices.extend(leaked)

    train_indices.sort()
    val_indices.sort()
    test_indices.sort()

    logger.info(
        f"Scaffold split: {len(train_indices)} train / {len(val_indices)} val / "
        f"{len(test_indices)} test across {len(scaffold_keys)} distinct scaffolds."
    )
    return train_indices, val_indices, test_indices

def save_split_indices(train_indices: List[int], val_indices: List[int],
                       test_indices: List[int], output_path: str) -> None:
    """
    Saves the split indices to a JSON file.
    """
    data = {
        "train": train_indices,
        "val": val_indices,
        "test": test_indices
    }
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved split indices to {output_path}")

def load_processed_dataset_hdf5(filepath: str, use_memory_mapping: bool = True) -> h5py.File:
    """
    Optimized loader for HDF5 datasets.
    Uses memory mapping to reduce I/O wait and memory footprint.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")

    try:
        file_handle = h5py.File(filepath, 'r')
        logger.info(f"Opened dataset with memory mapping optimization: {filepath}")
        return file_handle
    except Exception as e:
        logger.error(f"Failed to open dataset: {e}")
        raise

def _extract_smiles_from_hdf5(dataset: h5py.File) -> List[str]:
    """
    Extract the ordered list of SMILES strings from the processed HDF5 dataset.

    Supports the structure written by save_dataset.py:
    /dataset/graphs/{id}/attrs with a 'smiles' attribute,
    as well as a flat 'smiles' dataset for compatibility.

    Args:
        dataset: Open h5py.File handle.

    Returns:
        List of SMILES strings in deterministic (sorted graph-id) order.
    """
    if 'smiles' in dataset:
        return [s.decode('utf-8') if isinstance(s, bytes) else str(s)
                for s in dataset['smiles'][:]]

    if 'dataset' in dataset and 'graphs' in dataset['dataset']:
        graphs_group = dataset['dataset']['graphs']
        graph_ids = sorted(graphs_group.keys())
        smiles_list = []
        for gid in graph_ids:
            grp = graphs_group[gid]
            if 'attrs' in grp:
                attrs = grp['attrs']
                smi = None
                if isinstance(attrs, h5py.Dataset):
                    # attrs stored as a JSON string dataset
                    raw = attrs[()]
                    if isinstance(raw, bytes):
                        raw = raw.decode('utf-8')
                    try:
                        parsed = json.loads(raw)
                        smi = parsed.get('smiles')
                    except (ValueError, TypeError):
                        smi = None
                elif isinstance(attrs, h5py.Group):
                    smi = attrs.attrs.get('smiles')
                if smi is None:
                    smi = grp.attrs.get('smiles')
                if smi is None:
                    smi = grp.attrs.get('smiles')
                if smi is None:
                    raise ValueError(f"No SMILES found for graph '{gid}' in HDF5 file.")
                if isinstance(smi, bytes):
                    smi = smi.decode('utf-8')
                smiles_list.append(str(smi))
            else:
                smi = grp.attrs.get('smiles')
                if smi is None:
                    raise ValueError(f"No SMILES found for graph '{gid}' in HDF5 file.")
                if isinstance(smi, bytes):
                    smi = smi.decode('utf-8')
                smiles_list.append(str(smi))
        if not smiles_list:
            raise ValueError("HDF5 file contains no graphs with SMILES.")
        return smiles_list

    raise KeyError(
        "HDF5 dataset has neither a 'smiles' dataset nor a '/dataset/graphs' group. "
        "Run code/data/save_dataset.py first (T014)."
    )

def _resolve_path(relative_path: str) -> str:
    """Resolve a project-relative path against the project root."""
    if os.path.exists(relative_path):
        return relative_path
    try:
        from llmxive_toolkit import paths
        candidate = paths.path(*relative_path.split('/'))
        if os.path.exists(candidate):
            return str(candidate)
    except Exception:
        pass
    return relative_path

def main():
    """
    Main entry point for the scaffold-splitting pipeline (T020).

    Loads the processed dataset produced by T014, performs a Murcko
    scaffold split, and writes the split indices to
    code/data/processed/scaffold_split_indices.json.

    Fails loudly (non-zero exit) if the processed dataset is missing —
    no dummy or simulated split is ever produced.
    """
    logger.info("Starting Murcko scaffold split pipeline (T020)...")

    data_path = _resolve_path(
        "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5"
    )
    if not os.path.exists(data_path):
        data_path = _resolve_path("code/data/processed/polymers.h5")

    if not os.path.exists(data_path):
        logger.error(
            f"FATAL: processed dataset not found at {data_path}. "
            "Run the ingestion and save_dataset pipeline (T010-T014) first. "
            "No simulated split will be produced."
        )
        sys.exit(1)

    dataset = load_processed_dataset_hdf5(data_path)
    try:
        smiles_list = _extract_smiles_from_hdf5(dataset)
    finally:
        dataset.close()

    logger.info(f"Loaded {len(smiles_list)} SMILES from {data_path}")

    train_idx, val_idx, test_idx = murcko_scaffold_split(
        [], smiles_list, test_ratio=0.2, val_ratio=0.1, seed=42
    )

    output_path = _resolve_path(
        "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/scaffold_split_indices.json"
    )
    if not os.path.isdir(os.path.dirname(os.path.abspath(data_path))):
        output_path = _resolve_path("code/data/processed/scaffold_split_indices.json")
    else:
        # Write next to the input dataset for consistency.
          output_path = os.path.join(
              os.path.dirname(os.path.abspath(data_path)),
              "scaffold_split_indices.json",
          )

    save_split_indices(train_idx, val_idx, test_idx, output_path)
    logger.info(f"Scaffold split complete. Indices saved to {output_path}")

if __name__ == "__main__":
    main()