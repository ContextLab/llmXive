import os
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_state_yaml() -> Dict[str, Any]:
    """Load state.yaml from project root."""
    state_path = get_path("state/projects/PROJ-345/state.yaml")
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Creating new one.")
        return {"project": "PROJ-345", "checksums": {}, "metrics": {}}
    
    with open(state_path, "r") as f:
        return yaml.safe_load(f)

def save_state_yaml(data: Dict[str, Any]) -> None:
    """Save state.yaml to project root."""
    state_path = get_path("state/projects/PROJ-345/state.yaml")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def verify_and_record_checksums() -> Dict[str, str]:
    """
    Verify checksums for all downloaded raw data files in data/raw/
    and record them in state.yaml.
    
    Returns:
        Dict mapping file paths to their calculated checksums.
    """
    raw_dir = get_path("data/raw")
    if not raw_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_dir}")
        return {}

    state_data = load_state_yaml()
    if "checksums" not in state_data:
        state_data["checksums"] = {}

    recorded_checksums = state_data["checksums"]
    calculated_checksums = {}

    for file_path in raw_dir.glob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(get_path()))
            
            try:
                current_checksum = calculate_file_checksum(file_path)
                calculated_checksums[rel_path] = current_checksum
                
                if rel_path in recorded_checksums:
                    if recorded_checksums[rel_path] == current_checksum:
                        logger.info(f"Checksum verified: {rel_path}")
                    else:
                        logger.warning(f"Checksum MISMATCH for {rel_path}")
                        logger.warning(f"  Expected: {recorded_checksums[rel_path]}")
                        logger.warning(f"  Got:      {current_checksum}")
                else:
                    logger.info(f"Recording new checksum for: {rel_path}")
                    state_data["checksums"][rel_path] = current_checksum
                    
            except Exception as e:
                logger.error(f"Error processing {rel_path}: {e}")

    save_state_yaml(state_data)
    return calculated_checksums

def calculate_linked_metadata_percentage() -> float:
    """
    Calculate the percentage of trials that have successfully linked metadata.
    
    Reads data/processed/linked_trials.csv and calculates the ratio of 
    trials with non-null stimulus_id to total trials.
    
    Returns:
        Float between 0.0 and 1.0 representing the linked metadata percentage.
    """
    linked_trials_path = get_path("data/processed/linked_trials.csv")
    if not linked_trials_path.exists():
        logger.error(f"Linked trials file not found: {linked_trials_path}")
        return 0.0

    total_trials = 0
    linked_trials = 0

    try:
        with open(linked_trials_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_trials += 1
                # Check if stimulus_id exists and is not empty
                if row.get("stimulus_id") and row["stimulus_id"].strip():
                    linked_trials += 1
    except Exception as e:
        logger.error(f"Error reading linked trials: {e}")
        return 0.0

    if total_trials == 0:
        logger.warning("No trials found in linked_trials.csv")
        return 0.0

    percentage = linked_trials / total_trials
    return percentage

def main():
    """Main entry point for T018: Checksum verification and metadata reporting."""
    logger.info("=== T018: Checksum Verification and Metadata Reporting ===")
    
    # Step 1: Verify and record checksums
    logger.info("Verifying checksums for raw data...")
    checksums = verify_and_record_checksums()
    logger.info(f"Processed {len(checksums)} files.")
    
    # Step 2: Calculate linked metadata percentage
    logger.info("Calculating linked metadata percentage...")
    linked_percentage = calculate_linked_metadata_percentage()
    
    # Configuration for SC-001 target
    threshold = 0.95  # Default 'vast majority' target
    
    logger.info("=" * 60)
    logger.info("T018 RESULTS:")
    logger.info(f"  Linked Metadata Percentage: {linked_percentage:.2%}")
    logger.info(f"  SC-001 Threshold (Configurable): {threshold:.2%}")
    
    if linked_percentage >= threshold:
        logger.info(f"  ✅ PASS: Exceeds SC-001 target of {threshold:.0%}")
    else:
        logger.warning(f"  ⚠️  FAIL: Below SC-001 target of {threshold:.0%}")
        logger.warning(f"  Current: {linked_percentage:.2%}, Needed: {threshold:.2%}")
    
    logger.info("=" * 60)
    
    # Update state.yaml with metrics
    state_data = load_state_yaml()
    if "metrics" not in state_data:
        state_data["metrics"] = {}
    
    state_data["metrics"]["linked_metadata_percentage"] = linked_percentage
    state_data["metrics"]["sc001_threshold"] = threshold
    state_data["metrics"]["sc001_passed"] = linked_percentage >= threshold
    
    save_state_yaml(state_data)
    logger.info("Metrics saved to state.yaml")

if __name__ == "__main__":
    import csv
    main()
