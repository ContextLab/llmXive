"""
Artifact Hash Tracker Module for PROJ-488.

This module implements SHA-256 hash tracking for major pipeline outputs
(datasets, metrics, statistics, figures) and records them in the project state file.
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Import existing project utilities
from state_tracker import load_state_file, save_state_file, ensure_state_directory
from logging_config import get_logger

# Constants
STATE_FILE_PATH = "state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml"
DATA_DIR = Path("data")
METRICS_DIR = Path("data/metrics")
RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"

logger = get_logger(__name__)


def compute_hash_for_path(file_path: Union[str, Path]) -> Optional[str]:
    """
    Compute SHA-256 hash of a single file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hex digest string or None if file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found for hashing: {path}")
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {path}: {e}")
        return None


def compute_directory_hash(dir_path: Union[str, Path]) -> Optional[str]:
    """
    Compute a combined SHA-256 hash for all files in a directory.
    Sorts files to ensure deterministic ordering.

    Args:
        dir_path: Path to the directory.

    Returns:
        Hex digest string or None if directory doesn't exist.
    """
    path = Path(dir_path)
    if not path.exists():
        logger.warning(f"Directory not found for hashing: {path}")
        return None

    if not path.is_dir():
        logger.warning(f"Path is not a directory: {path}")
        return None

    sha256_hash = hashlib.sha256()
    files = sorted([f for f in path.rglob("*") if f.is_file()])

    if not files:
        logger.warning(f"No files found in directory: {path}")
        return None

    # Hash the relative paths and contents of all files
    for file_path in files:
        # Include relative path in hash
        rel_path = file_path.relative_to(path)
        sha256_hash.update(str(rel_path).encode('utf-8'))
        sha256_hash.update(b"\x00") # Separator

        # Hash file contents
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return None

    return sha256_hash.hexdigest()


def track_dataset_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and record hashes for dataset artifacts.

    Args:
        state: Current state dictionary.

    Returns:
        Updated state dictionary.
    """
    datasets_section = state.setdefault("artifacts", {}).setdefault("datasets", {})
    datasets_section["updated_at"] = datetime.now().isoformat()

    # Check for downloaded dataset files (expected by T012-T015)
    # We look for processed JSONL or parquet files in data/raw or data/processed
    data_processed = DATA_DIR / "processed"
    data_raw = DATA_DIR / "raw"

    if data_processed.exists():
        dataset_hash = compute_directory_hash(data_processed)
        if dataset_hash:
            datasets_section["processed_hash"] = dataset_hash
            logger.info(f"Recorded processed dataset hash: {dataset_hash[:16]}...")

    if data_raw.exists():
        raw_hash = compute_directory_hash(data_raw)
        if raw_hash:
            datasets_section["raw_hash"] = raw_hash
            logger.info(f"Recorded raw dataset hash: {raw_hash[:16]}...")

    # Also check checksums.json if it exists (created by T005/T013)
    checksum_file = DATA_DIR / "checksums.json"
    if checksum_file.exists():
        checksum_hash = compute_hash_for_path(checksum_file)
        if checksum_hash:
            datasets_section["checksums_file_hash"] = checksum_hash
            logger.info(f"Recorded checksums file hash: {checksum_hash[:16]}...")

    return state


def track_metric_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and record hashes for metric artifacts.

    Args:
        state: Current state dictionary.

    Returns:
        Updated state dictionary.
    """
    metrics_section = state.setdefault("artifacts", {}).setdefault("metrics", {})
    metrics_section["updated_at"] = datetime.now().isoformat()

    if METRICS_DIR.exists():
        metrics_hash = compute_directory_hash(METRICS_DIR)
        if metrics_hash:
            metrics_section["directory_hash"] = metrics_hash
            logger.info(f"Recorded metrics directory hash: {metrics_hash[:16]}...")

        # Also hash individual CSV files if present
        csv_files = list(METRICS_DIR.glob("*.csv"))
        if csv_files:
            file_hashes = {}
            for csv_file in sorted(csv_files):
                h = compute_hash_for_path(csv_file)
                if h:
                    file_hashes[csv_file.name] = h
            if file_hashes:
                metrics_section["file_hashes"] = file_hashes
                logger.info(f"Recorded {len(file_hashes)} individual metric file hashes")

    return state


def track_statistical_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and record hashes for statistical analysis artifacts.

    Args:
        state: Current state dictionary.

    Returns:
        Updated state dictionary.
    """
    stats_section = state.setdefault("artifacts", {}).setdefault("statistics", {})
    stats_section["updated_at"] = datetime.now().isoformat()

    # Expected outputs from Phase 5 (T026-T035)
    stat_files = [
        RESULTS_DIR / "statistical_results.json",
        RESULTS_DIR / "guidelines.md",
        RESULTS_DIR / "sensitivity.md",
        RESULTS_DIR / "pilot_study.md",
        RESULTS_DIR / "justification.md",
        RESULTS_DIR / "independence.md"
    ]

    file_hashes = {}
    for stat_file in stat_files:
        if stat_file.exists():
            h = compute_hash_for_path(stat_file)
            if h:
                file_hashes[stat_file.name] = h
                logger.info(f"Recorded hash for {stat_file.name}: {h[:16]}...")

    if file_hashes:
        stats_section["file_hashes"] = file_hashes

    # Check for directory if it exists
    if RESULTS_DIR.exists():
        # Look for any JSON files in results that might be statistical outputs
        json_files = list(RESULTS_DIR.glob("*.json"))
        for json_file in json_files:
            if json_file.name not in file_hashes:
                h = compute_hash_for_path(json_file)
                if h:
                    file_hashes[json_file.name] = h
                    stats_section["file_hashes"] = file_hashes

    return state


def track_figure_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and record hashes for figure artifacts.

    Args:
        state: Current state dictionary.

    Returns:
        Updated state dictionary.
    """
    fig_section = state.setdefault("artifacts", {}).setdefault("figures", {})
    fig_section["updated_at"] = datetime.now().isoformat()

    if FIGURES_DIR.exists():
        fig_hash = compute_directory_hash(FIGURES_DIR)
        if fig_hash:
            fig_section["directory_hash"] = fig_hash
            logger.info(f"Recorded figures directory hash: {fig_hash[:16]}...")

        # Hash individual figure files
        fig_files = list(FIGURES_DIR.glob("*"))
        if fig_files:
            file_hashes = {}
            for fig_file in sorted(fig_files):
                if fig_file.is_file():
                    h = compute_hash_for_path(fig_file)
                    if h:
                        file_hashes[fig_file.name] = h
            if file_hashes:
                fig_section["file_hashes"] = file_hashes
                logger.info(f"Recorded {len(file_hashes)} individual figure hashes")

    return state


def update_state_with_all_artifacts(state_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Main entry point to compute hashes for all major artifact categories
    and update the state file.

    Args:
        state_path: Optional path to the state file. Defaults to STATE_FILE_PATH.

    Returns:
        The updated state dictionary.
    """
    if state_path is None:
        state_path = STATE_FILE_PATH
    else:
        state_path = Path(state_path)

    # Ensure directory exists
    ensure_state_directory(state_path)

    # Load current state
    try:
        state = load_state_file(state_path)
    except FileNotFoundError:
        logger.warning(f"State file not found at {state_path}. Creating new state.")
        state = {
            "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
            "artifacts": {},
            "amendment_status": {},
            "updated_at": datetime.now().isoformat()
        }

    # Track each category
    logger.info("Tracking dataset artifacts...")
    state = track_dataset_artifacts(state)

    logger.info("Tracking metric artifacts...")
    state = track_metric_artifacts(state)

    logger.info("Tracking statistical artifacts...")
    state = track_statistical_artifacts(state)

    logger.info("Tracking figure artifacts...")
    state = track_figure_artifacts(state)

    # Update global timestamp
    state["updated_at"] = datetime.now().isoformat()

    # Save state
    save_state_file(state_path, state)
    logger.info(f"State file updated at {state_path}")

    return state


def verify_artifact_integrity(state_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Verify that artifact hashes in the state file match current file hashes.

    Args:
        state_path: Optional path to the state file.

    Returns:
        True if all artifacts match, False otherwise.
    """
    if state_path is None:
        state_path = STATE_FILE_PATH

    state = load_state_file(state_path)
    artifacts = state.get("artifacts", {})
    all_valid = True

    # Verify datasets
    if "datasets" in artifacts:
        ds_info = artifacts["datasets"]
        if "processed_hash" in ds_info:
            if not DATA_DIR / "processed" / ".gitkeep".exists(): # Check if dir has content
                # We can't easily verify empty dirs, but we check if the hash exists
                logger.warning("Processed dataset directory might be missing.")
                # Re-compute to see if it matches
                current_hash = compute_directory_hash(DATA_DIR / "processed")
                if current_hash != ds_info["processed_hash"]:
                    logger.error(f"Processed dataset hash mismatch. Expected: {ds_info['processed_hash'][:16]}, Got: {current_hash[:16] if current_hash else 'N/A'}")
                    all_valid = False

    # Verify metrics
    if "metrics" in artifacts:
        m_info = artifacts["metrics"]
        if "directory_hash" in m_info:
            current_hash = compute_directory_hash(METRICS_DIR)
            if current_hash != m_info["directory_hash"]:
                logger.error(f"Metrics directory hash mismatch.")
                all_valid = False

    # Verify figures
    if "figures" in artifacts:
        f_info = artifacts["figures"]
        if "directory_hash" in f_info:
            current_hash = compute_directory_hash(FIGURES_DIR)
            if current_hash != f_info["directory_hash"]:
                logger.error(f"Figures directory hash mismatch.")
                all_valid = False

    if all_valid:
        logger.info("All artifact hashes verified successfully.")
    else:
        logger.warning("Some artifact hashes do not match.")

    return all_valid


def main():
    """CLI entry point for artifact hash tracking."""
    import argparse
    parser = argparse.ArgumentParser(description="Track artifact hashes in project state.")
    parser.add_argument("--state-file", type=str, default=STATE_FILE_PATH,
                      help="Path to the state YAML file")
    parser.add_argument("--verify", action="store_true",
                      help="Verify integrity of tracked artifacts instead of updating")
    args = parser.parse_args()

    if args.verify:
        success = verify_artifact_integrity(args.state_file)
        sys.exit(0 if success else 1)
    else:
        update_state_with_all_artifacts(args.state_file)
        sys.exit(0)


if __name__ == "__main__":
    main()