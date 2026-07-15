import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from logging_config import get_logger

logger = get_logger(__name__)

VERIFIED_SOURCES_FILE = Path("data/verified_sources.json")

def load_verified_sources() -> Dict[str, str]:
    """
    Loads verified sources from JSON file.
    
    Returns:
        Dictionary of verified sources.
    """
    if not VERIFIED_SOURCES_FILE.exists():
        return {}
        
    with open(VERIFIED_SOURCES_FILE, 'r') as f:
        return json.load(f)

def verify_datasets(dataset_name: str, status: str = "verified"):
    """
    Verifies a dataset by updating its status.
    
    Args:
        dataset_name: Name of the dataset.
        status: Verification status.
    """
    sources = load_verified_sources()
    sources[dataset_name] = status
    update_verified_sources(dataset_name, status)

def update_verified_sources(dataset_name: str, status: str = "verified"):
    """
    Updates verified sources file.
    
    Args:
        dataset_name: Name of the dataset.
        status: Verification status.
    """
    sources = load_verified_sources()
    sources[dataset_name] = status
    
    VERIFIED_SOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERIFIED_SOURCES_FILE, 'w') as f:
        json.dump(sources, f, indent=2)
        
    logger.info(f"Updated verified sources: {dataset_name} -> {status}")

def main():
    """
    Main entry point for verified sources updater.
    """
    update_verified_sources("test_dataset", "verified")
    print(f"Verified sources: {load_verified_sources()}")

if __name__ == "__main__":
    main()