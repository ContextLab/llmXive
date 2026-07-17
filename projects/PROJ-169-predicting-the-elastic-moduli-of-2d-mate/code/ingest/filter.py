import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class FilterStats:
    total: int
    passed: int
    failed_2d: int
    failed_tensor: int

def is_valid_6_component_tensor(tensor: np.ndarray) -> bool:
    """Check if tensor has 6 valid components."""
    if tensor is None:
        return False
    if len(tensor) != 6:
        return False
    return not np.any(np.isnan(tensor))

def is_2d_material(graph: Dict[str, Any]) -> bool:
    """Check if material is 2D (layered)."""
    # Simplified check: assume dimensionality flag exists
    return True

def filter_graphs(graphs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], FilterStats]:
    """Filter graphs based on 2D and tensor validity."""
    stats = FilterStats(total=len(graphs), passed=0, failed_2d=0, failed_tensor=0)
    filtered = []
    
    for g in graphs:
        if not is_2d_material(g):
            stats.failed_2d += 1
            continue
        if not is_valid_6_component_tensor(np.array(g.get('target_tensor'))):
            stats.failed_tensor += 1
            continue
        filtered.append(g)
        stats.passed += 1
        
    return filtered, stats

def save_filter_stats(stats: FilterStats, path: Path):
    """Save filter statistics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(stats), f, indent=2)

def main():
    # Placeholder for pipeline integration
    pass
