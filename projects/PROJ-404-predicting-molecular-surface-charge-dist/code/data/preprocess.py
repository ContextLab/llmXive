from typing import List, Tuple, Optional, Dict, Iterator
import numpy as np
import torch
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from data.dataset import MoleculeData
from utils import set_seed, get_logger

logger = get_logger(__name__)

def normalize_coordinates(pos: torch.Tensor) -> torch.Tensor:
    """Shift coordinates such that the center of mass (mean) is at the origin."""
    if pos.dim() == 1:
        pos = pos.unsqueeze(0)
    mean_pos = pos.mean(dim=0, keepdim=True)
    return pos - mean_pos

def normalize_batch(batch: List[MoleculeData]) -> List[MoleculeData]:
    """Apply coordinate normalization to a list of MoleculeData objects."""
    normalized_batch = []
    for data in batch:
        if hasattr(data, 'pos') and data.pos is not None:
            data.pos = normalize_coordinates(data.pos)
        normalized_batch.append(data)
    return normalized_batch

def extract_scaffold(mol: Chem.Mol) -> Optional[str]:
    """Extract the Bemis-Murcko scaffold string for a molecule."""
    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to extract scaffold: {e}")
        return None

def group_molecules_by_scaffold(
    data_stream: Iterator[MoleculeData],
    mol_from_data_fn
) -> Dict[str, List[int]]:
    """
    Group molecules by their scaffold string.
    
    Args:
        data_stream: Iterator of MoleculeData objects.
        mol_from_data_fn: A function that converts MoleculeData to an RDKit Mol.
    
    Returns:
        Dictionary mapping scaffold string to list of indices.
    """
    scaffold_groups: Dict[str, List[int]] = {}
    for idx, data in enumerate(data_stream):
        # Reconstruct RDKit Mol from MoleculeData
        mol = mol_from_data_fn(data)
        if mol is None:
            logger.warning(f"Molecule at index {idx} could not be reconstructed.")
            continue
        
        scaffold = extract_scaffold(mol)
        if scaffold is None:
            logger.warning(f"Molecule at index {idx} has no valid scaffold.")
            continue
        
        if scaffold not in scaffold_groups:
            scaffold_groups[scaffold] = []
        scaffold_groups[scaffold].append(idx)
    
    logger.info(f"Grouped {sum(len(v) for v in scaffold_groups.values())} molecules into {len(scaffold_groups)} scaffolds.")
    return scaffold_groups

def generate_scaffold_split_indices(
    data_stream: Iterator[MoleculeData],
    mol_from_data_fn,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[int], List[int], List[int]]:
    """
    Generate train, validation, and test index streams stratified by Bemis-Murcko scaffold.
    
    This function consumes the data stream once to group molecules by scaffold,
    then performs a stratified split by assigning entire scaffolds to sets.
    
    Args:
        data_stream: Iterator of MoleculeData objects.
        mol_from_data_fn: A function that converts MoleculeData to an RDKit Mol.
        train_ratio: Fraction of data for training.
        val_ratio: Fraction of data for validation.
        test_ratio: Fraction of data for testing.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (train_indices, val_indices, test_indices).
    
    Raises:
        ValueError: If ratios do not sum to 1.0.
    """
    if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
        raise ValueError("Ratios must sum to 1.0")
    
    set_seed(seed)
    
    # Group molecules by scaffold
    scaffold_groups = group_molecules_by_scaffold(data_stream, mol_from_data_fn)
    
    # Sort scaffolds by size (descending) for deterministic processing
    sorted_scaffolds = sorted(
        scaffold_groups.keys(), 
        key=lambda k: len(scaffold_groups[k]), 
        reverse=True
    )
    
    # Shuffle scaffolds
    rng = np.random.default_rng(seed)
    rng.shuffle(sorted_scaffolds)
    
    train_indices = []
    val_indices = []
    test_indices = []
    
    current_train_count = 0
    current_val_count = 0
    current_test_count = 0
    
    total_molecules = sum(len(indices) for indices in scaffold_groups.values())
    
    for scaffold in sorted_scaffolds:
        indices = scaffold_groups[scaffold]
        count = len(indices)
        
        # Assign scaffold to the set with the largest deficit relative to target
        train_deficit = (train_ratio * total_molecules) - current_train_count
        val_deficit = (val_ratio * total_molecules) - current_val_count
        test_deficit = (test_ratio * total_molecules) - current_test_count
        
        if train_deficit >= val_deficit and train_deficit >= test_deficit:
            train_indices.extend(indices)
            current_train_count += count
        elif val_deficit >= test_deficit:
            val_indices.extend(indices)
            current_val_count += count
        else:
            test_indices.extend(indices)
            current_test_count += count
    
    logger.info(f"Split generated: Train={len(train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")
    return train_indices, val_indices, test_indices

def apply_scaffold_split(
    data_stream: Iterator[MoleculeData],
    train_indices: List[int],
    val_indices: List[int],
    test_indices: List[int]
) -> Tuple[Iterator[MoleculeData], Iterator[MoleculeData], Iterator[MoleculeData]]:
    """
    Execute the scaffold split by filtering the input data stream into train, val, and test iterators.
    
    This function consumes the provided data stream exactly once, filtering molecules based on the
    provided index lists. It returns three independent iterators (or generators) that yield the
    corresponding subsets of the original data.
    
    Args:
        data_stream: The original iterator of MoleculeData objects.
        train_indices: List of indices belonging to the training set.
        val_indices: List of indices belonging to the validation set.
        test_indices: List of indices belonging to the test set.
    
    Returns:
        A tuple of (train_iterator, val_iterator, test_iterator).
    
    Note:
        The input data_stream is consumed immediately. The returned iterators must be consumed
        to retrieve the data. If the data_stream is a one-time generator, it must be passed
        directly to this function before being exhausted elsewhere.
    """
    # Convert lists to sets for O(1) lookup
    train_set = set(train_indices)
    val_set = set(val_indices)
    test_set = set(test_indices)
    
    def make_filter_iterator(indices_set: set, original_stream: Iterator[MoleculeData]) -> Iterator[MoleculeData]:
        """Helper to create a filtered iterator."""
        for idx, data in enumerate(original_stream):
            if idx in indices_set:
                yield data
    
    # Since we cannot rewind a stream, we must filter in a single pass and yield
    # However, the requirement is to return THREE separate iterators.
    # A single pass cannot yield to three independent iterators simultaneously if the source is a one-time generator.
    # To satisfy the contract of returning three iterators from a single stream, we must buffer the data.
    # Given the constraint of "streaming" in T006, we assume the stream might be large.
    # BUT, T009a specifically asks to "consume split indices... and filter... returning filtered iterators".
    # If the stream is truly infinite or too large to buffer, we cannot return 3 independent iterators without buffering.
    # The standard approach for a "split" operation on a one-shot stream is to materialize the split into lists of objects
    # OR to return a single generator that yields (split_name, data).
    # However, the task asks for "filtered iterators" (plural).
    # To be safe and correct with Python generators, we will buffer the necessary data for the split.
    # Since we have the indices, we can collect all data first.
    
    logger.info("Materializing data stream for scaffold split filtering...")
    all_data = list(data_stream)
    logger.info(f"Materialized {len(all_data)} molecules.")
    
    train_iter = (all_data[i] for i in sorted(train_set) if i < len(all_data))
    val_iter = (all_data[i] for i in sorted(val_set) if i < len(all_data))
    test_iter = (all_data[i] for i in sorted(test_set) if i < len(all_data))
    
    logger.info(f"Created split iterators: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}")
    
    return train_iter, val_iter, test_iter