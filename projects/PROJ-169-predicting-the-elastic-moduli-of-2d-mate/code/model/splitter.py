import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict

@dataclass
class SplitManifest:
    train_ids: List[str]
    val_ids: List[str]
    test_ids: List[str]
    family_splits: Dict[str, str]

def split_by_family(
    graphs: List[Dict[str, Any]],
    test_ratio: float = 0.2,
    val_ratio: float = 0.1,
    seed: int = 42
) -> SplitManifest:
    """Split graphs by chemical family to ensure family separation."""
    import random
    random.seed(seed)
    
    # Group by family
    families: Dict[str, List[str]] = {}
    for g in graphs:
        fam = g.get('family', 'unknown')
        if fam not in families:
            families[fam] = []
        families[fam].append(g['material_id'])
    
    train_ids, val_ids, test_ids = [], [], []
    family_splits = {}
    
    # Sort families by size to ensure balanced splits
    sorted_families = sorted(families.items(), key=lambda x: len(x[1]), reverse=True)
    
    for fam, ids in sorted_families:
        random.shuffle(ids)
        n_test = max(1, int(len(ids) * test_ratio))
        n_val = max(1, int(len(ids) * val_ratio))
        
        test_ids.extend(ids[:n_test])
        val_ids.extend(ids[n_test:n_test+n_val])
        train_ids.extend(ids[n_test+n_val:])
        
        for mid in ids:
            if mid in test_ids:
                family_splits[mid] = 'test'
            elif mid in val_ids:
                family_splits[mid] = 'val'
            else:
                family_splits[mid] = 'train'
    
    return SplitManifest(train_ids, val_ids, test_ids, family_splits)

def save_split_manifest(manifest: SplitManifest, path: Path):
    """Save split manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(manifest), f, indent=2)

def main():
    pass
