"""
Results Recorder for User Story 1 (T015).

This module implements the logic to record simulation results (eigenvalues,
perturbation params) to `data/processed/single_run_results.json`.

It satisfies Constitution Principle III (Data Hygiene) by ensuring structured,
schema-compliant output for every simulation run.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project paths and config utilities
from utils.config import get_project_paths, ensure_directories

# Setup logging
def setup_logging() -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def create_result_record(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    perturbation_type: Optional[str] = "diagonal",
    perturbation_rank: Optional[int] = 1
) -> Dict[str, Any]:
    """
    Create a result record dictionary adhering to the T015 schema.

    Schema:
    {
      "run_id": str,
      "N": int,
      "theta": float,
      "seed": int,
      "eigenvalues": list[float],
      "outlier_flag": bool,
      "metadata": {
         "timestamp": str,
         "perturbation_type": str,
         "perturbation_rank": int
      }
    }
    """
    return {
        "run_id": run_id,
        "N": N,
        "theta": float(theta),
        "seed": int(seed),
        "eigenvalues": [float(ev) for ev in eigenvalues],
        "outlier_flag": bool(outlier_flag),
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "perturbation_type": perturbation_type,
            "perturbation_rank": perturbation_rank
        }
    }

def save_single_run_results(
    record: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save the result record to the specified JSON path.

    If output_path is None, defaults to `data/processed/single_run_results.json`.
    Creates the directory if it does not exist.
    Overwrites the file if it exists (single run mode).
    """
    if output_path is None:
        project_paths = get_project_paths()
        output_path = str(project_paths["processed"] / "single_run_results.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving results to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2)

    logger.info(f"Successfully saved results to {output_file}")
    return str(output_file)

def load_single_run_results(
    input_path: Optional[str] = None
) -> Dict[str, Any]:
    """Load the single run results file."""
    if input_path is None:
        project_paths = get_project_paths()
        input_path = str(project_paths["processed"] / "single_run_results.json")

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_single_run_recorder(
    run_id: str,
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    outlier_flag: bool,
    perturbation_type: str = "diagonal",
    perturbation_rank: int = 1
) -> str:
    """
    Main entry point to orchestrate result recording.
    Returns the path to the saved file.
    """
    record = create_result_record(
        run_id=run_id,
        N=N,
        theta=theta,
        seed=seed,
        eigenvalues=eigenvalues,
        outlier_flag=outlier_flag,
        perturbation_type=perturbation_type,
        perturbation_rank=perturbation_rank
    )
    return save_single_run_results(record)

def main():
    """
    CLI entry point for testing the recorder independently.
    Example:
    python code/analysis/results_recorder.py --run_id test1 --N 100 --theta 2.5 --seed 42 --eigenvalues 2.1 2.05 1.9 --outlier True
    """
    parser = argparse.ArgumentParser(description="Record simulation results to JSON.")
    parser.add_argument("--run_id", type=str, required=True, help="Unique run identifier")
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation strength")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--eigenvalues", type=float, nargs='+', required=True, help="Top eigenvalues")
    parser.add_argument("--outlier", type=str, required=True, choices=["True", "False"], help="Outlier flag")
    parser.add_argument("--type", type=str, default="diagonal", help="Perturbation type")
    parser.add_argument("--rank", type=int, default=1, help="Perturbation rank")
    parser.add_argument("--output", type=str, default=None, help="Output file path (optional)")

    args = parser.parse_args()

    try:
        path = run_single_run_recorder(
            run_id=args.run_id,
            N=args.N,
            theta=args.theta,
            seed=args.seed,
            eigenvalues=args.eigenvalues,
            outlier_flag=(args.outlier == "True"),
            perturbation_type=args.type,
            perturbation_rank=args.rank
        )
        print(f"Results recorded to: {path}")
    except Exception as e:
        logger.error(f"Failed to record results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()