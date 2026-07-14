"""
Residual Logger for Eigenvalue Problems (Constitution Principle VI)

This module provides utilities to log residual norms and convergence flags
for every eigenvalue problem solved in the project. It ensures reproducibility
and numerical diagnostics by writing results to `data/metadata/residuals.json`.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from config import get_config
from logger_utils import get_logger

# Ensure the logger is configured
logger = get_logger(__name__)


def log_eigenvalue_residual(
    realization_id: int,
    disorder_width: float,
    system_size: int,
    eigenvalue_index: int,
    eigenvalue: float,
    residual_norm: float,
    converged: bool,
    solver_type: str,
    energy_window: Optional[Tuple[float, float]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a single eigenvalue residual entry.

    Args:
        realization_id: Unique identifier for the disorder realization.
        disorder_width: The disorder width W.
        system_size: The system size L.
        eigenvalue_index: Index of the eigenvalue in the sorted spectrum.
        eigenvalue: The computed eigenvalue.
        residual_norm: The residual norm ||Hv - Ev||.
        converged: Boolean flag indicating if the solver converged.
        solver_type: Type of solver used ('dense' or 'sparse').
        energy_window: Optional tuple (min_e, max_e) if filtering was applied.
        timestamp: Optional ISO timestamp string.

    Returns:
        A dictionary representing the log entry.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    entry = {
        "timestamp": timestamp,
        "realization_id": realization_id,
        "disorder_width": disorder_width,
        "system_size": system_size,
        "eigenvalue_index": eigenvalue_index,
        "eigenvalue": float(eigenvalue),
        "residual_norm": float(residual_norm),
        "converged": converged,
        "solver_type": solver_type,
        "energy_window": list(energy_window) if energy_window else None
    }

    logger.debug(f"Logged residual for realization {realization_id}, idx {eigenvalue_index}: "
                 f"norm={residual_norm:.2e}, converged={converged}")

    return entry


def save_residuals_to_file(
    entries: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save a list of residual log entries to a JSON file.

    Args:
        entries: List of dictionaries containing residual data.
        output_path: Optional path to the output file. If None, uses the default
                     path from config: `data/metadata/residuals.json`.

    Returns:
        The absolute path to the saved file.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.DATA_METADATA_DIR / "residuals.json")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if file exists to append or overwrite
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
            if isinstance(existing_data, list):
                existing_data.extend(entries)
            else:
                # If it's a dict or other format, overwrite to avoid corruption
                existing_data = entries
        except json.JSONDecodeError:
            logger.warning(f"Existing residuals.json is corrupted. Overwriting.")
            existing_data = entries
    else:
        existing_data = entries

    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Saved {len(entries)} residual entries to {output_path}")
    return output_path


def append_residuals_to_file(
    new_entries: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Append new residual entries to the existing residuals.json file.
    This is the preferred method for incremental logging during batch processing.

    Args:
        new_entries: List of new residual log entries.
        output_path: Optional path to the output file.

    Returns:
        The absolute path to the file.
    """
    return save_residuals_to_file(new_entries, output_path)


def main():
    """
    Main function for testing the residual logger.
    Generates dummy data and writes it to the metadata file.
    """
    config = get_config()
    logger.info("Running residual logger test...")

    dummy_entries = []
    for i in range(5):
        entry = log_eigenvalue_residual(
            realization_id=100 + i,
            disorder_width=1.0 + i * 0.5,
            system_size=100,
            eigenvalue_index=i,
            eigenvalue=float(-2.0 + i * 0.1),
            residual_norm=1e-10 + i * 1e-12,
            converged=True,
            solver_type="dense",
            energy_window=(-0.1, 0.1)
        )
        dummy_entries.append(entry)

    path = save_residuals_to_file(dummy_entries)
    logger.info(f"Test complete. Residuals saved to: {path}")


if __name__ == "__main__":
    main()