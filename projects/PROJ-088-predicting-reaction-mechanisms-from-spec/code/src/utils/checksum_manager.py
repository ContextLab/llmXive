import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from .io import calculate_file_checksum, read_json_file, write_json_file, ensure_directory_exists
from .logging import log_info, log_error, log_warning

def update_artifact_checksum(
    file_path: str,
    checksums_file: str = "data/checksums.json",
    state_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Calculate SHA-256 checksum for a file and update the checksums registry.
    Optionally updates the project state file's artifact_hashes map.

    Args:
        file_path: Path to the file to checksum.
        checksums_file: Path to the JSON file storing all checksums.
        state_file: Optional path to the project state YAML file.

    Returns:
        Dictionary containing the file path and its checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        log_error(f"Checksum calculation failed: File not found - {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.stat().st_size == 0:
        log_warning(f"File is empty, checksum might not be meaningful: {file_path}")

    checksum = calculate_file_checksum(str(path))
    
    if checksum is None:
        log_error(f"Failed to calculate checksum for {file_path}")
        raise ValueError(f"Could not calculate checksum for {file_path}")

    log_info(f"Calculated checksum for {file_path}: {checksum}")

    # Load existing checksums
    checksums_data = {}
    if Path(checksums_file).exists():
        checksums_data = read_json_file(checksums_file)

    # Update or add the checksum
    checksums_data[file_path] = checksum
    write_json_file(checksums_file, checksums_data)
    log_info(f"Updated checksums registry at {checksums_file}")

    # Update state file if provided
    if state_file:
        _update_state_file(state_file, file_path, checksum)

    return {"path": file_path, "checksum": checksum}


def calculate_batch_checksums(
    file_paths: List[str],
    checksums_file: str = "data/checksums.json",
    state_file: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Calculate checksums for multiple files and update registries.

    Args:
        file_paths: List of file paths to checksum.
        checksums_file: Path to the JSON file storing all checksums.
        state_file: Optional path to the project state YAML file.

    Returns:
        List of dictionaries containing path and checksum.
    """
    results = []
    for f_path in file_paths:
        try:
            res = update_artifact_checksum(f_path, checksums_file, state_file)
            results.append(res)
        except Exception as e:
            log_error(f"Skipping {f_path} due to error: {str(e)}")
            continue
    return results


def _update_state_file(state_file: str, artifact_path: str, checksum: str) -> None:
    """
    Updates the artifact_hashes map in the project state YAML file.
    """
    state_path = Path(state_file)
    if not state_path.exists():
        log_warning(f"State file not found, creating new one: {state_file}")
        state_data = {
            "project_id": "PROJ-088-predicting-reaction-mechanisms-from-spec",
            "artifact_hashes": {}
        }
    else:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        if state_data is None:
            state_data = {"artifact_hashes": {}}
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][artifact_path] = checksum
    
    ensure_directory_exists(str(state_path.parent))
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    log_info(f"Updated state file at {state_file} with checksum for {artifact_path}")
