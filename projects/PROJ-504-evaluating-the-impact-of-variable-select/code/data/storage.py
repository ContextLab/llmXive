"""
Storage utilities for saving simulation results.
Implements deterministic saving of processed data to Parquet/CSV formats.
"""
from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict, is_dataclass
import json
import hashlib
import time

import pandas as pd
import numpy as np

from models import SimulatedDataset, PowerMetric
from utils.logger import get_logger

logger = get_logger(__name__)


def _ensure_dir(path: str) -> None:
    """Ensure the directory for the given path exists."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def _serialize_dataset(dataset: SimulatedDataset) -> Dict[str, Any]:
    """Convert a SimulatedDataset dataclass to a serializable dictionary."""
    result = {}
    for key, value in asdict(dataset).items():
        if isinstance(value, np.ndarray):
            result[key] = value.tolist()
        elif is_dataclass(value):
            result[key] = _serialize_dataset(value)
        else:
            result[key] = value
    return result


def _serialize_metric(metric: PowerMetric) -> Dict[str, Any]:
    """Convert a PowerMetric dataclass to a serializable dictionary."""
    result = {}
    for key, value in asdict(metric).items():
        if isinstance(value, np.ndarray):
            result[key] = value.tolist()
        elif is_dataclass(value):
            result[key] = _serialize_metric(value)
        else:
            result[key] = value
    return result


def save_simulated_datasets(
    datasets: List[SimulatedDataset],
    output_path: str,
    file_format: str = "parquet"
) -> str:
    """
    Save a list of SimulatedDataset objects to a file.

    Args:
        datasets: List of SimulatedDataset objects to save.
        output_path: Path to the output file (directory will be created).
        file_format: Either 'parquet' or 'csv'.

    Returns:
        The absolute path to the saved file.
    """
    if not datasets:
        logger.warning("No datasets to save.")
        return ""

    _ensure_dir(output_path)

    # Convert to DataFrame
    records = [_serialize_dataset(ds) for ds in datasets]
    df = pd.DataFrame(records)

    # Add metadata columns if missing
    if 'seed' not in df.columns:
        logger.warning("Seed column missing; ensuring reproducibility metadata is present.")
    
    logger.info(f"Saving {len(datasets)} simulated datasets to {output_path} ({file_format})")

    if file_format.lower() == "parquet":
        df.to_parquet(output_path, index=False, engine='pyarrow')
    elif file_format.lower() == "csv":
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}. Use 'parquet' or 'csv'.")

    logger.info(f"Successfully saved {len(datasets)} datasets to {output_path}")
    return os.path.abspath(output_path)


def save_power_metrics(
    metrics: List[PowerMetric],
    output_path: str,
    file_format: str = "csv"
) -> str:
    """
    Save a list of PowerMetric objects to a file.

    Args:
        metrics: List of PowerMetric objects to save.
        output_path: Path to the output file.
        file_format: Either 'parquet' or 'csv'.

    Returns:
        The absolute path to the saved file.
    """
    if not metrics:
        logger.warning("No power metrics to save.")
        return ""

    _ensure_dir(output_path)

    # Convert to DataFrame
    records = [_serialize_metric(m) for m in metrics]
    df = pd.DataFrame(records)

    logger.info(f"Saving {len(metrics)} power metrics to {output_path} ({file_format})")

    if file_format.lower() == "parquet":
        df.to_parquet(output_path, index=False, engine='pyarrow')
    elif file_format.lower() == "csv":
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}. Use 'parquet' or 'csv'.")

    logger.info(f"Successfully saved {len(metrics)} metrics to {output_path}")
    return os.path.abspath(output_path)


def generate_run_id(seed: int, snr: float, sparsity: float, dataset_id: Optional[int] = None) -> str:
    """
    Generate a deterministic run ID for reproducibility tracking.

    Args:
        seed: Random seed used for simulation.
        snr: Signal-to-Noise Ratio level.
        sparsity: Sparsity level.
        dataset_id: Optional OpenML dataset ID.

    Returns:
        A unique string ID.
    """
    parts = [f"seed={seed}", f"snr={snr:.2f}", f"sparsity={sparsity:.2f}"]
    if dataset_id is not None:
        parts.append(f"dataset={dataset_id}")
    
    input_str = "|".join(parts)
    return hashlib.sha256(input_str.encode()).hexdigest()[:16]


def save_simulation_manifest(
    run_ids: List[str],
    config_summary: Dict[str, Any],
    output_path: str
) -> str:
    """
    Save a manifest file describing the simulation run for reproducibility.

    Args:
        run_ids: List of run IDs generated for this batch.
        config_summary: Summary of configuration parameters used.
        output_path: Path to the manifest JSON file.

    Returns:
        The absolute path to the saved manifest.
    """
    _ensure_dir(output_path)
    
    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "run_ids": run_ids,
        "config": config_summary,
        "total_runs": len(run_ids)
    }

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved simulation manifest to {output_path}")
    return os.path.abspath(output_path)


def main():
    """
    Main entry point for testing storage functionality.
    This function creates dummy data to demonstrate the storage logic
    and writes it to the data/processed directory as per the task requirements.
    """
    from config import get_config
    
    config = get_config()
    output_dir = config.get("output_path", "data/processed")
    
    # Create dummy data to demonstrate storage
    # In a real pipeline, these would come from the simulators
    dummy_datasets = [
        SimulatedDataset(
            X=[[1.0, 2.0], [3.0, 4.0]],
            Y=[1.0, 2.0],
            true_coefficients=[0.5, -0.5],
            snr=1.0,
            sparsity=0.5,
            seed=42,
            dataset_id=12345
        ),
        SimulatedDataset(
            X=[[2.0, 3.0], [4.0, 5.0]],
            Y=[3.0, 4.0],
            true_coefficients=[0.8, -0.2],
            snr=2.0,
            sparsity=0.3,
            seed=123,
            dataset_id=12345
        )
    ]
    
    dummy_metrics = [
        PowerMetric(
            method="ForwardStepwise",
            snr=1.0,
            sparsity=0.5,
            alpha=0.05,
            power_rate=0.85,
            ci_lower=0.75,
            ci_upper=0.95
        ),
        PowerMetric(
            method="LASSO",
            snr=1.0,
            sparsity=0.5,
            alpha=0.05,
            power_rate=0.82,
            ci_lower=0.72,
            ci_upper=0.92
        )
    ]

    # Save datasets
    dataset_path = os.path.join(output_dir, "simulated_datasets.parquet")
    save_simulated_datasets(dummy_datasets, dataset_path, "parquet")

    # Save metrics
    metrics_path = os.path.join(output_dir, "power_metrics.csv")
    save_power_metrics(dummy_metrics, metrics_path, "csv")

    # Save manifest
    run_ids = [generate_run_id(d.seed, d.snr, d.sparsity, d.dataset_id) for d in dummy_datasets]
    manifest_path = os.path.join(output_dir, "simulation_manifest.json")
    save_simulation_manifest(run_ids, {"seed": config.get("seed", 42)}, manifest_path)

    logger.info("Storage logic demonstration completed. Files written to data/processed/")


if __name__ == "__main__":
    main()
