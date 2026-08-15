import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_paths


def record_simulation_result(
    eigenvalues: List[float],
    perturbation_config: Dict[str, Any],
    simulation_metadata: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Record a single simulation run's results to a JSON file in data/processed/.

    Args:
        eigenvalues: List of computed eigenvalues (sorted descending).
        perturbation_config: Dictionary describing the perturbation applied.
        simulation_metadata: Dictionary with run metadata (seed, timestamp, N, etc.).
        output_dir: Optional override for the output directory. Defaults to
                    data/processed/ based on project config.

    Returns:
        Path to the written JSON file.
    """
    if output_dir is None:
        project_paths = get_project_paths()
        output_dir = project_paths.processed_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Construct the result record
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": simulation_metadata,
        "perturbation": perturbation_config,
        "eigenvalues": eigenvalues,
    }

    # Generate a unique filename based on timestamp and seed
    seed = simulation_metadata.get("seed", 0)
    n = simulation_metadata.get("N", 0)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"run_n{n}_seed{seed}_{timestamp_str}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return output_path


def append_to_aggregated_results(
    results_path: Path,
    aggregated_file: Optional[Path] = None,
) -> Path:
    """
    Append a single result record to an aggregated JSONL (or JSON) results file.

    Args:
        results_path: Path to the single result JSON file to append.
        aggregated_file: Path to the aggregated results file. Defaults to
                         data/processed/aggregated_results.jsonl.

    Returns:
        Path to the updated aggregated file.
    """
    if aggregated_file is None:
        project_paths = get_project_paths()
        aggregated_file = project_paths.processed_dir / "aggregated_results.jsonl"

    # Read the single result
    with open(results_path, "r", encoding="utf-8") as f:
        record = json.load(f)

    # Append as a single line in JSONL format
    with open(aggregated_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return aggregated_file