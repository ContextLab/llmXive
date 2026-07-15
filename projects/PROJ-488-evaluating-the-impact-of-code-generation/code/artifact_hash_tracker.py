"""
Artifact Hash Tracker for PROJ-488.

This module implements artifact-hash tracking as per Task T038.
It computes SHA-256 hashes for major outputs (datasets, metrics, stats, figures)
and records them in the project state file:
state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml
"""

import hashlib
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

# Import existing utilities from the project
from state_tracker import (
    load_state_file,
    save_state_file,
    compute_file_hash,
    compute_directory_hash,
    update_state_timestamp
)
from logging_config import setup_logger, get_logger

# Project constants
PROJECT_ID = "PROJ-488-evaluating-the-impact-of-code-generation"
STATE_FILE_PATH = Path("state/projects") / f"{PROJECT_ID}.yaml"
DATA_DIR = Path("data")
METRICS_DIR = Path("data/metrics")
RESULTS_DIR = Path("results")
FIGURES_DIR = Path("results/figures")

# Initialize logger
logger = setup_logger("artifact_hash_tracker", logging.INFO)


def get_artifact_type(file_path: Path) -> str:
    """
    Determine the category of an artifact based on its path.
    Returns one of: 'dataset', 'metric', 'stat', 'figure', 'other'
    """
    try:
        relative = file_path.resolve().relative_to(Path.cwd())
    except ValueError:
        return "other"

    if relative.parts[0] == "data" and "metrics" not in relative.parts:
        if "raw" in relative.parts or "processed" in relative.parts:
            return "dataset"
    elif relative.parts[0] == "data" and "metrics" in relative.parts:
        return "metric"
    elif relative.parts[0] == "results" and "figures" in relative.parts:
        return "figure"
    elif relative.parts[0] == "results" and "figures" not in relative.parts:
        # Statistical reports, sensitivity analysis, etc.
        return "stat"

    return "other"


def hash_artifact(path: Path) -> str:
    """
    Compute SHA-256 hash of a file or directory.
    For directories, computes a combined hash of all contained files.
    """
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    if path.is_file():
        return compute_file_hash(path)
    elif path.is_dir():
        return compute_directory_hash(path)
    else:
        raise ValueError(f"Invalid path type: {path}")


def register_artifact(
    artifact_path: Union[str, Path],
    state_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute hash for a specific artifact and register it in the state file.

    Args:
        artifact_path: Path to the file or directory to hash.
        state_file: Optional custom state file path (defaults to project state).

    Returns:
        Dictionary containing the artifact info and hash.
    """
    if state_file is None:
        state_file = STATE_FILE_PATH

    path = Path(artifact_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    logger.info(f"Registering artifact: {path}")

    try:
        artifact_hash = hash_artifact(path)
        artifact_type = get_artifact_type(path)
        timestamp = datetime.utcnow().isoformat()

        record = {
            "path": str(path.relative_to(Path.cwd())),
            "type": artifact_type,
            "hash": artifact_hash,
            "registered_at": timestamp
        }

        # Load state
        state = load_state_file(state_file)

        # Ensure artifact tracking section exists
        if "artifact_hashes" not in state:
            state["artifact_hashes"] = []

        # Check for duplicates (by path)
        existing_paths = {item["path"] for item in state["artifact_hashes"]}
        if str(path.relative_to(Path.cwd())) in existing_paths:
            logger.warning(f"Artifact already registered, updating hash: {path}")
            # Update existing entry
            for item in state["artifact_hashes"]:
                if item["path"] == str(path.relative_to(Path.cwd())):
                    item["hash"] = artifact_hash
                    item["registered_at"] = timestamp
                    item["type"] = artifact_type
                    break
        else:
            # Add new entry
            state["artifact_hashes"].append(record)
            logger.info(f"Registered new artifact: {path} (type: {artifact_type})")

        # Update timestamp
        state = update_state_timestamp(state)

        # Save state
        save_state_file(state, state_file)
        logger.info(f"State file updated: {state_file}")

        return record

    except Exception as e:
        logger.error(f"Failed to register artifact {path}: {e}")
        raise


def track_all_major_outputs(
    state_file: Optional[Path] = None,
    include_datasets: bool = True,
    include_metrics: bool = True,
    include_stats: bool = True,
    include_figures: bool = True
) -> List[Dict[str, Any]]:
    """
    Scan major output directories and register all found artifacts.

    Args:
        state_file: Optional custom state file path.
        include_datasets: Whether to track files in data/raw and data/processed.
        include_metrics: Whether to track files in data/metrics.
        include_stats: Whether to track files in results (excluding figures).
        include_figures: Whether to track files in results/figures.

    Returns:
        List of registered artifact records.
    """
    if state_file is None:
        state_file = STATE_FILE_PATH

    registered = []

    # Track datasets
    if include_datasets:
        for subdir in ["raw", "processed"]:
            dir_path = DATA_DIR / subdir
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            record = register_artifact(file_path, state_file)
                            registered.append(record)
                        except Exception as e:
                            logger.error(f"Skipped {file_path}: {e}")

    # Track metrics
    if include_metrics and METRICS_DIR.exists():
        for file_path in METRICS_DIR.rglob("*"):
            if file_path.is_file():
                try:
                    record = register_artifact(file_path, state_file)
                    registered.append(record)
                except Exception as e:
                    logger.error(f"Skipped {file_path}: {e}")

    # Track statistics (results excluding figures)
    if include_stats and RESULTS_DIR.exists():
        for file_path in RESULTS_DIR.rglob("*"):
            if file_path.is_file() and "figures" not in file_path.parts:
                try:
                    record = register_artifact(file_path, state_file)
                    registered.append(record)
                except Exception as e:
                    logger.error(f"Skipped {file_path}: {e}")

    # Track figures
    if include_figures and FIGURES_DIR.exists():
        for file_path in FIGURES_DIR.rglob("*"):
            if file_path.is_file():
                try:
                    record = register_artifact(file_path, state_file)
                    registered.append(record)
                except Exception as e:
                    logger.error(f"Skipped {file_path}: {e}")

    logger.info(f"Successfully registered {len(registered)} artifacts.")
    return registered


def verify_artifact_integrity(
    artifact_path: Union[str, Path],
    expected_hash: str,
    state_file: Optional[Path] = None
) -> bool:
    """
    Verify that an artifact's current hash matches the expected hash.

    Args:
        artifact_path: Path to the artifact.
        expected_hash: The expected SHA-256 hash.
        state_file: Optional custom state file path.

    Returns:
        True if hash matches, False otherwise.
    """
    path = Path(artifact_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    current_hash = hash_artifact(path)

    if current_hash == expected_hash:
        logger.info(f"Integrity check passed for: {path}")
        return True
    else:
        logger.error(f"Integrity check FAILED for {path}: expected {expected_hash}, got {current_hash}")
        return False


def main():
    """
    CLI entry point for artifact hash tracking.
    Usage: python code/artifact_hash_tracker.py [--track-all] [--verify <path> <hash>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Artifact Hash Tracker")
    parser.add_argument(
        "--track-all",
        action="store_true",
        help="Scan and register all major output artifacts."
    )
    parser.add_argument(
        "--register",
        type=str,
        metavar="PATH",
        help="Register a specific file or directory."
    )
    parser.add_argument(
        "--verify",
        nargs=2,
        metavar=("PATH", "HASH"),
        help="Verify integrity of an artifact against an expected hash."
    )
    parser.add_argument(
        "--state",
        type=str,
        default=str(STATE_FILE_PATH),
        help="Path to the state YAML file."
    )

    args = parser.parse_args()
    state_path = Path(args.state)

    if args.verify:
        path, expected_hash = args.verify
        success = verify_artifact_integrity(path, expected_hash, state_path)
        return 0 if success else 1

    if args.register:
        try:
            register_artifact(args.register, state_path)
            return 0
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return 1

    if args.track_all:
        try:
            track_all_major_outputs(state_path)
            return 0
        except Exception as e:
            logger.error(f"Tracking all failed: {e}")
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
