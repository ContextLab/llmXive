"""Hash Manager for Constitution Principle IV (Single Source of Truth).

This module computes SHA256 checksums for all data artifacts and updates
the project state file to maintain a verified record of data integrity.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_artifact_paths(data_dir: Path) -> List[Path]:
    """Get list of artifact paths to hash.

    Specifically targets:
    - graphs_v1.parquet
    - split_indices.json
    - model_v1.pt
    - All files in data/results/

    Args:
        data_dir: Root data directory.

    Returns:
        List of Path objects for artifacts to hash.
    """
    artifacts = []

    # Specific files in data/processed/
    processed_dir = data_dir / "processed"
    specific_files = ["graphs_v1.parquet", "split_indices.json", "model_v1.pt"]
    if processed_dir.exists():
        for filename in specific_files:
            file_path = processed_dir / filename
            if file_path.exists():
                artifacts.append(file_path)

    # All files in data/results/
    results_dir = data_dir / "results"
    if results_dir.exists():
        for file_path in results_dir.rglob("*"):
            if file_path.is_file():
                artifacts.append(file_path)

    return artifacts


def update_state_file(state_path: Path, artifact_hashes: Dict[str, str]) -> None:
    """Update the project state file with new artifact hashes.

    Args:
        state_path: Path to the state YAML file.
        artifact_hashes: Dictionary mapping file paths to SHA256 checksums.
    """
    # Load existing state or create new structure
    if state_path.exists():
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Update artifact_hashes
    state["artifact_hashes"] = artifact_hashes

    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Write updated state
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def run_hash_audit(
    data_dir: Path,
    state_path: Path,
    verbose: bool = True,
) -> Dict[str, str]:
    """Run the full hash audit and update state file.

    Args:
        data_dir: Root data directory to scan.
        state_path: Path to the state YAML file.
        verbose: Whether to print progress.

    Returns:
        Dictionary of artifact paths to their SHA256 hashes.
    """
    artifact_paths = get_artifact_paths(data_dir)

    if not artifact_paths:
        if verbose:
            print("No artifacts found to hash. Ensure data generation tasks have run.")
        return {}

    artifact_hashes = {}
    for path in artifact_paths:
        relative_path = str(path.relative_to(data_dir.parent))
        if verbose:
            print(f"Computing hash for: {relative_path}")
        hash_value = compute_sha256(path)
        artifact_hashes[relative_path] = hash_value

    # Update state file
    update_state_file(state_path, artifact_hashes)

    if verbose:
        print(f"Hash audit complete. {len(artifact_hashes)} artifacts recorded.")
        print(f"State updated at: {state_path}")

    return artifact_hashes


def main() -> None:
    """Main entry point for the hash manager CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute SHA256 checksums for project artifacts and update state."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root data directory (default: data)",
    )
    parser.add_argument(
        "--state-path",
        type=str,
        default="state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml",
        help="Path to the state YAML file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    state_path = Path(args.state_path).resolve()

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return

    run_hash_audit(data_dir, state_path, verbose=not args.quiet)


if __name__ == "__main__":
    main()