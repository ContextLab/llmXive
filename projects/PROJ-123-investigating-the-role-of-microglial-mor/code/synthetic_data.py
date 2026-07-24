import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from code.config import get_path, ensure_dirs, set_seed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_microglia_cell() -> Dict[str, Any]:
    """Generate synthetic microglia cell morphology data."""
    # Generate realistic morphological metrics
    branch_points = np.random.randint(5, 25)
    total_length = np.random.uniform(50, 200)
    soma_area = np.random.uniform(10, 50)
    
    # Generate Sholl intersections (simulated for different radii)
    sholl_radii = [5, 10, 15, 20, 25, 30]
    sholl_intersections = [np.random.randint(1, 10) for _ in sholl_radii]
    
    return {
        'branch_points': branch_points,
        'total_length': total_length,
        'soma_area': soma_area,
        'sholl_intersections': sholl_intersections
    }

def generate_ground_truth_metrics(n_cells: int = 100) -> List[Dict[str, Any]]:
    """Generate ground truth morphological metrics for n_cells."""
    cells = []
    for _ in range(n_cells):
        cell = generate_microglia_cell()
        cells.append(cell)
    return cells

def generate_synthetic_dataset(n_cells: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """Generate a complete synthetic dataset with all required fields."""
    set_seed(seed)
    
    cells = generate_ground_truth_metrics(n_cells)
    
    # Add metadata
    brain_regions = ['Hippocampus', 'Prefrontal Cortex']
    pathology_statuses = ['Normal', 'Early AD']
    
    dataset = []
    for i, cell in enumerate(cells):
        cell['subject_id'] = f'SUBJ_{i:03d}'
        cell['brain_region'] = random.choice(brain_regions)
        cell['pathology_status'] = random.choice(pathology_statuses)
        
        # Add cognitive score (realistic range)
        if cell['pathology_status'] == 'Early AD':
            cell['cognitive_score'] = np.random.uniform(10, 25)
        else:
            cell['cognitive_score'] = np.random.uniform(25, 40)
        
        # Add pathology markers
        cell['amyloid_beta_load'] = np.random.uniform(0, 1) if cell['pathology_status'] == 'Early AD' else np.random.uniform(0, 0.3)
        cell['tau_markers'] = np.random.uniform(0, 1) if cell['pathology_status'] == 'Early AD' else np.random.uniform(0, 0.3)
        
        dataset.append(cell)
    
    return dataset

def run_synthetic_pipeline(output_path: Optional[str] = None) -> str:
    """
    Run the synthetic data generation pipeline.
    
    Args:
        output_path: Optional path to save the synthetic dataset.
                    If None, saves to default location.
    
    Returns:
        Path to the generated synthetic dataset.
    """
    logger.info("Generating synthetic dataset...")
    
    # Generate dataset
    dataset = generate_synthetic_dataset(n_cells=100, seed=42)
    
    # Determine output path
    if output_path is None:
        output_path = get_path('processed', 'synthetic_dataset.csv')
    
    # Ensure directory exists
    ensure_dirs(output_path)
    
    # Save to CSV
    import pandas as pd
    df = pd.DataFrame(dataset)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Synthetic dataset generated at {output_path}")
    return output_path

def main():
    """Main entry point for synthetic data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic microglia data')
    parser.add_argument('--output', type=str, help='Output path for synthetic dataset')
    parser.add_argument('--n-cells', type=int, default=100, help='Number of cells to generate')
    
    args = parser.parse_args()
    
    run_synthetic_pipeline(output_path=args.output)

if __name__ == '__main__':
    main()
