"""
Provenance tracking module for the plant phenology prediction pipeline.

This module provides functionality to:
- Initialize and manage the provenance.yaml file
- Add new entries for data sources and processing steps
- Update checksums for processed files
- Validate the provenance schema
"""

import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import get_config
from src.lib.utils import setup_logging

# Constants
PROVENANCE_FILE_PATH = Path("data/provenance.yaml")
PROVENANCE_VERSION = "1.0.0"

# Logger setup
logger = setup_logging(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def initialize_provenance_file() -> None:
    """
    Initialize the provenance.yaml file with the default schema.
    
    Creates the file with standard metadata, empty data sources,
    and empty processing steps if it doesn't exist.
    """
    config = get_config()
    
    # Ensure data directory exists
    PROVENANCE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if PROVENANCE_FILE_PATH.exists():
        logger.info(f"Provenance file already exists at {PROVENANCE_FILE_PATH}")
        return
    
    provenance_data = {
        "version": PROVENANCE_VERSION,
        "project_id": config.project_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "processing_params": {
            "software_version": config.software_version,
            "python_version": f"{config.python_major}.{config.python_minor}",
            "random_seed": config.random_seed,
            "cloud_coverage_threshold": config.cloud_coverage_threshold,
            "spatial_resolution": "10m",
            "temporal_resolution": "10-day"
        },
        "data_sources": [],
        "processing_steps": [],
        "execution_log": [],
        "metadata": {
            "git_commit": "unknown",
            "environment": "development",
            "notes": "Initial provenance file created"
        }
    }
    
    with open(PROVENANCE_FILE_PATH, "w") as f:
        yaml.dump(provenance_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Initialized provenance file at {PROVENANCE_FILE_PATH}")


def load_provenance() -> Dict[str, Any]:
    """
    Load the provenance file.
    
    Returns:
        Dictionary containing the provenance data
        
    Raises:
        FileNotFoundError: If the provenance file doesn't exist
    """
    if not PROVENANCE_FILE_PATH.exists():
        raise FileNotFoundError(f"Provenance file not found at {PROVENANCE_FILE_PATH}")
    
    with open(PROVENANCE_FILE_PATH, "r") as f:
        return yaml.safe_load(f)


def save_provenance(data: Dict[str, Any]) -> None:
    """
    Save the provenance data to file.
    
    Args:
        data: Dictionary containing the provenance data to save
    """
    data["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    with open(PROVENANCE_FILE_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logger.debug(f"Saved provenance data to {PROVENANCE_FILE_PATH}")


def add_data_source(
    name: str,
    data_type: str,
    provider: str,
    endpoint: str,
    date_range: Dict[str, str],
    variables: Optional[List[str]] = None,
    bands: Optional[List[str]] = None,
    processing_level: Optional[str] = None,
    species: Optional[List[str]] = None,
    events: Optional[List[str]] = None
) -> None:
    """
    Add a new data source entry to the provenance file.
    
    Args:
        name: Unique identifier for the data source
        data_type: Type of data (satellite, climate, phenology)
        provider: Name of the data provider
        endpoint: API endpoint or asset path
        date_range: Dictionary with 'start' and 'end' keys
        variables: List of variables/bands (optional)
        bands: List of satellite bands (optional)
        processing_level: Processing level (e.g., L1C, L2A)
        species: List of species (for phenology data)
        events: List of phenological events
    """
    provenance = load_provenance()
    
    # Check if source already exists
    for source in provenance["data_sources"]:
        if source["name"] == name:
            logger.warning(f"Data source '{name}' already exists, updating")
            source["last_accessed"] = datetime.utcnow().isoformat() + "Z"
            save_provenance(provenance)
            return
    
    source_entry = {
        "name": name,
        "type": data_type,
        "provider": provider,
        "endpoint": endpoint,
        "date_range": date_range,
        "checksums": {},
        "status": "pending",
        "last_accessed": None
    }
    
    # Add optional fields
    if variables:
        source_entry["variables"] = variables
    if bands:
        source_entry["bands"] = bands
    if processing_level:
        source_entry["processing_level"] = processing_level
    if species:
        source_entry["species"] = species
    if events:
        source_entry["events"] = events
    
    provenance["data_sources"].append(source_entry)
    save_provenance(provenance)
    logger.info(f"Added data source '{name}' to provenance")


def add_processing_step(
    step_id: str,
    name: str,
    description: str,
    script: str,
    parameters: Dict[str, Any],
    outputs: List[str]
) -> None:
    """
    Add a new processing step entry to the provenance file.
    
    Args:
        step_id: Unique identifier for the step
        name: Name of the processing step
        description: Description of what the step does
        script: Path to the script that performs the step
        parameters: Dictionary of parameters used
        outputs: List of output file paths
    """
    provenance = load_provenance()
    
    # Check if step already exists
    for step in provenance["processing_steps"]:
        if step["id"] == step_id:
            logger.warning(f"Processing step '{step_id}' already exists, updating")
            return
    
    step_entry = {
        "id": step_id,
        "name": name,
        "description": description,
        "script": script,
        "parameters": parameters,
        "outputs": outputs,
        "checksums": {},
        "status": "pending",
        "executed_at": None
    }
    
    provenance["processing_steps"].append(step_entry)
    save_provenance(provenance)
    logger.info(f"Added processing step '{step_id}' to provenance")


def update_source_checksum(source_name: str, file_path: str, checksum: str) -> None:
    """
    Update the checksum for a specific data source file.
    
    Args:
        source_name: Name of the data source
        file_path: Path to the file
        checksum: Checksum value to record
    """
    provenance = load_provenance()
    
    for source in provenance["data_sources"]:
        if source["name"] == source_name:
            source["checksums"][file_path] = checksum
            source["status"] = "completed"
            source["last_accessed"] = datetime.utcnow().isoformat() + "Z"
            save_provenance(provenance)
            logger.debug(f"Updated checksum for source '{source_name}' file '{file_path}'")
            return
    
    logger.warning(f"Data source '{source_name}' not found in provenance")


def update_step_checksum(step_id: str, file_path: str, checksum: str) -> None:
    """
    Update the checksum for a specific processing step output.
    
    Args:
        step_id: ID of the processing step
        file_path: Path to the output file
        checksum: Checksum value to record
    """
    provenance = load_provenance()
    
    for step in provenance["processing_steps"]:
        if step["id"] == step_id:
            step["checksums"][file_path] = checksum
            save_provenance(provenance)
            logger.debug(f"Updated checksum for step '{step_id}' file '{file_path}'")
            return
    
    logger.warning(f"Processing step '{step_id}' not found in provenance")


def mark_step_executed(step_id: str) -> None:
    """
    Mark a processing step as executed.
    
    Args:
        step_id: ID of the processing step
    """
    provenance = load_provenance()
    
    for step in provenance["processing_steps"]:
        if step["id"] == step_id:
            step["status"] = "completed"
            step["executed_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Log execution
            log_entry = {
                "step_id": step_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": "executed"
            }
            provenance["execution_log"].append(log_entry)
            
            save_provenance(provenance)
            logger.info(f"Marked step '{step_id}' as executed")
            return
    
    logger.warning(f"Processing step '{step_id}' not found in provenance")


def add_provenance_entry(
    entry_type: str,
    entry_id: str,
    details: Dict[str, Any]
) -> None:
    """
    Add a generic provenance entry.
    
    Args:
        entry_type: Type of entry (e.g., 'data_source', 'processing_step')
        entry_id: Unique identifier for the entry
        details: Dictionary of additional details
    """
    provenance = load_provenance()
    
    entry = {
        "type": entry_type,
        "id": entry_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": details
    }
    
    if "entries" not in provenance:
        provenance["entries"] = []
    
    provenance["entries"].append(entry)
    save_provenance(provenance)
    logger.info(f"Added generic provenance entry: {entry_type}/{entry_id}")

# For backward compatibility with existing code
def update_entry_checksum(entry_type: str, entry_id: str, file_path: str, checksum: str) -> None:
    """
    Update checksum for a generic entry.
    
    Args:
        entry_type: Type of entry
        entry_id: ID of the entry
        file_path: Path to the file
        checksum: Checksum value
    """
    if entry_type == "data_source":
        update_source_checksum(entry_id, file_path, checksum)
    elif entry_type == "processing_step":
        update_step_checksum(entry_id, file_path, checksum)
    else:
        logger.warning(f"Unknown entry type: {entry_type}")
