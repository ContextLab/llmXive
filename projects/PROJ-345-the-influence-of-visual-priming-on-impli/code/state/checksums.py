import os
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path, get_seed

logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_yaml(state_path: Path) -> Dict[str, Any]:
    """Load state.yaml file, creating an empty structure if it doesn't exist."""
    if not state_path.exists():
        return {
            "project_id": "PROJ-345-the-influence-of-visual-priming-on-impli",
            "artifacts": {},
            "checksums": {},
            "metadata": {
                "created_at": None,
                "last_updated": None
            }
        }
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_state_yaml(state_path: Path, data: Dict[str, Any]) -> None:
    """Save state dictionary to state.yaml."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def verify_and_record_checksums(state_path: Path, raw_data_dir: Path, artifact_files: list) -> Dict[str, Any]:
    """
    Verify checksums of raw data files and record them in state.yaml.
    Returns updated state data.
    """
    state_data = load_state_yaml(state_path)
    
    # Ensure metadata exists
    if "metadata" not in state_data:
        state_data["metadata"] = {}
    if "checksums" not in state_data:
        state_data["checksums"] = {}
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    # Record checksums for raw data files
    if raw_data_dir.exists():
        raw_checksums = {}
        for file_path in raw_data_dir.rglob("*"):
            if file_path.is_file():
                try:
                    checksum = calculate_file_checksum(file_path)
                    rel_path = str(file_path.relative_to(raw_data_dir))
                    raw_checksums[rel_path] = {
                        "algorithm": "sha256",
                        "value": checksum
                    }
                    logger.info(f"Recorded checksum for {rel_path}: {checksum[:16]}...")
                except Exception as e:
                    logger.warning(f"Could not calculate checksum for {file_path}: {e}")
        
        state_data["checksums"]["raw_data"] = raw_checksums
    
    # Record checksums for specific artifact files
    for artifact_path in artifact_files:
        path_obj = Path(artifact_path)
        if path_obj.exists():
            try:
                checksum = calculate_file_checksum(path_obj)
                state_data["checksums"]["processed_artifacts"] = state_data["checksums"].get("processed_artifacts", {})
                state_data["checksums"]["processed_artifacts"][str(path_obj)] = {
                    "algorithm": "sha256",
                    "value": checksum
                }
                logger.info(f"Recorded checksum for artifact {path_obj}: {checksum[:16]}...")
            except Exception as e:
                logger.warning(f"Could not calculate checksum for {path_obj}: {e}")
    
    # Update metadata
    from datetime import datetime
    state_data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    save_state_yaml(state_path, state_data)
    return state_data

def calculate_linked_metadata_percentage(linked_trials_path: Path, state_path: Path) -> float:
    """
    Calculate the percentage of trials with linked metadata from linked_trials.csv.
    Returns the percentage as a float (0.0 to 100.0).
    """
    import pandas as pd
    
    if not linked_trials_path.exists():
        raise FileNotFoundError(f"Linked trials file not found: {linked_trials_path}")
    
    df = pd.read_csv(linked_trials_path)
    
    # Check for required columns
    required_cols = ['trial_id', 'stimulus_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {linked_trials_path}: {missing_cols}")
    
    total_trials = len(df)
    if total_trials == 0:
        logger.warning("No trials found in linked_trials.csv")
        return 0.0
    
    # Count trials with valid (non-null, non-empty) stimulus_id
    linked_trials = df[df['stimulus_id'].notna() & (df['stimulus_id'].astype(str).str.strip() != '')]
    linked_count = len(linked_trials)
    
    percentage = (linked_count / total_trials) * 100.0
    
    # Log the result
    logger.info(f"Linked metadata percentage: {percentage:.2f}% ({linked_count}/{total_trials} trials)")
    
    # Update state.yaml with this metric
    state_data = load_state_yaml(state_path)
    if "metrics" not in state_data:
        state_data["metrics"] = {}
    
    state_data["metrics"]["linked_metadata_percentage"] = {
        "value": percentage,
        "total_trials": total_trials,
        "linked_trials": linked_count,
        "threshold": 95.0,  # Default threshold as per SC-001
        "target_description": "SC-001: Vast majority of trials must have linked metadata",
        "status": "PASS" if percentage >= 95.0 else "FAIL"
    }
    
    save_state_yaml(state_path, state_data)
    
    return percentage

def main():
    """Main entry point for checksum verification and metadata percentage calculation."""
    logging.basicConfig(level=logging.INFO)
    
    # Get paths from config
    state_path = get_path("state") / "projects" / "PROJ-345" / "state.yaml"
    raw_data_dir = get_path("data") / "raw"
    linked_trials_path = get_path("data") / "processed" / "linked_trials.csv"
    
    logger.info("Starting checksum verification and metadata percentage calculation...")
    
    try:
        # Verify and record checksums
        artifact_files = [str(linked_trials_path)]
        state_data = verify_and_record_checksums(state_path, raw_data_dir, artifact_files)
        logger.info("Checksum verification completed.")
        
        # Calculate linked metadata percentage
        if linked_trials_path.exists():
            percentage = calculate_linked_metadata_percentage(linked_trials_path, state_path)
            
            # Log final result with threshold check
            threshold = 95.0
            if percentage >= threshold:
                logger.info(f"✓ SUCCESS: Linked metadata percentage ({percentage:.2f}%) meets SC-001 target (≥{threshold}%)")
            else:
                logger.error(f"✗ FAILURE: Linked metadata percentage ({percentage:.2f}%) below SC-001 target ({threshold}%)")
                logger.error("Data gap detected: Insufficient linkage between trials and stimuli.")
        else:
            logger.warning(f"Linked trials file not found at {linked_trials_path}. Skipping percentage calculation.")
            
    except Exception as e:
        logger.error(f"Error during checksum verification or metadata calculation: {e}")
        raise

if __name__ == "__main__":
    main()