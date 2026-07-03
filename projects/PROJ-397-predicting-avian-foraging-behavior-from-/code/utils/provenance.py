"""
Provenance utilities for the llmXive automated science pipeline.

This module provides functionality for:
- Generating deterministic hashes for data files
- Logging metadata for reproducibility
- Tracking pipeline execution context
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import get_project_root, get_output_dir


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute a cryptographic hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string representation of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_data_hash(data: Any) -> str:
    """
    Compute a deterministic hash of Python data structures.

    Args:
        data: Any Python object (dict, list, etc.).

    Returns:
        Hexadecimal string representation of the hash.
    """
    # Serialize with sorted keys for determinism
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_provenance_record(
    input_files: Optional[list[str]] = None,
    output_files: Optional[list[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    script_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive provenance record for a pipeline step.

    Args:
        input_files: List of input file paths.
        output_files: List of output file paths.
        parameters: Dictionary of parameters used in the step.
        script_name: Name of the script generating this record.

    Returns:
        Dictionary containing the provenance record.
    """
    project_root = get_project_root()
    timestamp = datetime.utcnow().isoformat() + "Z"

    record = {
        "timestamp": timestamp,
        "script": script_name or "unknown",
        "project_root": str(project_root),
        "inputs": [],
        "outputs": [],
        "parameters": parameters or {},
    }

    # Process input files with hashes
    if input_files:
        for f in input_files:
            file_path = Path(f)
            if file_path.exists():
                record["inputs"].append({
                    "path": str(file_path),
                    "hash": compute_file_hash(file_path),
                    "size_bytes": file_path.stat().st_size,
                })
            else:
                record["inputs"].append({
                    "path": str(file_path),
                    "status": "missing",
                })

    # Process output files with hashes
    if output_files:
        for f in output_files:
            file_path = Path(f)
            if file_path.exists():
                record["outputs"].append({
                    "path": str(file_path),
                    "hash": compute_file_hash(file_path),
                    "size_bytes": file_path.stat().st_size,
                })
            else:
                record["outputs"].append({
                    "path": str(file_path),
                    "status": "pending",
                })

    return record


def save_provenance_record(
    record: Dict[str, Any],
    output_dir: Optional[Union[str, Path]] = None,
    filename: Optional[str] = None,
) -> Path:
    """
    Save a provenance record to a JSON file.

    Args:
        record: The provenance record dictionary.
        output_dir: Directory to save the record (default: project's provenance dir).
        filename: Name of the file (default: auto-generated based on timestamp).

    Returns:
        Path to the saved file.
    """
    if output_dir is None:
        output_dir = get_output_dir() / "provenance"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"provenance_{timestamp}.json"

    file_path = output_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)

    return file_path


def log_step(
    script_name: str,
    input_files: list[str],
    output_files: list[str],
    parameters: Dict[str, Any],
    status: str = "success",
    error_message: Optional[str] = None,
) -> Path:
    """
    Convenience function to generate and save a provenance record for a pipeline step.

    Args:
        script_name: Name of the script.
        input_files: List of input file paths.
        output_files: List of output file paths.
        parameters: Dictionary of parameters.
        status: Execution status ("success", "failed", "partial").
        error_message: Optional error message if status is "failed".

    Returns:
        Path to the saved provenance record.
    """
    record = generate_provenance_record(
        input_files=input_files,
        output_files=output_files,
        parameters=parameters,
        script_name=script_name,
    )
    record["status"] = status
    if error_message:
        record["error"] = error_message

    return save_provenance_record(record)


def verify_data_integrity(
    file_path: Union[str, Path],
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Verify that a file's hash matches an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected hash value.
        algorithm: Hash algorithm to use.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash
