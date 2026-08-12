"""
Provenance module for metadata logging and hash generation.

This module provides utilities to compute file and data hashes,
generate provenance records with timestamps and execution context,
and verify data integrity across pipeline steps.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from utils.config import get_project_root


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hash_obj = hashlib.new(algorithm)

    # Read file in chunks to handle large files
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def compute_data_hash(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute the hash of arbitrary data (dict, list, string, etc.).

    Args:
        data: Data to hash. Must be JSON-serializable.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the data hash.
    """
    # Serialize data to JSON with sorted keys for deterministic output
    json_str = json.dumps(data, sort_keys=True, default=str)
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(json_str.encode("utf-8"))
    return hash_obj.hexdigest()


def generate_provenance_record(
    step_name: str,
    input_files: Optional[list] = None,
    output_files: Optional[list] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a provenance record for a pipeline step.

    Args:
        step_name: Name of the pipeline step.
        input_files: List of input file paths.
        output_files: List of output file paths.
        parameters: Dictionary of parameters used in the step.
        metadata: Additional metadata (e.g., user, environment).

    Returns:
        Dictionary containing the provenance record.
    """
    project_root = get_project_root()

    # Resolve paths relative to project root
    resolved_inputs = [str(Path(f).relative_to(project_root)) if Path(f).is_absolute() else str(f) for f in (input_files or [])]
    resolved_outputs = [str(Path(f).relative_to(project_root)) if Path(f).is_absolute() else str(f) for f in (output_files or [])]

    # Compute hashes for input and output files if they exist
    input_hashes = {}
    for f in resolved_inputs:
        full_path = project_root / f
        if full_path.exists():
            input_hashes[f] = compute_file_hash(full_path)

    output_hashes = {}
    for f in resolved_outputs:
        full_path = project_root / f
        if full_path.exists():
            output_hashes[f] = compute_file_hash(full_path)

    record = {
        "step_name": step_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_files": resolved_inputs,
        "input_hashes": input_hashes,
        "output_files": resolved_outputs,
        "output_hashes": output_hashes,
        "parameters": parameters or {},
        "metadata": metadata or {},
        "project_root": str(project_root)
    }

    return record


def save_provenance_record(record: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Save a provenance record to a JSON file.

    Args:
        record: The provenance record dictionary.
        output_path: Path to save the record.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)


def log_step(
    step_name: str,
    input_files: Optional[list] = None,
    output_files: Optional[list] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    log_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Generate and save a provenance record for a pipeline step.

    Args:
        step_name: Name of the pipeline step.
        input_files: List of input file paths.
        output_files: List of output file paths.
        parameters: Dictionary of parameters used in the step.
        metadata: Additional metadata.
        log_dir: Directory to save the log file. Defaults to project_root/logs/provenance.

    Returns:
        The generated provenance record.
    """
    record = generate_provenance_record(
        step_name=step_name,
        input_files=input_files,
        output_files=output_files,
        parameters=parameters,
        metadata=metadata
    )

    if log_dir is None:
        project_root = get_project_root()
        log_dir = project_root / "logs" / "provenance"
    else:
        log_dir = Path(log_dir)

    # Generate filename based on timestamp and step name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{step_name.replace(' ', '_')}.json"
    output_path = log_dir / filename

    save_provenance_record(record, output_path)

    return record


def verify_data_integrity(
    file_path: Union[str, Path],
    expected_hash: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify the integrity of a file by comparing its hash to an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected hash value.
        algorithm: Hash algorithm to use.

    Returns:
        True if the hash matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash