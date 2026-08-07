import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_paths

def _get_checksum(data: Dict[str, Any]) -> str:
    """Generate a deterministic checksum for result data."""
    normalized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def record_simulation_result(
    seed: int,
    matrix_size: int,
    perturbation_norm: float,
    perturbation_type: str,
    eigenvalues: List[float],
    outlier_indices: List[int],
    theoretical_edge: float,
    is_outlier_present: bool,
    sparsity_density: Optional[float] = None,
    execution_time_seconds: Optional[float] = None,
) -> Path:
    """
    Records a single simulation result to data/processed/ with metadata.
    Returns the path to the written JSON file.
    """
    paths = get_project_paths()
    processed_dir = paths["data"] / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    result_id = f"run_{seed}_{matrix_size}_{int(perturbation_norm * 1000)}"

    result_data: Dict[str, Any] = {
        "result_id": result_id,
        "timestamp": timestamp,
        "parameters": {
            "seed": seed,
            "matrix_size": matrix_size,
            "perturbation_norm": perturbation_norm,
            "perturbation_type": perturbation_type,
            "sparsity_density": sparsity_density,
        },
        "results": {
            "eigenvalues": eigenvalues,
            "outlier_indices": outlier_indices,
            "theoretical_edge": theoretical_edge,
            "is_outlier_present": is_outlier_present,
        },
        "metadata": {
            "checksum": _get_checksum(result_data),
        },
    }

    if execution_time_seconds is not None:
        result_data["metadata"]["execution_time_seconds"] = execution_time_seconds

    output_file = processed_dir / f"{result_id}.json"
    with open(output_file, "w") as f:
        json.dump(result_data, f, indent=2)

    return output_file

def append_to_aggregated_results(
    result_path: Path,
    aggregated_file: Optional[Path] = None,
) -> Path:
    """
    Appends a single result to an aggregated CSV file for sweep analysis.
    Converts JSON result to CSV row format.
    """
    if aggregated_file is None:
        paths = get_project_paths()
        aggregated_file = paths["data"] / "processed" / "aggregated_results.csv"

    with open(result_path, "r") as f:
        data = json.load(f)

    params = data["parameters"]
    results = data["results"]
    meta = data["metadata"]

    row = {
        "result_id": data["result_id"],
        "timestamp": data["timestamp"],
        "seed": params["seed"],
        "matrix_size": params["matrix_size"],
        "perturbation_norm": params["perturbation_norm"],
        "perturbation_type": params["perturbation_type"],
        "sparsity_density": params.get("sparsity_density"),
        "top_eigenvalue": results["eigenvalues"][0] if results["eigenvalues"] else None,
        "num_outliers": len(results["outlier_indices"]),
        "is_outlier_present": results["is_outlier_present"],
        "checksum": meta["checksum"],
    }

    file_exists = aggregated_file.exists()
    with open(aggregated_file, "a") as f:
        if not file_exists:
            f.write(",".join(row.keys()) + "\n")
        f.write(",".join(str(v) for v in row.values()) + "\n")

    return aggregated_file
