from __future__ import annotations

import os
import logging
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import asdict, is_dataclass, fields
import json
import hashlib
from datetime import datetime

import pandas as pd
import numpy as np

from config import get_config
from models import SimulatedDataset, PowerMetric
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_run_id() -> str:
    """
    Generate a deterministic run ID based on current timestamp and a random UUID.
    Used to uniquely identify simulation runs.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"run_{timestamp}_{unique_id}"


def _enforce_constraints(
    datasets: List[SimulatedDataset],
    simulations_per_condition: int,
    expected_dataset_count: int
) -> Tuple[List[SimulatedDataset], Dict[str, Any]]:
    """
    Enforce the dataset count and simulation count constraints before writing.
    
    Args:
        datasets: List of SimulatedDataset objects.
        simulations_per_condition: Expected number of simulations per condition.
        expected_dataset_count: Expected number of datasets (e.g., 10).
        
    Returns:
        Tuple of (validated_datasets, metadata)
        
    Raises:
        ValueError: If constraints are not met.
    """
    # Check dataset count
    if len(datasets) != expected_dataset_count:
        raise ValueError(
            f"Dataset count constraint violated: expected {expected_dataset_count}, "
            f"got {len(datasets)}. Ensure fetch_datasets returns exactly {expected_dataset_count} valid datasets."
        )
    
    # Check simulation counts per condition
    # We group by (dataset_id, snr, sparsity) to verify counts
    simulation_counts: Dict[Tuple[str, float, float], int] = {}
    
    for ds in datasets:
        # SimulatedDataset contains the simulation results for specific conditions
        # Depending on how SimulatedDataset is structured in models.py, we might need to
        # check the internal simulation list or assume the object represents one simulation.
        # Based on T015 description ("process a batch"), SimulatedDataset likely represents
        # a single simulation instance with metadata.
        # However, T019 mentions "simulations per condition rule".
        # Let's assume datasets here is a flat list of all simulation results.
        
        key = (ds.dataset_id, ds.snr, ds.sparsity)
        simulation_counts[key] = simulation_counts.get(key, 0) + 1
    
    for key, count in simulation_counts.items():
        if count != simulations_per_condition:
            raise ValueError(
                f"Simulation count constraint violated for condition {key}: "
                f"expected {simulations_per_condition}, got {count}."
            )
    
    logger.info(
        f"Constraints validated: {len(datasets)} total simulations across "
        f"{len(set(d.dataset_id for d in datasets))} datasets, "
        f"{simulations_per_condition} per condition."
    )
    
    metadata = {
        "total_simulations": len(datasets),
        "dataset_count": len(set(d.dataset_id for d in datasets)),
        "simulations_per_condition": simulations_per_condition,
        "conditions_verified": list(simulation_counts.keys())
    }
    
    return datasets, metadata


def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Recursively convert a dataclass to a dictionary, handling numpy arrays.
    """
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            val = getattr(obj, f.name)
            result[f.name] = _dataclass_to_dict(val)
        return result
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (list, tuple)):
        return [_dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    else:
        return obj


def save_simulated_datasets(
    datasets: List[SimulatedDataset],
    output_path: Optional[str] = None,
    simulations_per_condition: int = 200,
    expected_dataset_count: int = 10
) -> str:
    """
    Save simulated datasets to `data/processed/simulated_datasets.csv`.
    
    Enforces constraints on dataset count and simulations per condition before writing.
    
    Args:
        datasets: List of SimulatedDataset objects.
        output_path: Optional override for output path. Defaults to data/processed/simulated_datasets.csv.
        simulations_per_condition: Expected number of simulations per (dataset, snr, sparsity) condition.
        expected_dataset_count: Expected number of unique datasets.
        
    Returns:
        Path to the saved file.
        
    Raises:
        ValueError: If constraints are not met.
    """
    config = get_config()
    if output_path is None:
        output_path = os.path.join(config.output_path, "simulated_datasets.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Enforce constraints
    validated_datasets, metadata = _enforce_constraints(
        datasets, simulations_per_condition, expected_dataset_count
    )
    
    # Convert to DataFrame
    data_rows = []
    for ds in validated_datasets:
        row = _dataclass_to_dict(ds)
        # Flatten nested structures if necessary for CSV compatibility
        # Ensure arrays are stored as JSON strings or flattened
        for k, v in row.items():
            if isinstance(v, (list, dict)):
                row[k] = json.dumps(v)
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(df)} simulated dataset records to {output_path}")
    
    # Save manifest
    manifest_path = os.path.join(os.path.dirname(output_path), "simulation_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({
            "run_id": generate_run_id(),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "file_path": output_path
        }, f, indent=2)
    
    return output_path


def save_power_metrics(
    metrics: List[PowerMetric],
    output_path: Optional[str] = None
) -> str:
    """
    Save power metrics to `data/processed/power_metrics.csv`.
    
    Args:
        metrics: List of PowerMetric objects.
        output_path: Optional override for output path. Defaults to data/processed/power_metrics.csv.
        
    Returns:
        Path to the saved file.
    """
    config = get_config()
    if output_path is None:
        output_path = os.path.join(config.output_path, "power_metrics.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to DataFrame
    data_rows = []
    for m in metrics:
        row = _dataclass_to_dict(m)
        for k, v in row.items():
            if isinstance(v, (list, dict)):
                row[k] = json.dumps(v)
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(df)} power metric records to {output_path}")
    
    return output_path


def save_simulation_manifest(
    run_id: str,
    metadata: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save a manifest file for the simulation run.
    
    Args:
        run_id: Unique identifier for the run.
        metadata: Dictionary containing run metadata.
        output_path: Optional override for output path.
        
    Returns:
        Path to the saved manifest file.
    """
    config = get_config()
    if output_path is None:
        output_path = os.path.join(config.output_path, "simulation_manifest.json")
    
    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved simulation manifest to {output_path}")
    
    return output_path


def main() -> None:
    """
    Main entry point for storage module.
    Demonstrates saving simulated datasets and power metrics.
    This function is intended to be called by the pipeline after simulation.
    """
    logger.info("Storage module main() called. Ready to save simulation results.")
    
    # Example usage (would be populated by the pipeline):
    # datasets = [...] # List of SimulatedDataset
    # metrics = [...]  # List of PowerMetric
    # save_simulated_datasets(datasets)
    # save_power_metrics(metrics)
    
    logger.info("Storage module ready.")


if __name__ == "__main__":
    main()