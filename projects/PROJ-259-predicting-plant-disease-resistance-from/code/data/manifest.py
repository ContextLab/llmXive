"""
Data manifest schema and loader for the plant disease resistance project.

This module defines the structure of data/data_manifest.yaml and provides
functions to load and validate the manifest.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_path
from utils.logging import get_logger

logger = get_logger(__name__)

# Expected schema for data_manifest.yaml
MANIFEST_SCHEMA = {
    "version": str,
    "source_type": str,  # 'REAL', 'SIMULATED', or 'HYBRID'
    "datasets": list,
}

DATASET_SCHEMA = {
    "dataset_id": str,
    "source": str,
    "accession": Optional[str],
    "modality": str,  # 'SNP', 'metabolite', 'phenotype', etc.
    "file_path": str,
    "status": str,  # 'pending', 'downloaded', 'processed'
    "checksum": Optional[str],
    "metadata": Optional[dict],
}

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate the data manifest from YAML file.
    
    Args:
        manifest_path: Path to the manifest file. If None, uses default path
                       from config (data/data_manifest.yaml).
    
    Returns:
        Dict containing the parsed manifest data.
    
    Raises:
        FileNotFoundError: If manifest file does not exist.
        ValueError: If manifest schema is invalid.
    """
    if manifest_path is None:
        manifest_path = get_path("data", "data_manifest.yaml")
    
    if not Path(manifest_path).exists():
        logger.warning(f"Manifest file not found at {manifest_path}. "
                     "Creating default manifest structure.")
        return _create_default_manifest(manifest_path)
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse manifest YAML: {e}")
    
    # Basic schema validation
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a YAML dictionary")
    
    if "version" not in manifest:
        manifest["version"] = "1.0"
    
    if "source_type" not in manifest:
        manifest["source_type"] = "SIMULATED"
        logger.info("Defaulting source_type to SIMULATED")
    
    if "datasets" not in manifest:
        manifest["datasets"] = []
        logger.info("Initializing empty datasets list")
    
    # Validate dataset entries
    for i, dataset in enumerate(manifest["datasets"]):
        if not isinstance(dataset, dict):
            raise ValueError(f"Dataset at index {i} must be a dictionary")
        
        required_fields = ["dataset_id", "source", "modality", "file_path", "status"]
        for field in required_fields:
            if field not in dataset:
                raise ValueError(f"Dataset at index {i} missing required field: {field}")
        
        # Add optional fields with defaults if missing
        if "accession" not in dataset:
            dataset["accession"] = None
        if "checksum" not in dataset:
            dataset["checksum"] = None
        if "metadata" not in dataset:
            dataset["metadata"] = {}
    
    logger.info(f"Loaded manifest with {len(manifest['datasets'])} datasets "
               f"from {manifest_path}")
    return manifest

def _create_default_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Create a default manifest file and return its content.
    
    Args:
        manifest_path: Path where the manifest should be created.
    
    Returns:
        Dict containing the default manifest data.
    """
    default_manifest = {
        "version": "1.0",
        "source_type": "SIMULATED",
        "description": "Data manifest for plant disease resistance prediction pipeline",
        "datasets": []
    }
    
    # Ensure parent directory exists
    Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        yaml.dump(default_manifest, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Created default manifest at {manifest_path}")
    return default_manifest

def save_manifest(manifest: Dict[str, Any], manifest_path: Optional[Path] = None) -> None:
    """
    Save the manifest to a YAML file.
    
    Args:
        manifest: The manifest dictionary to save.
        manifest_path: Path to save the manifest. If None, uses default path.
    """
    if manifest_path is None:
        manifest_path = get_path("data", "data_manifest.yaml")
    
    Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved manifest to {manifest_path}")

def get_dataset_by_id(manifest: Dict[str, Any], dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a dataset entry by its ID.
    
    Args:
        manifest: The loaded manifest dictionary.
        dataset_id: The ID of the dataset to find.
    
    Returns:
        The dataset dictionary if found, None otherwise.
    """
    for dataset in manifest.get("datasets", []):
        if dataset.get("dataset_id") == dataset_id:
            return dataset
    return None

def add_dataset(manifest: Dict[str, Any], dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new dataset entry to the manifest.
    
    Args:
        manifest: The loaded manifest dictionary.
        dataset: The dataset dictionary to add.
    
    Returns:
        The updated manifest dictionary.
    """
    if "datasets" not in manifest:
        manifest["datasets"] = []
    
    # Validate required fields
    required_fields = ["dataset_id", "source", "modality", "file_path", "status"]
    for field in required_fields:
        if field not in dataset:
            raise ValueError(f"Missing required field: {field}")
    
    # Check for duplicate dataset_id
    if get_dataset_by_id(manifest, dataset["dataset_id"]):
        raise ValueError(f"Dataset with ID {dataset['dataset_id']} already exists")
    
    # Add optional fields with defaults
    if "accession" not in dataset:
        dataset["accession"] = None
    if "checksum" not in dataset:
        dataset["checksum"] = None
    if "metadata" not in dataset:
        dataset["metadata"] = {}
    
    manifest["datasets"].append(dataset)
    logger.info(f"Added dataset {dataset['dataset_id']} to manifest")
    return manifest

def update_dataset_status(manifest: Dict[str, Any], dataset_id: str, 
                         new_status: str) -> Dict[str, Any]:
    """
    Update the status of a dataset in the manifest.
    
    Args:
        manifest: The loaded manifest dictionary.
        dataset_id: The ID of the dataset to update.
        new_status: The new status value.
    
    Returns:
        The updated manifest dictionary.
    
    Raises:
        ValueError: If dataset_id not found or invalid status.
    """
    valid_statuses = ["pending", "downloaded", "processed", "failed"]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
    
    for dataset in manifest.get("datasets", []):
        if dataset.get("dataset_id") == dataset_id:
            dataset["status"] = new_status
            logger.info(f"Updated dataset {dataset_id} status to {new_status}")
            return manifest
    
    raise ValueError(f"Dataset with ID {dataset_id} not found in manifest")

def get_datasets_by_modality(manifest: Dict[str, Any], modality: str) -> List[Dict[str, Any]]:
    """
    Retrieve all datasets of a specific modality.
    
    Args:
        manifest: The loaded manifest dictionary.
        modality: The modality to filter by (e.g., 'SNP', 'metabolite').
    
    Returns:
        List of dataset dictionaries matching the modality.
    """
    return [
        dataset for dataset in manifest.get("datasets", [])
        if dataset.get("modality") == modality
    ]

def get_source_type(manifest: Dict[str, Any]) -> str:
    """
    Get the source_type from the manifest.
    
    Args:
        manifest: The loaded manifest dictionary.
    
    Returns:
        The source_type string ('REAL', 'SIMULATED', or 'HYBRID').
    """
    return manifest.get("source_type", "SIMULATED")

def is_simulation_mode(manifest: Dict[str, Any]) -> bool:
    """
    Check if the manifest indicates simulation mode.
    
    Args:
        manifest: The loaded manifest dictionary.
    
    Returns:
        True if source_type is 'SIMULATED', False otherwise.
    """
    return get_source_type(manifest) == "SIMULATED"
