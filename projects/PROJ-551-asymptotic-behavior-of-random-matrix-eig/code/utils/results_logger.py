"""
Utilities for recording simulation results to JSON files.
Satisfies Constitution Principle III (Data Hygiene).
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
    output_path: Optional[Path] = None
) -> Path:
    """
    Record a single simulation run result to a JSON file.

    Args:
        run_id: Unique identifier for the run.
        N: Matrix dimension.
        theta: Perturbation norm.
        seed: Random seed used.
        eigenvalues: List of computed eigenvalues (top k).
        outlier_flag: Boolean indicating if an outlier was detected.
        output_path: Optional specific path to write results. If None, uses
                     project paths from config.

    Returns:
        Path to the written results file.

    Schema:
        {
            "run_id": str,
            "N": int,
            "theta": float,
            "seed": int,
            "eigenvalues": list,
            "outlier_flag": bool,
            "timestamp": str (ISO 8601)
        }
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = paths["processed"] / "single_run_results.json"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_data = {
        "run_id": run_id,
        "N": N,
        "theta": theta,
        "seed": seed,
        "eigenvalues": eigenvalues,
        "outlier_flag": outlier_flag,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)

    return output_path


def append_to_aggregated_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Append a list of results to an aggregated JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Optional specific path. Defaults to aggregated results file.

    Returns:
        Path to the aggregated file.
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = paths["processed"] / "aggregated_results.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data if file exists
    existing_data = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_data = []

    # Append new results
    existing_data.extend(results)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)

    return output_path
