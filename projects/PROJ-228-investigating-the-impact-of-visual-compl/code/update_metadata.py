import os
import yaml
import json
from datetime import datetime
from pathlib import Path

def ensure_dir(file_path: Path) -> None:
    """Ensure the directory for a file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

def init_metadata(
    dataset_id: str,
    version: str,
    checksum: str,
    download_date: str,
    metadata_path: Path
) -> None:
    """
    Initialize or update the data/metadata.yaml file with dataset information.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000246')
        version: The dataset version string
        checksum: The SHA256 checksum of the downloaded dataset
        download_date: ISO format timestamp of download
        metadata_path: Path to the metadata.yaml file
    """
    ensure_dir(metadata_path)
    
    metadata = {
        "dataset_id": dataset_id,
        "version": version,
        "checksum": checksum,
        "download_date": download_date
    }
    
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

def init_project_state(
    project_id: str,
    artifact_hashes: dict,
    state_path: Path
) -> None:
    """
    Initialize or update the project state YAML file with artifact hashes.
    
    Args:
        project_id: The project identifier (e.g., 'PROJ-228-investigating-the-impact-of-visual-compl')
        artifact_hashes: Dictionary mapping artifact names to their checksums
        state_path: Path to the state YAML file
    """
    ensure_dir(state_path)
    
    state = {
        "project_id": project_id,
        "artifact_hashes": artifact_hashes,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_metadata_with_download(
    dataset_id: str,
    version: str,
    checksum: str,
    project_id: str,
    artifact_hashes: dict,
    metadata_path: Path,
    state_path: Path
) -> None:
    """
    Update both metadata.yaml and project state file after a successful download.
    
    This function ensures that:
    1. data/metadata.yaml is updated with the new dataset checksum and download date
    2. state/projects/{project_id}.yaml is updated with the artifact_hashes map
    
    Args:
        dataset_id: The OpenNeuro dataset ID
        version: The dataset version
        checksum: The SHA256 checksum of the downloaded dataset
        project_id: The project identifier
        artifact_hashes: Dictionary of artifact names to checksums
        metadata_path: Path to data/metadata.yaml
        state_path: Path to state/projects/{project_id}.yaml
    """
    download_date = datetime.utcnow().isoformat()
    
    # Update metadata.yaml
    init_metadata(
        dataset_id=dataset_id,
        version=version,
        checksum=checksum,
        download_date=download_date,
        metadata_path=metadata_path
    )
    
    # Update project state
    init_project_state(
        project_id=project_id,
        artifact_hashes=artifact_hashes,
        state_path=state_path
    )
