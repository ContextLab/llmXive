import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import DATA_METADATA_DIR, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_metadata_dir() -> Path:
    """Ensure the metadata directory exists."""
    ensure_directories()
    metadata_path = Path(DATA_METADATA_DIR)
    metadata_path.mkdir(parents=True, exist_ok=True)
    return metadata_path

def get_algo_version(algo_name: str) -> str:
    """
    Return a version string for the given algorithm.
    In a real pipeline, this might be fetched from a package __version__
    or a git tag. For now, we return a fixed semantic version per algo.
    """
    versions = {
        "harmonic_interp": "1.0.0",
        "wiener_filter": "1.0.0",
        "iterative_synthesis": "1.0.0",
        "custom_likelihood": "1.0.0",
        "mode_coupling": "1.0.0"
    }
    return versions.get(algo_name, "0.0.0")

def record_algorithm_metadata(
    realization_id: str,
    algo_name: str,
    exec_time_sec: float,
    metadata_dir: Optional[Path] = None
) -> Path:
    """
    Record algorithm execution metadata to a JSON file.
    
    Schema requirements:
    - algo_name: str
    - algo_version: str
    - exec_time_sec: float
    - timestamp: str (ISO format)
    
    Args:
        realization_id: Unique identifier for the realization (e.g., "realization_001")
        algo_name: Name of the algorithm used (e.g., "harmonic_interp")
        exec_time_sec: Execution time in seconds
        metadata_dir: Optional override for the metadata directory path.
        
    Returns:
        Path to the created JSON file.
        
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    if not realization_id:
        raise ValueError("realization_id cannot be empty")
    if not algo_name:
        raise ValueError("algo_name cannot be empty")
    if exec_time_sec < 0:
        raise ValueError("exec_time_sec cannot be negative")

    if metadata_dir is None:
        metadata_dir = ensure_metadata_dir()
    else:
        metadata_dir.mkdir(parents=True, exist_ok=True)

    # Construct filename: {realization_id}_algo_{name}.json
    filename = f"{realization_id}_algo_{algo_name}.json"
    file_path = metadata_dir / filename

    algo_version = get_algo_version(algo_name)
    timestamp = datetime.utcnow().isoformat() + "Z"

    metadata = {
        "algo_name": algo_name,
        "algo_version": algo_version,
        "exec_time_sec": exec_time_sec,
        "timestamp": timestamp
    }

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Recorded metadata for {algo_name} on {realization_id} to {file_path}")
    except IOError as e:
        logger.error(f"Failed to write metadata file {file_path}: {e}")
        raise

    return file_path

def load_algorithm_metadata(
    realization_id: str,
    algo_name: str,
    metadata_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load algorithm metadata from the corresponding JSON file.
    
    Args:
        realization_id: Unique identifier for the realization.
        algo_name: Name of the algorithm.
        metadata_dir: Optional override for the metadata directory path.
        
    Returns:
        Dictionary containing the metadata.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    if metadata_dir is None:
        metadata_dir = Path(DATA_METADATA_DIR)
    
    filename = f"{realization_id}_algo_{algo_name}.json"
    file_path = metadata_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Command-line entry point for testing metadata recording.
    Usage: python -m code.analysis.metadata_recorder --realization_id R1 --algo_name harmonic_interp --time 12.5
    """
    import argparse

    parser = argparse.ArgumentParser(description="Record algorithm metadata")
    parser.add_argument("--realization_id", type=str, required=True, help="Realization ID")
    parser.add_argument("--algo_name", type=str, required=True, help="Algorithm name")
    parser.add_argument("--time", type=float, required=True, help="Execution time in seconds")
    
    args = parser.parse_args()

    try:
        path = record_algorithm_metadata(
            realization_id=args.realization_id,
            algo_name=args.algo_name,
            exec_time_sec=args.time
        )
        print(f"Successfully recorded metadata to: {path}")
    except Exception as e:
        print(f"Error recording metadata: {e}")
        raise

if __name__ == "__main__":
    main()