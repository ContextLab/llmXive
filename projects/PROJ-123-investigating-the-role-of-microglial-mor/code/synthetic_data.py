"""
Synthetic Data Generator for Pipeline Validation (Task T007).

This module generates synthetic microglial morphology data conforming to the
dataset schema defined in T006a. It is used for logic validation (T010) ONLY.
It does NOT feed the main regression pipeline unless explicitly configured for
testing via a separate CLI flag.

IMPORTANT: This data is synthetic and intended for unit testing and pipeline
validation. It is NOT a substitute for real experimental data.
"""
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from code.config import get_path, ensure_dirs, get_default_config, set_seed
from code.logging_utils import get_logger

logger = get_logger(__name__)


def set_seed(seed: int = 42) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def generate_microglia_cell(
    brain_region: str = "Hippocampus",
    pathology_status: str = "Normal",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generates a single synthetic microglial cell record.
    
    Args:
        brain_region: The brain region (Hippocampus or Prefrontal Cortex).
        pathology_status: The pathology status (Normal or Early AD).
        seed: Optional seed for this specific generation.
    
    Returns:
        A dictionary representing a single cell record.
    """
    if seed is not None:
        set_seed(seed)
    
    # Base values for "Normal" state
    base_branch_points = 15.0
    base_total_length = 200.0
    base_soma_area = 50.0
    
    # Adjust based on pathology
    if pathology_status == "Early AD":
        # Simulate dystrophic morphology: fewer branches, shorter length, larger soma
        branch_factor = 0.7
        length_factor = 0.8
        soma_factor = 1.5
    else:
        branch_factor = 1.0
        length_factor = 1.0
        soma_factor = 1.0
    
    # Add noise
    branch_points = max(1, int(base_branch_points * branch_factor * np.random.uniform(0.8, 1.2)))
    total_length = max(10, base_total_length * length_factor * np.random.uniform(0.8, 1.2))
    soma_area = max(10, base_soma_area * soma_factor * np.random.uniform(0.8, 1.2))
    
    # Generate Sholl intersections (simplified vector)
    # Simulate a decay curve: intersections decrease as radius increases
    radii = [5, 10, 15, 20, 25]
    sholl_counts = []
    base_intersections = 20
    for r in radii:
        # Exponential decay model
        count = int(base_intersections * np.exp(-0.1 * r) * np.random.uniform(0.9, 1.1))
        sholl_counts.append(max(0, count))
    
    # Cognitive score (synthetic correlation)
    # Lower cognitive score for Early AD
    if pathology_status == "Early AD":
        cognitive_score = np.random.normal(0.3, 0.1)
    else:
        cognitive_score = np.random.normal(0.8, 0.1)
    cognitive_score = max(0.0, min(1.0, cognitive_score))
    
    # Amyloid and Tau (synthetic)
    if pathology_status == "Early AD":
        amyloid_beta_load = np.random.uniform(0.6, 1.0)
        tau_markers = np.random.uniform(0.6, 1.0)
    else:
        amyloid_beta_load = np.random.uniform(0.0, 0.3)
        tau_markers = np.random.uniform(0.0, 0.3)
    
    return {
        "brain_region": brain_region,
        "pathology_status": pathology_status,
        "branch_points": branch_points,
        "total_length": total_length,
        "soma_area": soma_area,
        "sholl_intersections": sholl_counts, # Store as list for now, will be JSON'd later
        "cognitive_score": round(cognitive_score, 3),
        "amyloid_beta_load": round(amyloid_beta_load, 3),
        "tau_markers": round(tau_markers, 3)
    }


def generate_ground_truth_metrics(n_samples: int = 100) -> List[Dict[str, Any]]:
    """
    Generates a balanced synthetic dataset for validation.
    
    Args:
        n_samples: Total number of samples to generate.
    
    Returns:
        A list of dictionaries representing the dataset.
    """
    set_seed(42)
    data = []
    
    # Ensure balanced classes
    n_per_class = n_samples // 4
    regions = ["Hippocampus", "Prefrontal Cortex"]
    statuses = ["Normal", "Early AD"]
    
    for region in regions:
        for status in statuses:
            for i in range(n_per_class):
                cell = generate_microglia_cell(region, status)
                data.append(cell)
    
    # Add a few extra random samples to reach n_samples if needed
    while len(data) < n_samples:
        region = random.choice(regions)
        status = random.choice(statuses)
        cell = generate_microglia_cell(region, status)
        data.append(cell)
    
    return data


def generate_synthetic_dataset(output_path: Optional[str] = None) -> str:
    """
    Generates a synthetic dataset and saves it to CSV.
    
    Args:
        output_path: Optional path to save the CSV. If None, uses default config.
    
    Returns:
        The path to the generated CSV file.
    """
    logger.info("Generating synthetic dataset for pipeline validation (T007)...")
    
    if output_path is None:
        output_path = get_path("data_processed", "synthetic_dataset.csv")
    
    data = generate_ground_truth_metrics(n_samples=200)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    ensure_dirs(os.path.dirname(output_path))
    df.to_csv(output_path, index=False)
    
    logger.info(f"Synthetic dataset saved to {output_path}")
    return output_path


def run_synthetic_pipeline() -> str:
    """
    Runs the full synthetic data generation pipeline.
    
    Returns:
        The path to the generated dataset.
    """
    return generate_synthetic_dataset()


# Import pandas here to avoid circular imports if config depends on it elsewhere
import pandas as pd


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    path = run_synthetic_pipeline()
    print(f"Generated: {path}")
