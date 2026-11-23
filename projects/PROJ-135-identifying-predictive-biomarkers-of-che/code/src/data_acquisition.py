import os
import sys
import json
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import get_project_root, ensure_directories
from .utils import calculate_checksum, setup_logging

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal checksum string.
    """
    return calculate_checksum(file_path, algorithm)

def write_checksum_to_state(
    file_path: str, state_file: str, key: str, algorithm: str = "sha256"
) -> None:
    """
    Write a file's checksum to the project state file.

    Args:
        file_path: Path to the file.
        state_file: Path to the state YAML file.
        key: Key under which to store the checksum.
        algorithm: Hash algorithm to use.
    """
    import yaml

    checksum = compute_file_checksum(file_path, algorithm)

    # Load existing state or create new
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Update checksum
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    state["artifact_hashes"][key] = checksum

    # Write back
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

    logger.info(f"Wrote checksum for {file_path} to {state_file} under key {key}")

def write_feasibility_gate_result(
    result: Dict[str, Any], output_file: str
) -> None:
    """
    Write the feasibility gate result to a JSON file.

    Args:
        result: Dictionary containing the feasibility result.
        output_file: Path to the output JSON file.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Wrote feasibility gate result to {output_file}")

def fetch_geo_dataset(
    geo_id: str, output_dir: str, timeout: int = 300
) -> Path:
    """
    Fetch a GEO dataset using GEOquery (via R subprocess).

    Args:
        geo_id: GEO accession ID (e.g., 'GSE25055').
        output_dir: Directory to save the data.
        timeout: Timeout in seconds for the R script.

    Returns:
        Path to the downloaded file.

    Raises:
        RuntimeError: If the download fails.
    """
    import subprocess

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Path to the R script
    r_script_path = Path(get_project_root()) / "code" / "src" / "scripts" / "run_geo_download.R"

    if not r_script_path.exists():
        raise FileNotFoundError(f"GEO download script not found: {r_script_path}")

    output_file = output_dir_path / f"{geo_id}_data.rds"

    # Construct R command
    cmd = [
        "Rscript",
        str(r_script_path),
        geo_id,
        str(output_file),
    ]

    try:
        logger.info(f"Fetching GEO dataset {geo_id}...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
        logger.info(result.stdout)

        if not output_file.exists():
            raise RuntimeError(f"R script completed but output file not found: {output_file}")

        return output_file

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout fetching GEO dataset {geo_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching GEO dataset {geo_id}: {e.stderr}")
        raise RuntimeError(f"Failed to fetch GEO dataset {geo_id}: {e.stderr}")

def parse_geo_samples(data_file: Path) -> List[Dict[str, Any]]:
    """
    Parse samples from a GEO dataset file.

    Args:
        data_file: Path to the GEO data file.

    Returns:
        List of sample dictionaries.
    """
    # This is a placeholder; actual implementation depends on the data format
    # For now, return an empty list
    logger.warning("parse_geo_samples is a placeholder; actual parsing depends on data format")
    return []

def get_valid_geo_count(geo_ids: List[str], data_dir: str) -> int:
    """
    Count how many GEO datasets are valid (have response annotations).

    Args:
        geo_ids: List of GEO accession IDs.
        data_dir: Directory containing the downloaded data.

    Returns:
        Count of valid datasets.
    """
    valid_count = 0
    for geo_id in geo_ids:
        data_file = Path(data_dir) / f"{geo_id}_data.rds"
        if data_file.exists():
            # Check if the dataset has response annotations
            # This is a simplified check; actual implementation depends on data format
            samples = parse_geo_samples(data_file)
            if any("response" in sample for sample in samples):
                valid_count += 1

    return valid_count

def check_feasibility_gate(
    tcga_types: List[str], geo_datasets: List[str], test_mode: bool = False
) -> bool:
    """
    Check if the data feasibility gate is passed.

    Args:
        tcga_types: List of available TCGA tumor types.
        geo_datasets: List of available GEO datasets.
        test_mode: If True, allow fewer datasets for testing.

    Returns:
        True if the gate is passed, False otherwise.
    """
    if test_mode:
        logger.info("Test mode: skipping strict feasibility check")
        return True

    # Check TCGA types
    if len(tcga_types) < 3:
        logger.error(f"Insufficient TCGA types: {len(tcga_types)} < 3")
        return False

    # Check GEO datasets
    if len(geo_datasets) < 2:
        logger.error(f"Insufficient GEO datasets: {len(geo_datasets)} < 2")
        return False

    logger.info("Feasibility gate passed")
    return True

def main():
    """Main entry point for data acquisition module."""
    import argparse

    parser = argparse.ArgumentParser(description="Data Acquisition Module")
    parser.add_argument("--mode", choices=["real", "test"], default="test")
    parser.add_argument("--subset-size", type=int, default=100)
    args = parser.parse_args()

    setup_logging(level=logging.INFO)

    project_root = get_project_root()
    data_dir = str(Path(project_root) / "code" / "data" / "raw")

    # Example: Fetch a GEO dataset
    if args.mode == "real":
        try:
            geo_id = "GSE25055"  # Example ID
            fetch_geo_dataset(geo_id, data_dir)
        except Exception as e:
            logger.error(f"Data acquisition failed: {e}")
            sys.exit(1)
    else:
        logger.info("Test mode: skipping real data acquisition")

if __name__ == "__main__":
    main()