"""
Provenance management for the plant phenology pipeline.

This module handles the creation, initialization, and updating of the
data provenance record (data/provenance.yaml). It ensures that all data
ingestion steps are logged with their source endpoints, checksums, and
processing parameters to maintain reproducibility.
"""
import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import utility functions from the existing API surface
from src.lib.utils import ensure_dir, compute_file_hash, get_provenance_metadata


PROVENANCE_FILE_PATH = "data/provenance.yaml"


def _load_provenance() -> Dict[str, Any]:
    """
    Load the existing provenance file or return a fresh skeleton if it doesn't exist.
    """
    path = Path(PROVENANCE_FILE_PATH)
    if not path.exists():
        return {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "entries": []
        }

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        # Ensure structure exists if file was corrupted or empty
        if data is None:
            return {
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "entries": []
            }
        if "entries" not in data:
            data["entries"] = []
        return data


def _save_provenance(data: Dict[str, Any]) -> None:
    """
    Save the provenance dictionary to the YAML file.
    """
    path = Path(PROVENANCE_FILE_PATH)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _compute_checksum(filepath: str) -> str:
    """
    Compute the SHA-256 checksum of a file.
    """
    return compute_file_hash(filepath)


def add_provenance_entry(
    source_type: str,
    source_url: str,
    output_path: str,
    processing_params: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add a new entry to the provenance record.

    Args:
        source_type: Type of source (e.g., 'GEE', 'NOAA', 'NatureNotebook').
        source_url: The API endpoint or URL used.
        output_path: Relative path to the generated data file.
        processing_params: Dictionary of parameters used during processing.
        metadata: Additional metadata (e.g., site IDs, date ranges).
    """
    data = _load_provenance()

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_type": source_type,
        "source_url": source_url,
        "output_path": output_path,
        "checksum": None,
        "processing_params": processing_params or {},
        "metadata": metadata or {}
    }

    # Compute checksum if output file exists
    if output_path and os.path.exists(output_path):
        entry["checksum"] = _compute_checksum(output_path)
    else:
        # If file doesn't exist yet, mark as pending or store empty
        entry["checksum"] = "pending"

    data["entries"].append(entry)
    _save_provenance(data)


def initialize_provenance_file() -> None:
    """
    Initialize the provenance file with the schema structure if it does not exist.
    This is the primary entry point for T007.
    """
    path = Path(PROVENANCE_FILE_PATH)
    if not path.exists():
        data = {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "description": "Records API endpoints, checksums, and processing parameters for all data artifacts.",
            "entries": []
        }
        _save_provenance(data)


def update_entry_checksum(output_path: str) -> None:
    """
    Update the checksum for a specific entry if the file has changed.
    This is useful to call after a download completes.
    """
    if not os.path.exists(output_path):
        return

    checksum = _compute_checksum(output_path)
    data = _load_provenance()

    # Find the entry with the matching output_path
    for entry in data["entries"]:
        if entry.get("output_path") == output_path:
            entry["checksum"] = checksum
            break

    _save_provenance(data)
