"""
Dataset Registry Management Module.

Handles the selection, verification, and registration of public policy datasets.
Supports fetching from Hugging Face and computing SHA256 checksums for integrity.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REGISTRY_PATH = DATA_DIR / "dataset_registry.yaml"

# Verified sources for the initial datasets
DATASET_CONFIGS = [
    {
        "name": "california_housing",
        "source_type": "huggingface",
        "source_id": "scikit-learn/california_housing",
        "description": "California Housing Prices - 20,640 observations, 8 features.",
        "target_file": "california_housing.csv",
        "checksum": None,  # Computed at runtime
        "columns": ["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude", "MedHouseVal"]
    },
    {
        "name": "crime_and_communities",
        "source_type": "huggingface",
        "source_id": "UCI/crime_and_communities",
        "description": "Crime and Communities - US county crime data and demographics.",
        "target_file": "crime_and_communities.csv",
        "checksum": None,
        "columns": None  # Dynamic based on dataset
    }
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_and_save_dataset(config: Dict[str, Any]) -> Path:
    """
    Fetch dataset from Hugging Face, save as CSV, and compute checksum.
    
    Args:
        config: Dataset configuration dictionary.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        RuntimeError: If dataset fetch fails or file cannot be saved.
    """
    source_id = config["source_id"]
    target_file = config["target_file"]
    target_path = RAW_DIR / target_file

    print(f"Fetching dataset: {source_id} -> {target_path}")
    
    try:
        # Load dataset from Hugging Face
        ds = load_dataset(source_id, split="train")
        
        # Convert to pandas and save
        df = ds.to_pandas()
        df.to_csv(target_path, index=False)
        
        print(f"Saved {len(df)} rows to {target_path}")
        
        # Compute checksum
        checksum = compute_sha256(target_path)
        config["checksum"] = checksum
        
        return target_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch and save dataset {source_id}: {str(e)}")

def update_registry() -> None:
    """
    Fetch datasets, compute checksums, and update the registry file.
    
    This function:
    1. Ensures the raw data directory exists
    2. Fetches each configured dataset
    3. Computes SHA256 checksums
    4. Writes the registry to YAML
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    registry_entries = []
    
    for config in DATASET_CONFIGS:
        try:
            path = fetch_and_save_dataset(config)
            entry = {
                "name": config["name"],
                "description": config["description"],
                "source_type": config["source_type"],
                "source_id": config["source_id"],
                "file_path": str(path.relative_to(PROJECT_ROOT)),
                "checksum": config["checksum"],
                "columns": config.get("columns"),
                "verified": True
            }
            registry_entries.append(entry)
            print(f"✓ Registered: {config['name']} (checksum: {config['checksum'][:16]}...)")
            
        except Exception as e:
            print(f"✗ Failed to register {config['name']}: {str(e)}")
            # Add entry with verified=False for failed datasets
            entry = {
                "name": config["name"],
                "description": config["description"],
                "source_type": config["source_type"],
                "source_id": config["source_id"],
                "file_path": None,
                "checksum": None,
                "columns": config.get("columns"),
                "verified": False,
                "error": str(e)
            }
            registry_entries.append(entry)
    
    # Write registry
    registry_data = {
        "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z",  # Placeholder, can be dynamic
        "datasets": registry_entries
    }
    
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(registry_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nRegistry updated: {REGISTRY_PATH}")

def verify_checksum(dataset_name: str) -> bool:
    """
    Verify the checksum of a registered dataset.
    
    Args:
        dataset_name: Name of the dataset to verify.
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        ValueError: If dataset not found in registry.
    """
    if not REGISTRY_PATH.exists():
        raise ValueError("Registry file not found")
        
    with open(REGISTRY_PATH, "r") as f:
        registry = yaml.safe_load(f)
        
    dataset = next((d for d in registry["datasets"] if d["name"] == dataset_name), None)
    if not dataset:
        raise ValueError(f"Dataset {dataset_name} not found in registry")
        
    if not dataset["verified"]:
        return False
        
    file_path = PROJECT_ROOT / dataset["file_path"]
    if not file_path.exists():
        return False
        
    current_checksum = compute_sha256(file_path)
    return current_checksum == dataset["checksum"]

if __name__ == "__main__":
    update_registry()
