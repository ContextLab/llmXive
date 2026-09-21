"""
Task T037: Update state/projects/PROJ-312-.../state.yaml with artifact hashes and updated_at timestamp.
Implements Constitution Principle V: State tracking of artifacts.
"""
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ID = "PROJ-312-evaluating-the-impact-of-code-generation"
STATE_DIR = Path("state") / "projects" / PROJECT_ID
STATE_FILE = STATE_DIR / "state.yaml"

# Artifacts to hash and track (relative to project root)
ARTIFACTS_TO_TRACK = [
    "data/raw/repos.json",
    "data/raw/pr_data.json",
    "data/processed/pr_turnaround.csv",
    "data/processed/pr_turnaround_cleaned.csv",
    "data/processed/excluded_repos.txt",
    "data/processed/repo_metadata.json",
    "data/processed/distribution_stats.json",
    "data/processed/statistical_results.json",
    "data/spot_check/sample_list.csv",
    "data/spot_check/annotations.csv",
    "data/spot_check/validation_report.csv",
    "artifacts/boxplot.png",
    "artifacts/final_report.md",
]

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_current_state() -> Dict[str, Any]:
    """
    Load existing state file if it exists, otherwise return empty structure.
    
    Returns:
        Dictionary containing current state
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load existing state file: {e}. Starting fresh.")
            return {}
    return {}

def update_state_with_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update state dictionary with artifact hashes and metadata.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    updated_artifacts = {}
    missing_artifacts = []
    
    for artifact_path in ARTIFACTS_TO_TRACK:
        full_path = Path(artifact_path)
        if full_path.exists():
            try:
                file_hash = compute_file_hash(full_path)
                file_size = full_path.stat().st_size
                last_modified = datetime.fromtimestamp(
                    full_path.stat().st_mtime, tz=timezone.utc
                ).isoformat()
                
                updated_artifacts[artifact_path] = {
                    "hash": file_hash,
                    "size_bytes": file_size,
                    "last_modified": last_modified,
                    "exists": True
                }
                logger.info(f"Hashed artifact: {artifact_path} ({file_size} bytes)")
            except Exception as e:
                logger.error(f"Error hashing {artifact_path}: {e}")
                missing_artifacts.append(artifact_path)
        else:
            updated_artifacts[artifact_path] = {
                "exists": False,
                "hash": None,
                "size_bytes": None,
                "last_modified": None,
                "reason": "File not found"
            }
            logger.warning(f"Artifact missing: {artifact_path}")
    
    state["artifacts"] = updated_artifacts
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["artifact_count"] = len([a for a in updated_artifacts.values() if a.get("exists")])
    state["missing_count"] = len([a for a in updated_artifacts.values() if not a.get("exists")])
    
    return state

def save_state(state: Dict[str, Any]) -> None:
    """
    Save state dictionary to YAML file.
    
    Args:
        state: State dictionary to save
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"State saved to {STATE_FILE}")

def main() -> None:
    """
    Main entry point for T037: Update state with artifact hashes.
    """
    logger.info(f"Starting T037: Updating state for {PROJECT_ID}")
    
    current_state = load_current_state()
    updated_state = update_state_with_artifacts(current_state)
    save_state(updated_state)
    
    logger.info(f"T037 completed. State updated at {updated_state['updated_at']}")
    logger.info(f"Artifacts tracked: {updated_state['artifact_count']}, Missing: {updated_state['missing_count']}")

if __name__ == "__main__":
    main()
