"""
Metadata Recorder Module for User Story 2 (T023).

Records algorithm name, version, execution time, and timestamp for each
gap-filling algorithm application.
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import DATA_METADATA_DIR


def ensure_metadata_dir():
    """Ensure the metadata output directory exists."""
    if not DATA_METADATA_DIR.exists():
        DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_METADATA_DIR


def get_algo_version(algo_name: str) -> str:
    """
    Return a fixed version string for known algorithms.
    In a real pipeline, this might read from a package __version__ or git hash.
    """
    versions = {
        "harmonic_interp": "1.0.0",
        "wiener_filter": "1.0.0",
        "iterative_synthesis": "1.0.0",
    }
    return versions.get(algo_name, "unknown")


def record_algorithm_metadata(
    realization_id: str,
    algo_name: str,
    exec_time_sec: float,
    output_dir: Optional[Path] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Record algorithm execution metadata to a JSON file.

    The output file is named: {realization_id}_algo_{algo_name}.json
    The JSON schema includes:
      - algo_name: str
      - algo_version: str
      - exec_time_sec: float
      - timestamp: str (ISO format)
      - (optional) extra fields from extra_metadata

    Args:
        realization_id: Unique identifier for the CMB realization.
        algo_name: Name of the gap-filling algorithm used.
        exec_time_sec: Execution time in seconds.
        output_dir: Directory to write the metadata file. Defaults to DATA_METADATA_DIR.
        extra_metadata: Optional dictionary of additional key-value pairs to store.

    Returns:
        Path to the created metadata file.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    if not realization_id:
        raise ValueError("realization_id must be a non-empty string.")
    if not algo_name:
        raise ValueError("algo_name must be a non-empty string.")
    if exec_time_sec < 0:
        raise ValueError("exec_time_sec must be non-negative.")

    output_dir = output_dir or ensure_metadata_dir()

    filename = f"{realization_id}_algo_{algo_name}.json"
    file_path = output_dir / filename

    metadata = {
        "algo_name": algo_name,
        "algo_version": get_algo_version(algo_name),
        "exec_time_sec": exec_time_sec,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if extra_metadata:
        metadata.update(extra_metadata)

    # Write the JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return file_path


def main():
    """
    CLI entry point for testing the metadata recorder.
    Usage: python -m code.analysis.metadata_recorder <realization_id> <algo_name> <exec_time>
    """
    import sys

    if len(sys.argv) < 4:
        print(
            "Usage: python -m code.analysis.metadata_recorder <realization_id> <algo_name> <exec_time_sec>"
        )
        sys.exit(1)

    realization_id = sys.argv[1]
    algo_name = sys.argv[2]
    try:
        exec_time_sec = float(sys.argv[3])
    except ValueError:
        print(f"Error: exec_time_sec must be a number, got '{sys.argv[3]}'")
        sys.exit(1)

    try:
        file_path = record_algorithm_metadata(
            realization_id=realization_id,
            algo_name=algo_name,
            exec_time_sec=exec_time_sec,
        )
        print(f"Metadata recorded to: {file_path}")
    except Exception as e:
        print(f"Error recording metadata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()