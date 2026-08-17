"""
Results logging utilities for simulation outputs.

This module provides functions to record simulation results to JSON files,
satisfying Constitution Principle III (Data Hygiene) by ensuring all
experimental outputs are persisted with full metadata.
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_paths


def record_simulation_result(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    output_path: Optional[str] = None,
) -> str:
    """
    Record a single simulation run result to a JSON file.

    The output file satisfies Constitution Principle III (Data Hygiene) by
    persisting all run parameters and results with metadata.

    Args:
        run_id: Unique identifier for this simulation run.
        N: Matrix dimension.
        theta: Perturbation norm parameter.
        seed: Random seed used for reproducibility.
        eigenvalues: List of computed top eigenvalues.
        outlier_flag: Boolean indicating if an outlier was detected.
        output_path: Optional custom output path. If None, uses default path.

    Returns:
        Path to the written JSON file.

    Raises:
        ValueError: If required fields are missing or invalid.
        IOError: If file cannot be written.
    """
    if not run_id or not isinstance(run_id, str):
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(N, int) or N <= 0:
        raise ValueError("N must be a positive integer")
    if not isinstance(theta, (int, float)):
        raise ValueError("theta must be a number")
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(eigenvalues, list):
        raise ValueError("eigenvalues must be a list")
    if not isinstance(outlier_flag, bool):
        raise ValueError("outlier_flag must be a boolean")

    project_paths = get_project_paths()
    if output_path is None:
        output_path = str(project_paths["data_processed"] / "single_run_results.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result_record = {
        "run_id": run_id,
        "N": N,
        "theta": float(theta),
        "seed": seed,
        "eigenvalues": [float(ev) for ev in eigenvalues],
        "outlier_flag": outlier_flag,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "schema_version": "1.0",
            "constitution_principle": "III",
            "principle_name": "Data Hygiene",
        },
    }

    # Check if file exists and load existing results
    existing_results = []
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_results = json.loads(content)
                    if not isinstance(existing_results, list):
                        existing_results = [existing_results]
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted or unreadable, start fresh
            existing_results = []

    # Append new result
    existing_results.append(result_record)

    # Write back with proper formatting
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, indent=2)

    return str(output_file)


def append_to_aggregated_results(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None,
) -> str:
    """
    Append multiple results to an aggregated JSON file.

    Args:
        results: List of result dictionaries to append.
        output_path: Optional custom output path. If None, uses default path.

    Returns:
        Path to the written JSON file.

    Raises:
        ValueError: If results is not a list or contains invalid entries.
        IOError: If file cannot be written.
    """
    if not isinstance(results, list):
        raise ValueError("results must be a list of dictionaries")

    project_paths = get_project_paths()
    if output_path is None:
        output_path = str(project_paths["data_processed"] / "aggregated_results.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing results if file exists
    existing_results = []
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_results = json.loads(content)
                    if not isinstance(existing_results, list):
                        existing_results = [existing_results]
        except (json.JSONDecodeError, IOError):
            existing_results = []

    # Append new results
    existing_results.extend(results)

    # Write back
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, indent=2)

    return str(output_file)