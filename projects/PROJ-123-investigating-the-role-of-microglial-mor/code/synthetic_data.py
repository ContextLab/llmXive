import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import logging

from code.config import get_path, ensure_dirs, set_seed

logger = logging.getLogger(__name__)

def generate_microglia_cell(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate a single synthetic microglia cell with realistic morphology.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Realistic ranges based on literature
    branch_points = random.randint(3, 15)
    total_length = random.uniform(50.0, 300.0) # micrometers
    soma_area = random.uniform(20.0, 100.0) # square micrometers
    sholl_intersections = [random.randint(0, 10) for _ in range(10)] # 10 radii

    return {
        "branch_points": branch_points,
        "total_length": total_length,
        "soma_area": soma_area,
        "sholl_intersections": sholl_intersections
    }

def generate_ground_truth_metrics(n_cells: int = 100, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate a dataset of synthetic microglia cells.
    """
    set_seed(seed)
    data = []
    for i in range(n_cells):
        cell = generate_microglia_cell(seed=seed+i)
        # Add metadata
        cell['brain_region'] = random.choice(['Hippocampus', 'Prefrontal Cortex'])
        cell['pathology_status'] = random.choice(['Normal', 'Early AD'])
        cell['cognitive_score'] = random.uniform(0.0, 100.0)
        cell['amyloid_beta_load'] = random.uniform(0.0, 1.0)
        cell['tau_markers'] = random.uniform(0.0, 1.0)
        data.append(cell)
    
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_cells: int = 100, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate a full synthetic dataset for validation.
    """
    return generate_ground_truth_metrics(n_cells, seed)

def run_synthetic_pipeline(output_path: Optional[str] = None, **kwargs) -> str:
    """
    Run the synthetic data generation pipeline.
    Accepts output_path as a keyword argument or positional.
    """
    logger.info("Running synthetic pipeline.")
    
    # Handle arguments flexibly
    out_path = output_path
    if out_path is None:
        out_path = kwargs.get('output_path')
    if out_path is None:
        out_path = kwargs.get('output')
    
    if out_path is None:
        out_path = get_path("data/processed/synthetic_dataset.csv")
    
    ensure_dirs(out_path)
    
    df = generate_synthetic_dataset(n_cells=100, seed=42)
    df.to_csv(out_path, index=False)
    logger.info(f"Synthetic data generated at {out_path}")
    return out_path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic data.")
    parser.add_argument('--output', type=str, help="Output path for synthetic data")
    parser.add_argument('--n', type=int, default=100, help="Number of cells")
    args = parser.parse_args()
    
    path = run_synthetic_pipeline(args.output)
    print(f"Generated: {path}")

if __name__ == "__main__":
    main()
