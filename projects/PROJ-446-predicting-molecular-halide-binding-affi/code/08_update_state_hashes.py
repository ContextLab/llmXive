"""
Task T039: Update state.yaml with final artifact hashes.

This script computes SHA-256 hashes for all critical project artifacts
(code files, data outputs, figures, and reports) and updates the
project's state.yaml file to reflect the current state of the pipeline.
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logger import get_logger
from code.utils.state_manager import (
    calculate_file_hash,
    calculate_directory_hash,
    load_state_yaml,
    save_state_yaml,
    get_project_state_path,
    generate_state_for_directory
)

logger = get_logger(__name__)

# Define the directories and files to include in the state hash
ARTIFACT_PATHS = [
    # Code directory
    "code",
    # Data outputs
    "data/processed",
    "data/simulated",
    # Figures
    "docs/paper/figures",
    # Reports
    "docs/paper/report.md",
    "data/processed/statistical_summary.json",
    "data/processed/feature_analysis.json",
    "data/processed/model_runs.json",
]

def get_relative_path(full_path: Path) -> str:
    """Convert absolute path to relative path from project root."""
    try:
        return str(full_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(full_path)

def collect_artifacts(paths: List[str]) -> Dict[str, str]:
    """
    Collect all artifacts and compute their hashes.
    
    Args:
        paths: List of relative paths to directories or files
        
    Returns:
        Dictionary mapping relative paths to their SHA-256 hashes
    """
    artifacts = {}
    
    for path_str in paths:
        full_path = PROJECT_ROOT / path_str
        rel_path = get_relative_path(full_path)
        
        if not full_path.exists():
            logger.warning(f"Artifact path does not exist: {rel_path}")
            continue
        
        if full_path.is_file():
            # Single file
            file_hash = calculate_file_hash(full_path)
            artifacts[rel_path] = file_hash
            logger.info(f"Hashed file: {rel_path} -> {file_hash[:16]}...")
        elif full_path.is_dir():
            # Directory - hash all files recursively
            dir_hash = generate_state_for_directory(full_path)
            if dir_hash:
                artifacts[rel_path] = dir_hash
                logger.info(f"Hashed directory: {rel_path} -> {dir_hash[:16]}...")
            else:
                logger.warning(f"Directory is empty or unreadable: {rel_path}")
        else:
            logger.warning(f"Path exists but is neither file nor directory: {rel_path}")
    
    return artifacts

def update_state_yaml(artifacts: Dict[str, str]) -> bool:
    """
    Update the state.yaml file with new artifact hashes.
    
    Args:
        artifacts: Dictionary of artifact paths to hashes
        
    Returns:
        True if update was successful, False otherwise
    """
    state_path = get_project_state_path()
    
    # Load existing state or create new
    state = load_state_yaml(state_path)
    if state is None:
        state = {
            "project_id": "PROJ-446-predicting-molecular-halide-binding-affi",
            "version": "1.0.0",
            "last_updated": None,
            "artifacts": {}
        }
    
    # Update artifact hashes
    state["artifacts"] = artifacts
    state["last_updated"] = "2024-01-01T00:00:00Z"  # Placeholder, actual time set by save
    
    # Save updated state
    save_state_yaml(state_path, state)
    logger.info(f"Successfully updated state.yaml at {state_path}")
    
    return True

def main() -> int:
    """
    Main entry point for updating state hashes.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting T039: Update state.yaml with final artifact hashes")
    
    try:
        # Collect all artifact hashes
        logger.info(f"Collecting artifacts from {len(ARTIFACT_PATHS)} paths...")
        artifacts = collect_artifacts(ARTIFACT_PATHS)
        
        if not artifacts:
            logger.error("No artifacts were collected. State update aborted.")
            return 1
        
        logger.info(f"Collected {len(artifacts)} artifact hashes")
        
        # Update state.yaml
        if not update_state_yaml(artifacts):
            logger.error("Failed to update state.yaml")
            return 1
        
        # Verify the update
        state_path = get_project_state_path()
        updated_state = load_state_yaml(state_path)
        
        if updated_state is None:
            logger.error("Failed to read updated state.yaml for verification")
            return 1
        
        if "artifacts" not in updated_state:
            logger.error("Updated state.yaml missing 'artifacts' key")
            return 1
        
        logger.info("Verification successful. State.yaml updated with:")
        for path, hash_val in updated_state["artifacts"].items():
            logger.info(f"  {path}: {hash_val[:16]}...")
        
        logger.info("T039 completed successfully")
        return 0
        
    except Exception as e:
        logger.exception(f"Unexpected error during T039 execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
