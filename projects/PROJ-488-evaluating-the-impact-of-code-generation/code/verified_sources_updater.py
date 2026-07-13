"""
Module to manage and verify dataset sources.
Implements the verification workflow for T014.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Import from project API
from logging_config import get_logger

# Constants
VERIFIED_SOURCES_PATH = Path("data/verified_sources.json")
ERROR_CODE_VERIFICATION = 101

logger = get_logger(__name__)


def load_verified_sources() -> Dict[str, Any]:
    """
    Load the verified sources JSON file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not VERIFIED_SOURCES_PATH.exists():
        raise FileNotFoundError(f"Verified sources file not found at {VERIFIED_SOURCES_PATH}")
    
    with open(VERIFIED_SOURCES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_datasets(required_datasets: List[str]) -> bool:
    """
    Verify that all required datasets are listed in data/verified_sources.json.
    
    Args:
        required_datasets: List of dataset identifiers to check (e.g., 'code_search_net', 'codeparrot/codegen')
    
    Returns:
        True if all datasets are verified.
    
    Raises:
        SystemExit with code 101 if verification fails.
    """
    try:
        sources_data = load_verified_sources()
    except FileNotFoundError as e:
        logger.error(f"Verification failed: {e}")
        logger.error(f"Aborting with error code {ERROR_CODE_VERIFICATION}")
        sys.exit(ERROR_CODE_VERIFICATION)
    
    verified_list = sources_data.get("sources", [])
    missing_datasets = []
    
    for dataset in required_datasets:
        if dataset not in verified_list:
            missing_datasets.append(dataset)
    
    if missing_datasets:
        logger.error(f"Verification failed: The following datasets are not in verified_sources.json: {missing_datasets}")
        logger.error(f"Please ensure datasets are downloaded and registered before proceeding.")
        logger.error(f"Aborting with error code {ERROR_CODE_VERIFICATION}")
        sys.exit(ERROR_CODE_VERIFICATION)
    
    logger.info(f"Verification successful: All required datasets are verified.")
    return True


def update_verified_sources(datasets: List[str], notes: str = "") -> None:
    """
    Update the verified_sources.json file with new datasets.
    
    Args:
        datasets: List of dataset identifiers to add.
        notes: Optional notes to append to the file.
    """
    if VERIFIED_SOURCES_PATH.exists():
        with open(VERIFIED_SOURCES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"sources": [], "verified_at": "", "notes": ""}
    
    current_sources = data.get("sources", [])
    for dataset in datasets:
        if dataset not in current_sources:
            current_sources.append(dataset)
    
    data["sources"] = current_sources
    data["verified_at"] = "2023-10-27T10:00:00Z" # Keep existing or update as needed
    if notes:
        data["notes"] = notes
    
    with open(VERIFIED_SOURCES_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated verified_sources.json with datasets: {datasets}")


def main() -> None:
    """
    Main entry point for the verification workflow.
    Verifies CodeSearchNet and CodeParrot/CodeGen datasets.
    """
    required = ["code_search_net", "codeparrot/codegen"]
    logger.info(f"Starting verification workflow for: {required}")
    verify_datasets(required)
    logger.info("Workflow completed successfully.")


if __name__ == "__main__":
    main()