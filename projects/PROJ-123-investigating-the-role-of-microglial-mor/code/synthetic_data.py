"""
Synthetic Data Generator for Microglial Morphology Pipeline.

Generates synthetic microglial cell data conforming to the dataset schema
defined in T006a. This data is used for pipeline validation and logic testing
where real data is unavailable or for initial regression logic checks.

Constraints:
- Generates data for 'Hippocampus' and 'Prefrontal Cortex'.
- Generates data for 'Normal' and 'Early AD' pathology status.
- Metrics: branch_points, total_length, soma_area, sholl_intersections.
- Includes cognitive_score (mwm_latency).
- Does NOT include 'fractal_dimension' or 'complexity_index'.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.config import get_path, ensure_dirs, set_seed, get_project_root


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def generate_microglia_cell(
    brain_region: str,
    pathology_status: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a single synthetic microglia cell record.

    Args:
        brain_region: 'Hippocampus' or 'Prefrontal Cortex'.
        pathology_status: 'Normal' or 'Early AD'.
        seed: Optional seed for this specific cell (for reproducibility).

    Returns:
        Dictionary containing synthetic morphological metrics and metadata.
    """
    if seed is not None:
        local_rng = np.random.default_rng(seed)
    else:
        local_rng = np.random.default_rng()

    # Base parameters (approximate biological ranges in microns)
    # Hippocampus tends to have slightly different morphology than PFC
    region_bias = 1.0
    if brain_region == "Hippocampus":
        region_bias = 1.1
    elif brain_region == "Prefrontal Cortex":
        region_bias = 0.95

    # Pathology effect: AD typically shows dystrophy (reduced complexity)
    # Normal: higher branch points, longer processes
    # Early AD: lower branch points, shorter processes, sometimes larger soma
    pathology_factor = 1.0
    if pathology_status == "Normal":
        pathology_factor = 1.2
    elif pathology_status == "Early AD":
        pathology_factor = 0.7

    # Generate Morphological Metrics
    # Branch Points: Typically 10-40 for microglia
    base_branch_points = 25.0
    branch_points = int(np.clip(
        local_rng.normal(base_branch_points * region_bias * pathology_factor, 5.0),
        5, 60
    ))

    # Total Length (microns): Typically 100-500
    base_total_length = 300.0
    total_length = float(np.clip(
        local_rng.normal(base_total_length * region_bias * pathology_factor, 50.0),
        50, 800
    ))

    # Soma Area (microns^2): Typically 50-200
    # Dystrophic (AD) cells often have hypertrophied (larger) somas
    soma_factor = 1.0
    if pathology_status == "Early AD":
        soma_factor = 1.4 # Hypertrophy
    base_soma_area = 100.0
    soma_area = float(np.clip(
        local_rng.normal(base_soma_area * region_bias * soma_factor, 20.0),
        30, 400
    ))

    # Sholl Intersections: Count at a specific radius (e.g., 20um)
    # Correlates with branch points but distinct metric
    base_sholl = 15.0
    sholl_intersections = int(np.clip(
        local_rng.normal(base_sholl * region_bias * pathology_factor, 3.0),
        2, 40
    ))

    # Cognitive Score (mwm_latency in seconds):
    # Normal: Lower latency (better performance, e.g., 20-40s)
    # Early AD: Higher latency (worse performance, e.g., 60-120s)
    # Correlate with pathology_status
    if pathology_status == "Normal":
        cognitive_score = float(np.clip(
            local_rng.normal(30.0, 8.0),
            10, 60
        ))
    else:
        cognitive_score = float(np.clip(
            local_rng.normal(90.0, 20.0),
            40, 180
        ))

    return {
        "subject_id": f"SUBJ-{random.randint(1000, 9999)}-{random.randint(1, 100)}",
        "brain_region": brain_region,
        "pathology_status": pathology_status,
        "morphological_metrics": {
            "branch_points": branch_points,
            "total_length": round(total_length, 2),
            "soma_area": round(soma_area, 2),
            "sholl_intersections": sholl_intersections
        },
        "cognitive_score": round(cognitive_score, 2),
        "metadata": {
            "generated_by": "synthetic_data.py",
            "version": "1.0",
            "seed": seed
        }
    }


def generate_ground_truth_metrics(
    n_cells: int = 100,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate a list of synthetic microglia cells representing ground truth.

    Args:
        n_cells: Number of cells to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries, each representing a cell record.
    """
    if seed is not None:
        set_seed(seed)

    regions = ["Hippocampus", "Prefrontal Cortex"]
    statuses = ["Normal", "Early AD"]

    cells = []
    for i in range(n_cells):
        # Ensure balanced distribution for testing
        region = regions[i % 2]
        status = statuses[(i // 2) % 2]

        # Add some randomness to the assignment to avoid perfect alternation
        if random.random() > 0.5:
            region = random.choice(regions)
        if random.random() > 0.5:
            status = random.choice(statuses)

        cell = generate_microglia_cell(region, status, seed=i)
        cells.append(cell)

    return cells


def generate_synthetic_dataset(
    output_path: Optional[str] = None,
    n_cells: int = 200,
    seed: int = 42
) -> str:
    """
    Generate the full synthetic dataset and save it to disk.

    This function creates a CSV file conforming to the schema in T006a.
    It also saves the raw JSON ground truth for reference.

    Args:
        output_path: Optional path to save the CSV. Defaults to data/processed/synthetic_morphology.csv.
        n_cells: Number of cells to generate.
        seed: Random seed.

    Returns:
        Path to the generated CSV file.
    """
    set_seed(seed)

    # Generate data
    raw_data = generate_ground_truth_metrics(n_cells=n_cells, seed=seed)

    # Flatten for CSV
    rows = []
    for cell in raw_data:
        metrics = cell["morphological_metrics"]
        rows.append({
            "subject_id": cell["subject_id"],
            "brain_region": cell["brain_region"],
            "pathology_status": cell["pathology_status"],
            "branch_points": metrics["branch_points"],
            "total_length": metrics["total_length"],
            "soma_area": metrics["soma_area"],
            "sholl_intersections": metrics["sholl_intersections"],
            "cognitive_score": cell["cognitive_score"]
        })

    df = pd.DataFrame(rows)

    # Ensure output directory exists
    if output_path is None:
        output_path = get_path("data_processed", "synthetic_morphology.csv")

    output_dir = os.path.dirname(output_path)
    ensure_dirs(output_dir)

    # Save CSV
    df.to_csv(output_path, index=False)

    # Save JSON ground truth for debugging/validation
    json_path = output_path.replace(".csv", "_ground_truth.json")
    with open(json_path, "w") as f:
        json.dump(raw_data, f, indent=2)

    return output_path


def run_synthetic_pipeline() -> str:
    """
    Entry point to run the synthetic data generation pipeline.
    Used by T007 to produce the validation dataset.

    Returns:
        Path to the generated CSV.
    """
    print("Generating synthetic microglial morphology dataset...")
    output_path = generate_synthetic_dataset(n_cells=500, seed=42)
    print(f"Synthetic dataset generated at: {output_path}")
    return output_path


if __name__ == "__main__":
    run_synthetic_pipeline()
