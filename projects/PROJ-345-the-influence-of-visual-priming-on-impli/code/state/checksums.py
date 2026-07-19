import os
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path, get_all_base_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SC-001 Target: 'Vast Majority' linked metadata
# Defined as configurable threshold, default 0.95
DEFAULT_LINKED_THRESHOLD = 0.95

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_yaml(state_path: Path) -> Dict[str, Any]:
    """Load existing state.yaml or return empty dict if not found."""
    if not state_path.exists():
        return {}
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_state_yaml(state_path: Path, data: Dict[str, Any]) -> None:
    """Save data to state.yaml."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def verify_and_record_checksums(state_path: Path, raw_data_dir: Path) -> Dict[str, Any]:
    """
    Verify checksums of files in raw_data_dir and record them in state.yaml.
    Returns the updated state dictionary.
    """
    state = load_state_yaml(state_path)
    if 'raw_data_checksums' not in state:
        state['raw_data_checksums'] = {}

    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return state

    for file_path in raw_data_dir.rglob("*"):
        if file_path.is_file():
          rel_path = str(file_path.relative_to(raw_data_dir))
          checksum = calculate_file_checksum(file_path)
          state['raw_data_checksums'][rel_path] = checksum
          logger.info(f"Recorded checksum for {rel_path}: {checksum[:16]}...")

    save_state_yaml(state_path, state)
    return state

def calculate_linked_metadata_percentage(
    linked_trials_path: Path,
    threshold: float = DEFAULT_LINKED_THRESHOLD
) -> float:
    """
    Calculate the percentage of trials in linked_trials.csv that have valid metadata.
    A trial is considered 'linked' if 'stimulus_id' is not null/empty.
    
    Args:
        linked_trials_path: Path to data/processed/linked_trials.csv
        threshold: The target threshold for 'vast majority' (default 0.95)
        
    Returns:
        The calculated percentage (0.0 to 1.0)
    """
    if not linked_trials_path.exists():
        logger.error(f"Linked trials file not found: {linked_trials_path}")
        return 0.0

    total_trials = 0
    linked_trials = 0

    try:
        with open(linked_trials_path, 'r', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                total_trials += 1
                # Check if stimulus_id exists and is not empty
                stimulus_id = row.get('stimulus_id', '').strip()
                if stimulus_id:
                    linked_trials += 1
    
        if total_trials == 0:
            return 0.0
        
        percentage = linked_trials / total_trials
        return percentage

    except Exception as e:
        logger.error(f"Error calculating linked metadata percentage: {e}")
        return 0.0

def main():
    """
    Main entry point for T018:
    1. Verify checksums of downloaded raw data and record in state.yaml.
    2. Calculate and report the 'linked metadata percentage' against SC-001 target.
    """
    project_root = get_all_base_paths()['project_root']
    state_root = get_path('state')
    raw_data_dir = get_path('raw')
    linked_trials_path = get_path('processed', filename='linked_trials.csv')
    
    # Ensure state directory exists
    state_root.mkdir(parents=True, exist_ok=True)
    state_yaml_path = state_root / 'state.yaml'

    logger.info("=== T018: Checksum Verification & Metadata Linkage Report ===")

    # 1. Verify and record checksums for raw data
    logger.info(f"Verifying checksums for raw data in: {raw_data_dir}")
    if raw_data_dir.exists():
        state = verify_and_record_checksums(state_yaml_path, raw_data_dir)
        logger.info(f"Checksums recorded in {state_yaml_path}")
    else:
        logger.warning(f"Raw data directory missing: {raw_data_dir}. Skipping checksum verification.")

    # 2. Calculate Linked Metadata Percentage
    logger.info(f"Calculating linked metadata percentage from: {linked_trials_path}")
    linked_pct = calculate_linked_metadata_percentage(
        linked_trials_path, 
        threshold=DEFAULT_LINKED_THRESHOLD
    )
    
    # Log the result clearly
    logger.info(f"Linked Metadata Percentage: {linked_pct:.2%}")
    logger.info(f"SC-001 Target (Vast Majority): {DEFAULT_LINKED_THRESHOLD:.2%}")
    
    if linked_pct >= DEFAULT_LINKED_THRESHOLD:
        logger.info(f"SUCCESS: Linkage percentage ({linked_pct:.2%}) meets SC-001 target.")
    else:
        logger.warning(f"FAILURE: Linkage percentage ({linked_pct:.2%}) is BELOW SC-001 target ({DEFAULT_LINKED_THRESHOLD:.2%}).")
        
    return linked_pct

if __name__ == "__main__":
    main()
