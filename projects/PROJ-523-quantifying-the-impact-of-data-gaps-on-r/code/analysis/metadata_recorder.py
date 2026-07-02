"""
Metadata Recorder for Gap-Filling Algorithms (T023)

Implements logic to record algorithm name, version, execution time, and timestamp
for each gap-filling algorithm run. Output is stored in data/metadata/
with the naming convention: {realization_id}_algo_{name}.json

Schema keys required:
- algo_name
- algo_version
- exec_time_sec
- timestamp
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import project constants
try:
    from code.config import DATA_METADATA_DIR
except ImportError:
    # Fallback if code/config.py is not in PYTHONPATH but file exists
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from code.config import DATA_METADATA_DIR


def ensure_metadata_dir():
    """Ensure the metadata directory exists."""
    Path(DATA_METADATA_DIR).mkdir(parents=True, exist_ok=True)


def record_algorithm_metadata(
    realization_id: str,
    algo_name: str,
    algo_version: str,
    exec_time_sec: float,
    timestamp: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Record algorithm execution metadata to a JSON file.

    Args:
        realization_id: Unique identifier for the CMB realization
        algo_name: Name of the gap-filling algorithm (e.g., 'harmonic_interp')
        algo_version: Version string of the algorithm
        exec_time_sec: Execution time in seconds
        timestamp: ISO format timestamp (defaults to current time if None)
        additional_info: Optional dictionary of extra metadata

    Returns:
        Path to the created metadata file
    """
    ensure_metadata_dir()

    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"

    # Construct metadata dictionary per schema requirements
    metadata = {
        "algo_name": algo_name,
        "algo_version": algo_version,
        "exec_time_sec": round(exec_time_sec, 4),
        "timestamp": timestamp
    }

    # Add additional info if provided
    if additional_info:
        metadata.update(additional_info)

    # Construct filename
    filename = f"{realization_id}_algo_{algo_name}.json"
    filepath = Path(DATA_METADATA_DIR) / filename

    # Write metadata to file
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)

    return filepath


def get_algo_version(algo_module_name: str) -> str:
    """
    Attempt to retrieve version string from an algorithm module.
    Falls back to 'unknown' if version cannot be determined.

    Args:
        algo_module_name: Name of the algorithm module (e.g., 'harmonic_interp')

    Returns:
        Version string
    """
    try:
        # Import the module dynamically
        module = __import__(f'code.gap_filling.{algo_module_name}', fromlist=[''])
        # Try common version attributes
        if hasattr(module, '__version__'):
            return module.__version__
        elif hasattr(module, 'VERSION'):
            return module.VERSION
        else:
            return 'unknown'
    except (ImportError, AttributeError):
        return 'unknown'


def main():
    """
    Example usage for testing the metadata recorder.
    This function demonstrates recording metadata for all three algorithms.
    """
    import logging
    logging.basicConfig(level=logging.INFO)

    # Example: Record metadata for a test realization
    test_realization_id = "test_real_001"
    algorithms = [
        ("harmonic_interp", "harmonic_interp"),
        ("wiener_filter", "wiener_filter"),
        ("iterative_synthesis", "iterative_synthesis")
    ]

    for algo_name, module_name in algorithms:
        # Simulate execution time
        start_time = time.time()
        time.sleep(0.01)  # Small delay to simulate work
        exec_time = time.time() - start_time

        # Get version
        version = get_algo_version(module_name)

        # Record metadata
        filepath = record_algorithm_metadata(
            realization_id=test_realization_id,
            algo_name=algo_name,
            algo_version=version,
            exec_time_sec=exec_time,
            additional_info={"test_run": True}
        )

        logging.info(f"Recorded metadata for {algo_name} -> {filepath}")

    print("Metadata recording example completed.")


if __name__ == "__main__":
    main()