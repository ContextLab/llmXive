"""
Provenance tracking module for llmXive project.
Generates SHA-256 hashes for data artifacts and records source metadata
to satisfy Constitution Principle VI (Habitat Data Provenance).
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
import yaml

from utils.config import get_data_dir, get_metadata_file


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def compute_data_hash(data: Any) -> str:
    """
    Compute SHA-256 hash of arbitrary data (serialized to JSON).

    Args:
        data: Python object to hash (must be JSON serializable).

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()


def generate_provenance_record(
    artifact_path: Union[str, Path],
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    extraction_date: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a provenance record for a data artifact.

    Args:
        artifact_path: Path to the artifact file.
        source_url: URL where the data was sourced from.
        version: Version string of the dataset.
        extraction_date: Date the data was extracted (ISO format).
        description: Optional description of the artifact.

    Returns:
        Dictionary containing the provenance record.
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    file_hash = compute_file_hash(artifact_path)
    file_size = artifact_path.stat().st_size
    relative_path = str(artifact_path.relative_to(get_data_dir()))

    record = {
        "artifact_path": relative_path,
        "sha256_hash": file_hash,
        "file_size_bytes": file_size,
        "generated_at": datetime.utcnow().isoformat(),
        "source_info": {
            "url": source_url,
            "version": version,
            "extraction_date": extraction_date or datetime.utcnow().isoformat(),
            "description": description
        }
    }
    return record


def load_metadata_config() -> Dict[str, Any]:
    """
    Load the metadata.yaml configuration file.
    Creates an empty structure if the file does not exist.

    Returns:
        Dictionary containing the metadata configuration.
    """
    metadata_path = get_metadata_file()
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {
        "datasets": {},
        "artifacts": {},
        "pipeline_runs": []
    }


def save_metadata_config(metadata: Dict[str, Any]) -> None:
    """
    Save the metadata configuration to data/metadata.yaml.

    Args:
        metadata: Dictionary to save.
    """
    metadata_path = get_metadata_file()
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)


def save_provenance_record(record: Dict[str, Any]) -> None:
    """
    Append a provenance record to the metadata.yaml file.

    Args:
        record: The provenance record dictionary to save.
    """
    metadata = load_metadata_config()
    artifact_path = record.get("artifact_path")
    if not artifact_path:
        raise ValueError("Provenance record must contain 'artifact_path'")

    # Initialize sections if missing
    if "artifacts" not in metadata:
        metadata["artifacts"] = {}

    # Update or add the record
    metadata["artifacts"][artifact_path] = record
    save_metadata_config(metadata)


def record_source_info(
    dataset_name: str,
    source_url: str,
    version: str,
    extraction_date: str,
    description: Optional[str] = None
) -> None:
    """
    Record source information for a dataset in metadata.yaml.

    Args:
        dataset_name: Name of the dataset.
        source_url: URL where the data was sourced from.
        version: Version string of the dataset.
        extraction_date: Date the data was extracted.
        description: Optional description.
    """
    metadata = load_metadata_config()
    if "datasets" not in metadata:
        metadata["datasets"] = {}

    metadata["datasets"][dataset_name] = {
        "source_url": source_url,
        "version": version,
        "extraction_date": extraction_date,
        "description": description,
        "recorded_at": datetime.utcnow().isoformat()
    }
    save_metadata_config(metadata)


def log_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a pipeline step execution to metadata.yaml.

    Args:
        step_name: Name of the pipeline step.
        status: Status of the step (e.g., 'success', 'failed').
        details: Optional dictionary of additional details.
    """
    metadata = load_metadata_config()
    if "pipeline_runs" not in metadata:
        metadata["pipeline_runs"] = []

    run_entry = {
        "step_name": step_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    metadata["pipeline_runs"].append(run_entry)
    save_metadata_config(metadata)


def verify_data_integrity(artifact_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify the integrity of a data artifact by comparing its hash.

    Args:
        artifact_path: Path to the artifact.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_file_hash(artifact_path)
    return actual_hash == expected_hash


def load_provenance_records() -> Dict[str, Any]:
    """
    Load all provenance records from metadata.yaml.

    Returns:
        Dictionary of all recorded artifacts and their provenance.
    """
    metadata = load_metadata_config()
    return metadata.get("artifacts", {})


def record_artifact_provenance(
    artifact_path: Union[str, Path],
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    extraction_date: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate and save a provenance record in one step.

    Args:
        artifact_path: Path to the artifact.
        source_url: Source URL.
        version: Dataset version.
        extraction_date: Date extracted.
        description: Optional description.

    Returns:
        The generated provenance record.
    """
    record = generate_provenance_record(
        artifact_path, source_url, version, extraction_date, description
    )
    save_provenance_record(record)
    return record


def main() -> None:
    """
    Main entry point for the provenance module.
    Scans the data directory for artifacts and records their provenance
    if not already recorded, or updates existing records.
    """
    data_dir = get_data_dir()
    if not data_dir.exists():
        print(f"Data directory does not exist: {data_dir}")
        return

    # Example: Record provenance for a hypothetical downloaded file
    # This is a placeholder for the actual logic that would be called
    # by download scripts (T036, T037, T008a) after they save files.
    print("Provenance module loaded. Use record_artifact_provenance() to register files.")
    print(f"Metadata file location: {get_metadata_file()}")


if __name__ == "__main__":
    main()
