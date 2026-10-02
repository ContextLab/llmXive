"""
Task T019b: TRACEABILITY - Register checksum with SimulationRun metadata.

This task creates or updates the state/metadata_registry.json file to link
the checksum generated in T019 with the SimulationRun metadata record.

JSON Schema:
{
  "runs": [
    {
      "run_id": str,
      "checksum": str,
      "parameters": {
        "N": int,
        "seed": int,
        "theta": float
      }
    }
  ]
}
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Import project utilities
from utils.config import get_project_paths


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging for the traceability task."""
    logger = logging.getLogger("task019b_traceability")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def load_checksum_manifest(checksum_file: Path) -> Dict[str, str]:
    """
    Load the checksum manifest produced by T019.

    Expected format:
    {
      "checksums": [
        {"file": "path/to/file.npy", "checksum": "sha256_hash"},
        ...
      ]
    }
    """
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {checksum_file}")

    with open(checksum_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {item["file"]: item["checksum"] for item in data.get("checksums", [])}


def load_single_run_results(results_file: Path) -> Optional[Dict[str, Any]]:
    """
    Load the single run results produced by T014/T015.

    Expected format:
    {
      "run_id": str,
      "N": int,
      "theta": float,
      "seed": int,
      "eigenvalues": list,
      "outlier_flag": bool
    }
    """
    if not results_file.exists():
        return None

    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def find_checksum_for_run(
    checksums: Dict[str, str],
    run_id: str,
    N: int,
    seed: int
) -> Optional[str]:
    """
    Find the checksum for the raw matrix associated with this run.

    The raw matrix file is expected to be named:
    data/raw/matrix_N{N}_seed{seed}.npy
    """
    expected_file = f"data/raw/matrix_N{N}_seed{seed}.npy"

    # Check if exact match exists
    if expected_file in checksums:
        return checksums[expected_file]

    # Try to find by scanning for matching pattern
    for file_path, checksum in checksums.items():
        if f"matrix_N{N}_seed{seed}" in file_path:
            return checksum

    return None


def update_run_metadata(
    registry_path: Path,
    run_id: str,
    checksum: str,
    N: int,
    seed: int,
    theta: float
) -> None:
    """
    Update or create the metadata registry with the new run entry.

    Schema:
    {
      "runs": [
        {
          "run_id": str,
          "checksum": str,
          "parameters": {
            "N": int,
            "seed": int,
            "theta": float
          }
        }
      ]
    }
    """
    # Load existing registry if it exists
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {"runs": []}

    # Ensure runs key exists
    if "runs" not in registry:
        registry["runs"] = []

    # Check if run_id already exists
    existing_run = None
    for run in registry["runs"]:
        if run.get("run_id") == run_id:
            existing_run = run
            break

    if existing_run:
        # Update existing entry
        existing_run["checksum"] = checksum
        existing_run["parameters"] = {
            "N": N,
            "seed": seed,
            "theta": theta
        }
    else:
        # Add new entry
        new_run = {
            "run_id": run_id,
            "checksum": checksum,
            "parameters": {
                "N": N,
                "seed": seed,
                "theta": theta
            }
        }
        registry["runs"].append(new_run)

    # Write updated registry
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def save_updated_results(
    results_file: Path,
    run_id: str,
    checksum: str
) -> None:
    """
    Save the updated results with checksum information.
    This ensures the results file is linked to its checksum.
    """
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_file}")

    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    results["checksum"] = checksum
    results["metadata_updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def main() -> int:
    """
    Main entry point for T019b traceability task.

    Usage:
      python code/analysis/task019b_traceability.py \
        --checksum-manifest state/checksums_manifest.json \
        --results-file data/processed/single_run_results.json \
        --registry state/metadata_registry.json
    """
    parser = argparse.ArgumentParser(
        description="T019b: Register checksum with SimulationRun metadata"
    )
    parser.add_argument(
        "--checksum-manifest",
        type=str,
        required=True,
        help="Path to checksum manifest from T019"
    )
    parser.add_argument(
        "--results-file",
        type=str,
        required=True,
        help="Path to single run results JSON"
    )
    parser.add_argument(
        "--registry",
        type=str,
        default="state/metadata_registry.json",
        help="Path to metadata registry JSON (default: state/metadata_registry.json)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (optional)"
    )

    args = parser.parse_args()

    # Setup logging
    log_path = Path(args.log_file) if args.log_file else None
    logger = setup_logging(log_path)
    logger.info("Starting T019b traceability task")

    try:
        # Get project paths
        paths = get_project_paths()

        # Resolve paths
        checksum_manifest_path = Path(args.checksum_manifest)
        results_file_path = Path(args.results_file)
        registry_path = Path(args.registry)

        if not checksum_manifest_path.exists():
            logger.error(f"Checksum manifest not found: {checksum_manifest_path}")
            return 1

        if not results_file_path.exists():
            logger.error(f"Results file not found: {results_file_path}")
            return 1

        # Load checksum manifest
        logger.info(f"Loading checksum manifest from {checksum_manifest_path}")
        checksums = load_checksum_manifest(checksum_manifest_path)
        logger.info(f"Loaded {len(checksums)} checksum entries")

        # Load single run results
        logger.info(f"Loading results from {results_file_path}")
        results = load_single_run_results(results_file_path)

        if results is None:
            logger.error("Failed to load results file")
            return 1

        # Extract parameters from results
        run_id = results.get("run_id")
        N = results.get("N")
        seed = results.get("seed")
        theta = results.get("theta")

        if run_id is None or N is None or seed is None or theta is None:
            logger.error("Missing required fields in results: run_id, N, seed, theta")
            return 1

        logger.info(f"Run parameters: run_id={run_id}, N={N}, seed={seed}, theta={theta}")

        # Find checksum for this run
        logger.info("Searching for matching checksum...")
        checksum = find_checksum_for_run(checksums, run_id, N, seed)

        if checksum is None:
            logger.error(f"No checksum found for run: run_id={run_id}, N={N}, seed={seed}")
            logger.error("Available checksums:")
            for file_path in checksums.keys():
                logger.error(f"  - {file_path}")
            return 1

        logger.info(f"Found checksum: {checksum[:16]}...")

        # Update metadata registry
        logger.info(f"Updating metadata registry: {registry_path}")
        update_run_metadata(
            registry_path=registry_path,
            run_id=run_id,
            checksum=checksum,
            N=N,
            seed=seed,
            theta=theta
        )
        logger.info("Metadata registry updated successfully")

        # Update results file with checksum
        logger.info("Updating results file with checksum...")
        save_updated_results(results_file_path, run_id, checksum)
        logger.info("Results file updated successfully")

        logger.info("T019b traceability task completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())