"""
Synthetic data generator for pipeline validation (Task T007).

Generates synthetic microglial morphology data conforming to the schema defined in T006a.
This data is used strictly for unit tests (T010) and logic validation (T010, T011).
It does NOT feed the main regression pipeline which requires real data (T012a).

Schema Compliance (T006a):
- brain_region: Enum ['Hippocampus', 'Prefrontal Cortex']
- pathology_status: Enum ['Normal', 'Early AD']
- morphological_metrics: branch_points, total_length, soma_area, sholl_intersections
- cognitive_score: mwm_latency
"""
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from code.config import get_path, ensure_dirs, set_seed, get_project_root
from code.logging_utils import get_logger

logger = get_logger(__name__)

# Constants for synthetic generation
BRAIN_REGIONS = ['Hippocampus', 'Prefrontal Cortex']
PATHOLOGY_STATUSES = ['Normal', 'Early AD']
METRICS_COLUMNS = ['branch_points', 'total_length', 'soma_area', 'sholl_intersections']
COGNITIVE_SCORE_COL = 'mwm_latency'

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_microglia_cell(
    brain_region: str,
    pathology_status: str,
    seed_offset: int = 0
) -> Dict[str, Any]:
    """
    Generate a single synthetic microglial cell record.

    Logic:
    - 'Early AD' in 'Hippocampus' typically shows simplified morphology (fewer branches, shorter length).
    - 'Normal' shows more complex morphology.
    - 'Prefrontal Cortex' has slightly different baseline values than 'Hippocampus'.
    - Cognitive score (mwm_latency) correlates inversely with complexity in AD.

    Args:
        brain_region: 'Hippocampus' or 'Prefrontal Cortex'
        pathology_status: 'Normal' or 'Early AD'
        seed_offset: Offset for random variation to ensure unique rows

    Returns:
        Dictionary with morphology metrics and metadata.
    """
    # Base parameters
    base_branches = 8 if brain_region == 'Hippocampus' else 10
    base_length = 150.0 if brain_region == 'Hippocampus' else 180.0
    base_soma = 40.0
    base_sholl = 12 if brain_region == 'Hippocampus' else 15
    base_latency = 20.0  # seconds

    # Pathology modifier
    if pathology_status == 'Early AD':
        # Simplification: fewer branches, shorter processes
        branch_modifier = -0.4
        length_modifier = -0.3
        soma_modifier = 0.1  # slight swelling
        sholl_modifier = -0.3
        latency_modifier = 0.6  # worse performance (higher latency)
    else:
        branch_modifier = 0.0
        length_modifier = 0.0
        soma_modifier = 0.0
        sholl_modifier = 0.0
        latency_modifier = 0.0

    # Region modifier (Prefrontal Cortex generally larger/more complex)
    region_branch_modifier = 0.0 if brain_region == 'Hippocampus' else 0.2
    region_length_modifier = 0.0 if brain_region == 'Hippocampus' else 0.15

    # Apply modifiers with noise
    noise_scale = 0.15
    branch_points = max(1, int((base_branches * (1 + branch_modifier + region_branch_modifier)) * (1 + np.random.normal(0, noise_scale) + seed_offset * 0.001)))
    total_length = max(10.0, base_length * (1 + length_modifier + region_length_modifier) * (1 + np.random.normal(0, noise_scale) + seed_offset * 0.001))
    soma_area = max(10.0, base_soma * (1 + soma_modifier) * (1 + np.random.normal(0, noise_scale) + seed_offset * 0.001))
    sholl_intersections = max(1, int((base_sholl * (1 + sholl_modifier)) * (1 + np.random.normal(0, noise_scale) + seed_offset * 0.001)))

    # Cognitive score: Higher latency = worse performance
    # Normal: ~20s, AD: ~35s
    cognitive_score = base_latency * (1 + latency_modifier) * (1 + np.random.normal(0, 0.1))
    cognitive_score = max(5.0, cognitive_score)

    return {
        'brain_region': brain_region,
        'pathology_status': pathology_status,
        'branch_points': branch_points,
        'total_length': round(total_length, 2),
        'soma_area': round(soma_area, 2),
        'sholl_intersections': sholl_intersections,
        'mwm_latency': round(cognitive_score, 2),
        'cell_id': f"cell_{brain_region}_{pathology_status}_{seed_offset}"
    }

def generate_ground_truth_metrics(
    n_cells: int = 100,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate a balanced synthetic dataset for validation.

    Args:
        n_cells: Total number of cells to generate
        seed: Random seed

    Returns:
        List of dictionaries representing cell records.
    """
    set_seed(seed)
    data = []
    n_per_group = n_cells // 4

    # Generate balanced groups
    groups = [
        ('Hippocampus', 'Normal'),
        ('Hippocampus', 'Early AD'),
        ('Prefrontal Cortex', 'Normal'),
        ('Prefrontal Cortex', 'Early AD')
    ]

    for group_idx, (region, status) in enumerate(groups):
        for i in range(n_per_group):
            cell = generate_microglia_cell(region, status, seed_offset=group_idx * 1000 + i)
            data.append(cell)

    # Add a few extra random samples to reach n_cells if not divisible
    remaining = n_cells - len(data)
    for i in range(remaining):
        region = random.choice(BRAIN_REGIONS)
        status = random.choice(PATHOLOGY_STATUSES)
        cell = generate_microglia_cell(region, status, seed_offset=10000 + i)
        data.append(cell)

    return data

def generate_synthetic_dataset(
    output_path: Optional[str] = None,
    n_cells: int = 100,
    seed: int = 42
) -> str:
    """
    Generate synthetic dataset and save to CSV.

    Args:
        output_path: Path to save CSV. If None, uses default path from config.
        n_cells: Number of cells to generate
        seed: Random seed

    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        output_path = get_path('data/processed/synthetic_morphological_metrics.csv')

    output_path = Path(output_path)
    ensure_dirs(output_path)

    data = generate_ground_truth_metrics(n_cells=n_cells, seed=seed)

    import pandas as pd
    df = pd.DataFrame(data)

    # Ensure column order matches schema expectations
    expected_cols = ['cell_id', 'brain_region', 'pathology_status'] + METRICS_COLUMNS + [COGNITIVE_SCORE_COL]
    # Reorder if necessary, but ensure all exist
    final_cols = [c for c in expected_cols if c in df.columns]
    # Add any missing columns (shouldn't happen with current logic)
    for c in df.columns:
        if c not in final_cols:
            final_cols.append(c)

    df = df[final_cols]
    df.to_csv(output_path, index=False)
    logger.info(f"Generated synthetic dataset with {len(df)} rows at {output_path}")

    return str(output_path)

def run_synthetic_pipeline(
    n_cells: int = 100,
    seed: int = 42
) -> str:
    """
    Run the full synthetic data generation pipeline.

    This function is the entry point for T012b (synthetic ingestion path).

    Args:
        n_cells: Number of cells to generate
        seed: Random seed

    Returns:
        Path to the generated CSV file.
    """
    logger.info("Starting synthetic data generation pipeline...")
    output_path = generate_synthetic_dataset(n_cells=n_cells, seed=seed)
    logger.info("Synthetic data generation complete.")
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic microglial morphology data")
    parser.add_argument("--n-cells", type=int, default=100, help="Number of cells to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    path = run_synthetic_pipeline(n_cells=args.n_cells, seed=args.seed)
    print(f"Generated: {path}")
