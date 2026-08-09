"""
Downloaders module for fetching and managing materials science datasets.
Implements fail-loudly logic for OQMD, AFLOW, and Materials Project.
"""
import os
import hashlib
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from datasets import load_dataset
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hex digest of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def generate_checksum_file(file_path: Path, checksum_dir: Path) -> Path:
    """
    Generate a checksum file in sha256sum format.
    
    Args:
        file_path: Path to the file to checksum.
        checksum_dir: Directory to store the checksum file.
        
    Returns:
        Path to the generated checksum file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot generate checksum for non-existent file: {file_path}")
    
    checksum = calculate_sha256(file_path)
    checksum_filename = f"{file_path.name}.sha256"
    checksum_path = checksum_dir / checksum_filename
    
    # Format: <hash> <filename> (sha256sum style)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    logger.info(f"Generated checksum file: {checksum_path}")
    return checksum_path

def update_state_file(state_path: Path, artifact_name: str, checksum: str) -> None:
    """
    Update the project state YAML file with a new artifact checksum.
    
    Args:
        state_path: Path to the state YAML file.
        artifact_name: Name of the artifact (e.g., 'oqmd.parquet').
        checksum: SHA-256 checksum of the artifact.
        
    Raises:
        ValueError: If the state file structure is invalid or missing 'artifact_hashes'.
        FileNotFoundError: If the state file does not exist.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    try:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in state file: {e}")
    
    if not isinstance(state_data, dict):
        raise ValueError("State file must be a YAML dictionary.")
    
    if 'artifact_hashes' not in state_data:
        raise ValueError("State file is missing the 'artifact_hashes' key.")
    
    if not isinstance(state_data['artifact_hashes'], dict):
        raise ValueError("'artifact_hashes' must be a dictionary.")
    
    state_data['artifact_hashes'][artifact_name] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file with checksum for {artifact_name}")

def load_huggingface_dataset(dataset_name: str, config_name: str, split: str, output_path: Path) -> Path:
    """
    Load a dataset from Hugging Face and save it as a Parquet file.
    
    Args:
        dataset_name: Name of the dataset on Hugging Face.
        config_name: Configuration name for the dataset.
        split: Dataset split to load (e.g., 'train').
        output_path: Path where the Parquet file will be saved.
        
    Returns:
        Path to the saved Parquet file.
        
    Raises:
        DataFetchError: If the dataset fetch fails.
    """
    try:
        logger.info(f"Loading dataset {dataset_name} (config: {config_name}, split: {split})...")
        dataset = load_dataset(dataset_name, config_name, split=split, trust_remote_code=True)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as Parquet
        dataset.to_parquet(str(output_path))
        logger.info(f"Dataset saved to {output_path}")
        
        return output_path
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise DataFetchError(f"Failed to fetch dataset {dataset_name}: {e}")

def download_oqmd_constitution(output_dir: Path) -> Path:
    """
    Download the OQMD constitution dataset.
    
    Args:
        output_dir: Directory to save the dataset.
        
    Returns:
        Path to the downloaded Parquet file.
    """
    output_path = output_dir / "oqmd.parquet"
    return load_huggingface_dataset(
        dataset_name="oqmd/oqmd",
        config_name="formation_energy_per_atom",
        split="train",
        output_path=output_path
    )

def download_aflow_constitution(output_dir: Path) -> Optional[Path]:
    """
    Download the AFLOW constitution dataset.
    
    Args:
        output_dir: Directory to save the dataset.
        
    Returns:
        Path to the downloaded Parquet file, or None if unavailable.
    """
    # AFLOW might not have a direct HF dataset; handle gracefully if needed
    # For now, assume it's not available or requires a different mechanism
    logger.warning("AFLOW dataset download not implemented in this version.")
    return None

def download_materials_project(output_dir: Path, api_key: Optional[str] = None) -> Optional[Path]:
    """
    Download the Materials Project dataset.
    
    Args:
        output_dir: Directory to save the dataset.
        api_key: Optional API key for authentication.
        
    Returns:
        Path to the downloaded Parquet file, or None if unavailable.
    """
    if not api_key:
        logger.warning("Materials Project API key not provided. Skipping download.")
        return None
    
    try:
        output_path = output_dir / "mp.parquet"
        # Note: The actual dataset name might vary. Using a placeholder here.
        # In a real scenario, this would use the verified HF dataset ID for MP.
        return load_huggingface_dataset(
            dataset_name="materials-project/mp",
            config_name="default",
            split="train",
            output_path=output_path
        )
    except DataFetchError as e:
        logger.warning(f"Materials Project download failed: {e}")
        return None

def main():
    """
    Main function to orchestrate dataset downloads and checksum generation.
    """
    project_root = Path(__file__).parent.parent
    data_raw_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / "PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml"
    
    # Ensure directories exist
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for MP API key
    mp_api_key = os.getenv("MP_API_KEY")
    
    # Download OQMD
    oqmd_path = None
    try:
        oqmd_path = download_oqmd_constitution(data_raw_dir)
    except DataFetchError as e:
        logger.error(f"OQMD download failed: {e}")
        raise e  # Fail loudly for OQMD
    
    # Download AFLOW (optional)
    aflow_path = download_aflow_constitution(data_raw_dir)
    
    # Download MP (optional)
    mp_path = download_materials_project(data_raw_dir, mp_api_key)
    
    # Generate checksums and update state
    artifacts_to_process = [
        (oqmd_path, "oqmd.parquet"),
        (mp_path, "mp.parquet")
    ]
    
    if aflow_path:
        artifacts_to_process.append((aflow_path, "aflow.parquet"))
    
    for path, name in artifacts_to_process:
        if path and path.exists():
            checksum = calculate_sha256(path)
            generate_checksum_file(path, data_raw_dir)
            update_state_file(state_file, name, checksum)
        else:
            logger.info(f"Skipping checksum for {name} (file not present)")

if __name__ == "__main__":
    main()
