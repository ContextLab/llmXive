import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_master_seed(master_seed_path: str) -> int:
    """Load or create the master seed."""
    path = Path(master_seed_path)
    if path.exists():
        with open(path, 'r') as f:
            return int(f.read().strip())
    else:
        default_seed = 42
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(str(default_seed))
        return default_seed

def load_params(params_path: str) -> List[Dict[str, Any]]:
    """Load parameter sweep CSV."""
    import csv
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Params file not found at {params_path}")
    
    params_list = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            params_list.append({
                'n': int(row['n']),
                'p': int(row['p']),
                'rho': float(row['rho']),
                'distribution_type': row['distribution_type'],
                'iteration': int(row['iteration']),
                'seed': int(row['seed'])
            })
    return params_list

def build_seed_map(params_list: List[Dict[str, Any]], master_seed: int) -> Dict[str, List[int]]:
    """
    Build a seed map from parameters.
    Maps (n, p, rho, distribution_type) to a list of seeds.
    """
    seed_map = {}
    current_seed = master_seed
    
    # Sort params to ensure deterministic assignment
    # Group by unique keys
    from collections import defaultdict
    groups = defaultdict(list)
    for p in params_list:
        key = (p['n'], p['p'], p['rho'], p['distribution_type'])
        groups[key].append(p)
    
    for key, items in groups.items():
        # Assign sequential seeds
        seeds = []
        for item in items:
            seeds.append(current_seed)
            current_seed += 1
        seed_map[str(key)] = seeds
    
    return seed_map

def write_seed_map(seed_map: Dict[str, List[int]], output_path: str):
    """Write seed map to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(seed_map, f, indent=2)

def main():
    base_dir = Path(__file__).parent.parent
    params_path = base_dir / 'data' / 'sweep' / 'params.csv'
    master_seed_path = base_dir / 'data' / 'sweep' / 'master_seed.txt'
    output_path = base_dir / 'data' / 'sweep' / 'seed_map.json'
    
    master_seed = load_master_seed(str(master_seed_path))
    params_list = load_params(str(params_path))
    
    logger.info(f"Building seed map from {len(params_list)} parameters.")
    seed_map = build_seed_map(params_list, master_seed)
    
    write_seed_map(seed_map, str(output_path))
    logger.info(f"Seed map written to {output_path}")

if __name__ == '__main__':
    main()
