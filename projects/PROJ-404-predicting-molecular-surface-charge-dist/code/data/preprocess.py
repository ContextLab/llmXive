from typing import List, Tuple, Optional, Dict, Iterator
import numpy as np
import torch
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from data.dataset import MoleculeData

def normalize_coordinates(pos: torch.Tensor) -> torch.Tensor:
    """Center coordinates at origin (mean = 0)."""
    return pos - pos.mean(dim=0, keepdim=True)

def normalize_batch(batch: List[MoleculeData]) -> List[MoleculeData]:
    """Normalize coordinates for all molecules in a batch."""
    return [MoleculeData(
        x=data.x,
        pos=normalize_coordinates(data.pos),
        y=data.y,
        scaffold_id=data.scaffold_id,
        idx=data.idx
    ) for data in batch]

def extract_scaffold(mol: Chem.Mol) -> str:
    """Extract Bemis-Murcko scaffold string from molecule."""
    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return ""

def group_molecules_by_scaffold(
    molecules: List[Dict[str, Any]]
) -> Dict[str, List[int]]:
    """Group molecule indices by their scaffold ID."""
    groups = {}
    for idx, mol in enumerate(molecules):
        scaffold = mol.get('scaffold_id', 'unknown')
        if scaffold not in groups:
            groups[scaffold] = []
        groups[scaffold].append(idx)
    return groups

def generate_scaffold_split_indices(
    scaffold_groups: Dict[str, List[int]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 42
) -> Dict[str, List[int]]:
    """
    Generate scaffold-aware split indices.
    Ensures all molecules from same scaffold are in same split.
    """
    random.seed(seed)
    scaffolds = list(scaffold_groups.keys())
    random.shuffle(scaffolds)
    
    train_indices = []
    val_indices = []
    test_indices = []
    
    total_molecules = sum(len(indices) for indices in scaffold_groups.values())
    train_target = int(total_molecules * train_ratio)
    val_target = int(total_molecules * val_ratio)
    
    train_count = 0
    val_count = 0
    
    for scaffold in scaffolds:
        indices = scaffold_groups[scaffold]
        if train_count < train_target:
            train_indices.extend(indices)
            train_count += len(indices)
        elif val_count < val_target:
            val_indices.extend(indices)
            val_count += len(indices)
        else:
            test_indices.extend(indices)
    
    return {
        'train': train_indices,
        'val': val_indices,
        'test': test_indices
    }

def apply_scaffold_split(
    dataset: Iterator,
    split_name: str,
    indices_path: str
) -> Iterator:
    """Apply scaffold split to dataset stream."""
    import json
    
    with open(indices_path, 'r') as f:
        splits = json.load(f)
    
    if split_name not in splits:
        raise ValueError(f"Unknown split: {split_name}")
    
    valid_indices = set(splits[split_name])
    
    for item in dataset:
        if item.get('idx', -1) in valid_indices:
            yield item