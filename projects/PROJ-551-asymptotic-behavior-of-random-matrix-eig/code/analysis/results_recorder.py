"""
Results Recorder for Single Run Simulation Results.

This module implements Task T015: Add logic to record results (eigenvalues,
perturbation params) to `data/processed/single_run_results.json` with the
specified metadata schema.

Schema:
{
    "run_id": str,
    "N": int,
    "theta": float,
    "seed": int,
    "eigenvalues": list,
    "outlier_flag": bool
}
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local project structure
# Assuming this file is run from the project root or code/ directory
# Adjust imports if necessary based on execution context
try:
    from utils.config import get_project_paths
except ImportError:
    # Fallback if not run as module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.config import get_project_paths


def setup_logging() -> logging.Logger:
    """Configure logging for the results recorder."""
    logger = logging.getLogger("results_recorder")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def create_result_record(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create a result record dictionary matching the required schema.

    Args:
        run_id: Unique identifier for the simulation run.
        N: Matrix dimension.
        theta: Perturbation strength.
        seed: Random seed used.
        eigenvalues: List of computed eigenvalues (sorted descending).
        outlier_flag: Boolean indicating if an outlier was detected.
        timestamp: Optional timestamp (defaults to current UTC time).

    Returns:
        Dictionary conforming to the schema.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return {
        "run_id": run_id,
        "N": N,
        "theta": theta,
        "seed": seed,
        "eigenvalues": eigenvalues,
        "outlier_flag": outlier_flag,
        "timestamp": timestamp.isoformat()
    }


def save_single_run_results(
    record: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save a single run result record to a JSON file.

    If the file exists, it will be loaded, the new record appended,
    and the list saved back. If it does not exist, a new list is created.

    Args:
        record: The result record dictionary.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_records = []

    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_records = data
                else:
                    # If it was a single object (unexpected), wrap it
                    existing_records = [data]
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing results from {output_path}: {e}. Starting fresh.")
            existing_records = []

    existing_records.append(record)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_records, f, indent=2)

    logging.info(f"Saved result for run {record['run_id']} to {output_path}")


def load_single_run_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load existing results from the JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of result records. Empty list if file does not exist.
    """
    if not input_path.exists():
        return []

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return [data]


def run_single_run_recorder(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    output_path: Optional[Path] = None
) -> None:
    """
    Main entry point to record a single simulation run.

    Args:
        run_id: Unique identifier.
        N: Matrix dimension.
        theta: Perturbation strength.
        seed: Random seed.
        eigenvalues: Computed eigenvalues.
        outlier_flag: Outlier detection flag.
        output_path: Optional override for output file path.
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = paths.get("data_processed", Path("data/processed")) / "single_run_results.json"
        if not isinstance(output_path, Path):
            output_path = Path(output_path) / "single_run_results.json"

    record = create_result_record(
        run_id=run_id,
        N=N,
        theta=theta,
        seed=seed,
        eigenvalues=eigenvalues,
        outlier_flag=outlier_flag
    )

    save_single_run_results(record, output_path)


def main() -> None:
    """CLI entry point for T015."""
    parser = argparse.ArgumentParser(description="Record single run simulation results.")
    parser.add_argument("--run-id", type=str, required=True, help="Unique run ID")
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation strength")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--eigenvalues", type=float, nargs="+", required=True, help="List of eigenvalues")
    parser.add_argument("--outlier-flag", type=str, required=True, choices=["true", "false"],
                        help="Outlier flag (true/false)")
    parser.add_argument("--output", type=str, default=None, help="Output file path")

    args = parser.parse_args()

    setup_logging()

    outlier_flag = args.outlier_flag.lower() == "true"

    output_path = Path(args.output) if args.output else None

    run_single_run_recorder(
        run_id=args.run_id,
        N=args.N,
        theta=args.theta,
        seed=args.seed,
        eigenvalues=list(args.eigenvalues),
        outlier_flag=outlier_flag,
        output_path=output_path
    )


if __name__ == "__main__":
    main()