import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import yaml

from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import validate_dataframe_schema, load_schema
from data.config import get_config

logger = get_logger(__name__)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_data_to_raw(data_source_type: str, data: pd.DataFrame, raw_output_path: Path) -> Dict[str, Any]:
    """
    Saves the provided DataFrame to the `data/raw` directory as a CSV.
    
    Args:
        data_source_type: Either 'real' or 'synthetic'.
        data: The pandas DataFrame to save.
        raw_output_path: The full path where the CSV should be written.
        
    Returns:
        A dictionary containing the file path, hash, and source type.
    """
    logger.info(f"Saving {data_source_type} data to {raw_output_path}")
    
    # Ensure directory exists
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    data.to_csv(raw_output_path, index=False)
    
    # Calculate checksum
    file_hash = calculate_file_hash(raw_output_path)
    
    logger.info(f"Saved {raw_output_path.name} (SHA-256: {file_hash[:16]}...)")
    
    return {
        "path": str(raw_output_path),
        "hash": file_hash,
        "source_type": data_source_type,
        "rows": len(data),
        "columns": list(data.columns)
    }

def write_artifact_hashes_to_state(project_state_path: Path, artifact_info: Dict[str, Any]) -> None:
    """
    Appends or updates the artifact hash information in the project state YAML file.
    
    Args:
        project_state_path: Path to the state YAML file.
        artifact_info: Dictionary containing path, hash, source_type, etc.
    """
    state_data = {}
    
    if project_state_path.exists():
        with open(project_state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    # Ensure structure exists
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    # Update with new artifact info
    # Keying by the filename for uniqueness within raw data
    filename = Path(artifact_info['path']).name
    state_data['artifact_hashes'][filename] = {
        "path": artifact_info['path'],
        "hash": artifact_info['hash'],
        "source_type": artifact_info['source_type'],
        "rows": artifact_info['rows'],
        "columns": artifact_info['columns']
    }
    
    # Write back to file
    with open(project_state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file at {project_state_path}")

def run_loader(
    data: pd.DataFrame, 
    data_source_type: str, 
    output_filename: str = "dataset.csv"
) -> Dict[str, Any]:
    """
    Main entry point for T012.
    1. Validates the data against the dataset schema.
    2. Saves the data to `data/raw`.
    3. Writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml`.
    
    Args:
        data: The DataFrame to save (from download.py).
        data_source_type: 'real' or 'synthetic'.
        output_filename: Name of the file to save in data/raw.
        
    Returns:
        The artifact info dictionary.
    """
    log_execution_start(logger, "T012_Loader")
    
    config = get_config()
    project_root = config.project_root
    raw_dir = project_root / "data" / "raw"
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-490-the-effect-of-simulated-social-compariso.yaml"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate schema if available
    try:
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
        if schema_path.exists():
            schema = load_schema(schema_path)
            validate_dataframe_schema(data, schema)
            logger.info("Data validated against dataset schema successfully.")
        else:
            logger.warning("Dataset schema not found, skipping validation.")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise e
    
    # Construct output path
    output_path = raw_dir / output_filename
    
    # Save and hash
    artifact_info = load_data_to_raw(data_source_type, data, output_path)
    
    # Update state file
    write_artifact_hashes_to_state(state_file, artifact_info)
    
    log_execution_end(logger, "T012_Loader")
    
    return artifact_info
