"""
Manifest loader and schema validator for plant disease resistance project.

Handles loading, validating, and accessing the data manifest file
that tracks all data sources, types, and processing status.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import get_data_path
from utils.exceptions import PipelineError, EX_DATA_INTEGRITY
from utils.logging import get_logger, log_error_context

logger = get_logger(__name__)

MANIFEST_FILENAME = "data_manifest.yaml"
REQUIRED_FIELDS = {
    "schema_version": str,
    "created_at": str,
    "updated_at": str,
    "source_type": str,
    "datasets": list
}

DATASET_REQUIRED_FIELDS = {
    "accession_id": str,
    "modality": str,
    "source_url": str,
    "status": str,
    "file_path": str
}

VALID_SOURCE_TYPES = {"REAL", "SIMULATED"}
VALID_MODALITIES = {"SNP", "METABOLITE", "PHENOTYPE"}
VALID_STATUSES = {"pending", "downloaded", "preprocessed", "failed"}

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate the data manifest file.
    
    Args:
        manifest_path: Optional path to manifest file. If None, uses default location.
        
    Returns:
        Dictionary containing manifest data.
        
    Raises:
        PipelineError: If manifest file is missing, malformed, or fails validation.
    """
    if manifest_path is None:
        data_dir = get_data_path()
        manifest_path = Path(data_dir) / MANIFEST_FILENAME
    
    if not Path(manifest_path).exists():
        error_msg = f"Manifest file not found: {manifest_path}"
        logger.error(error_msg)
        raise PipelineError(
            code=EX_DATA_INTEGRITY.code,
            message=error_msg,
            context={"file": str(manifest_path)}
        )
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse manifest YAML: {e}"
        logger.error(error_msg)
        raise PipelineError(
            code=EX_DATA_INTEGRITY.code,
            message=error_msg,
            context={"file": str(manifest_path), "error": str(e)}
        )
    
    if not _validate_manifest_schema(data):
        error_msg = "Manifest schema validation failed"
        logger.error(error_msg)
        raise PipelineError(
            code=EX_DATA_INTEGRITY.code,
            message=error_msg,
            context={"file": str(manifest_path)}
        )
    
    logger.info(f"Successfully loaded manifest from {manifest_path}")
    return data

def _validate_manifest_schema(data: Dict[str, Any]) -> bool:
    """
    Validate manifest against required schema.
    
    Args:
        data: Manifest dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    # Check top-level required fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return False
        if not isinstance(data[field], expected_type):
            logger.warning(f"Invalid type for field {field}: expected {expected_type.__name__}")
            return False
    
    # Validate source_type
    if data["source_type"] not in VALID_SOURCE_TYPES:
        logger.warning(f"Invalid source_type: {data['source_type']}. Must be one of {VALID_SOURCE_TYPES}")
        return False
    
    # Validate datasets list
    if len(data["datasets"]) == 0:
        logger.warning("Manifest contains no datasets")
        return False
    
    for idx, dataset in enumerate(data["datasets"]):
        if not isinstance(dataset, dict):
            logger.warning(f"Dataset at index {idx} is not a dictionary")
            return False
        
        for field, expected_type in DATASET_REQUIRED_FIELDS.items():
            if field not in dataset:
                logger.warning(f"Dataset at index {idx} missing required field: {field}")
                return False
            if not isinstance(dataset[field], expected_type):
                logger.warning(f"Dataset at index {idx}: Invalid type for {field}")
                return False
        
        # Validate modality
        if dataset["modality"] not in VALID_MODALITIES:
            logger.warning(f"Invalid modality: {dataset['modality']}. Must be one of {VALID_MODALITIES}")
            return False
        
        # Validate status
        if dataset["status"] not in VALID_STATUSES:
            logger.warning(f"Invalid status: {dataset['status']}. Must be one of {VALID_STATUSES}")
            return False
    
    return True

def get_datasets_by_modality(manifest: Dict[str, Any], modality: str) -> List[Dict[str, Any]]:
    """
    Filter datasets by modality type.
    
    Args:
        manifest: Loaded manifest dictionary.
        modality: Modality to filter by (SNP, METABOLITE, PHENOTYPE).
        
    Returns:
        List of dataset dictionaries matching the modality.
        
    Raises:
        ValueError: If modality is not valid.
    """
    if modality not in VALID_MODALITIES:
        raise ValueError(f"Invalid modality: {modality}. Must be one of {VALID_MODALITIES}")
    
    return [ds for ds in manifest["datasets"] if ds["modality"] == modality]

def get_dataset_by_accession(manifest: Dict[str, Any], accession_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a dataset by its accession ID.
    
    Args:
        manifest: Loaded manifest dictionary.
        accession_id: Accession ID to search for.
        
    Returns:
        Dataset dictionary if found, None otherwise.
    """
    for dataset in manifest["datasets"]:
        if dataset["accession_id"] == accession_id:
            return dataset
    return None

def get_source_type(manifest: Dict[str, Any]) -> str:
    """
    Get the source type from the manifest.
    
    Args:
        manifest: Loaded manifest dictionary.
        
    Returns:
        Source type string ("REAL" or "SIMULATED").
    """
    return manifest["source_type"]

def create_default_manifest(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Create a default manifest structure for a new project run.
    
    Args:
        output_path: Optional path to write the manifest file.
        
    Returns:
        The created manifest dictionary.
    """
    now = datetime.utcnow().isoformat() + "Z"
    manifest = {
        "schema_version": "1.0.0",
        "created_at": now,
        "updated_at": now,
        "source_type": "SIMULATED",
        "datasets": []
    }
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Created default manifest at {output_path}")
    
    return manifest
