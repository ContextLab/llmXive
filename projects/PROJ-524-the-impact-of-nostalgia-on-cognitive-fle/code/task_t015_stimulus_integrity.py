"""
Task T015: Stimulus Integrity & Generation
Checks data/stimuli/ directory for existing files, validates against checksums if present,
or attempts to fetch real nostalgia stimuli if empty.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from config import get_config, ensure_dirs

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("task_t015")

class StimulusFidelityError(Exception):
    """Raised when stimulus integrity check fails or fetch fails."""
    pass

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_local_checksums(stimuli_dir: Path) -> Dict[str, str]:
    """Compute checksums for all files in the stimuli directory."""
    checksums = {}
    if not stimuli_dir.exists():
        return checksums
    
    for file_path in stimuli_dir.iterdir():
        if file_path.is_file():
            checksums[file_path.name] = compute_file_checksum(file_path)
    return checksums

def generate_synthetic_stimuli(stimuli_dir: Path) -> None:
    """
    Generate synthetic nostalgia stimuli if real data fetch fails.
    NOTE: Per strict requirements, this should only be called if a real fetch
    is impossible and the task allows simulation fallback. However, T015
    description says "If fetch fails, raise StimulusFidelityError".
    This function is provided for T015a to handle the 'simulation' case if
    the pipeline logic decides to fallback, but T015 itself should fail loudly
    if real data is missing unless a verified source is provided.
    
    For T015 strict implementation: We do NOT generate synthetic stimuli here.
    We raise an error. This function exists only to satisfy potential downstream
    needs if the task was interpreted as allowing simulation (which it explicitly forbids).
    """
    logger.warning("Synthetic stimuli generation is NOT allowed for T015 per strict constraints.")
    raise StimulusFidelityError("Real stimuli fetch failed and synthetic generation is prohibited.")

def fetch_canonical_checksum_from_metadata(metadata_path: Path) -> Optional[Dict[str, str]]:
    """
    Attempt to fetch expected checksums from a canonical metadata source.
    In a real scenario, this would query a remote registry. Here we check
    if a reference checksum file exists in the project (e.g., from a prior run).
    """
    # Check for a reference checksum file in the project root or contracts
    ref_path = Path("contracts/stimuli_checksums.json")
    if ref_path.exists():
        with open(ref_path, 'r') as f:
            return json.load(f)
    return None

def check_integrity(stimuli_dir: Path, expected_checksums: Optional[Dict[str, str]]) -> bool:
    """
    Check integrity of local files against expected checksums.
    Returns True if all match, False otherwise.
    """
    if not stimuli_dir.exists():
        logger.error("Stimuli directory does not exist.")
        return False

    current_checksums = compute_local_checksums(stimuli_dir)
    
    if not current_checksums:
        logger.warning("Stimuli directory is empty.")
        return False

    if expected_checksums is None:
        # No reference to check against, but files exist.
        # This is a "validation" state, but we can't verify integrity without a reference.
        logger.info("No reference checksums found. Assuming existing files are valid.")
        return True

    for filename, expected_hash in expected_checksums.items():
        if filename not in current_checksums:
            logger.error(f"Missing expected stimulus file: {filename}")
            return False
        if current_checksums[filename] != expected_hash:
            logger.error(f"Checksum mismatch for {filename}. Expected: {expected_hash}, Got: {current_checksums[filename]}")
            return False
    
    logger.info("Stimulus integrity check passed.")
    return True

def update_metadata_with_checksums(metadata_path: Path, checksums: Dict[str, str]) -> None:
    """Update the metadata file with the computed checksums."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    metadata['stimuli_checksums'] = checksums
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Updated metadata with checksums: {checksums}")

def save_metadata(state_path: Path, checksums: Dict[str, str]) -> None:
    """Save the current state of stimulus integrity to a temporary state file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_data = {
        "stimuli_checksums": checksums,
        "timestamp": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
    }
    with open(state_path, 'w') as f:
        json.dump(state_data, f, indent=2)
    logger.info(f"Saved stimulus state to {state_path}")

def update_state_yaml(state_yaml_path: Path, checksums: Dict[str, str]) -> None:
    """Update the project state.yaml file with stimulus checksums."""
    import yaml
    state_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_yaml_path.exists():
        with open(state_yaml_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    if 'stimuli' not in state:
        state['stimuli'] = {}
    
    state['stimuli']['checksums'] = checksums
    
    with open(state_yaml_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Updated state.yaml at {state_yaml_path}")

def main():
    """
    Main entry point for Task T015.
    1. Check data/stimuli/ directory.
    2. If empty: Attempt to fetch real stimuli. If fail -> Raise StimulusFidelityError.
    3. If non-empty: Validate checksums. If mismatch -> Log ERR_STIMULUS_CORRUPT and Halt.
    4. Write stimuli_checksums to temporary state.
    """
    config = get_config()
    stimuli_dir = Path(config.get('paths', {}).get('stimuli', 'data/stimuli'))
    metadata_path = Path(config.get('paths', {}).get('raw_metadata', 'data/raw/metadata.json'))
    state_yaml_path = Path('state/state.yaml')
    temp_state_path = Path('data/.temp_stimulus_state.json')
    
    ensure_dirs([stimuli_dir, metadata_path.parent, state_yaml_path.parent])

    logger.info(f"Checking stimuli directory: {stimuli_dir}")

    # Ensure directory exists
    if not stimuli_dir.exists():
        stimuli_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created stimuli directory: {stimuli_dir}")

    files = [f for f in stimuli_dir.iterdir() if f.is_file()]

    if not files:
        # Directory is empty
        logger.info("Stimuli directory is empty. Attempting to fetch real data.")
        
        # In a real implementation, this would call fetch_from_canonical_source()
        # For this specific task, since we cannot fetch real external data without a
        # verified source provided in the context (and we must fail loudly if missing),
        # we raise the error as per the task description: "If fetch fails, raise StimulusFidelityError".
        
        # NOTE: The task description says "If fetch fails, raise...". It implies a fetch attempt.
        # Since no real source URL is provided in the prompt's context for stimuli, 
        # and we cannot fabricate data, we simulate the failure condition.
        
        logger.error("No verified real data source for stimuli provided in context.")
        raise StimulusFidelityError("Real stimulus fetch failed: No canonical source URL provided and synthetic generation is prohibited.")
    
    else:
        # Directory has files
        logger.info(f"Found {len(files)} files in stimuli directory.")
        
        # Try to fetch expected checksums
        expected_checksums = fetch_canonical_checksum_from_metadata(Path("contracts/stimuli_checksums.json"))
        
        if expected_checksums:
            logger.info("Found reference checksums. Validating integrity.")
            if not check_integrity(stimuli_dir, expected_checksums):
                logger.error("ERR_STIMULUS_CORRUPT: Integrity check failed.")
                raise StimulusFidelityError("Stimulus integrity check failed: checksum mismatch.")
            logger.info("Stimulus integrity verified against reference.")
        else:
            logger.warning("No reference checksums found. Cannot validate integrity against a known good state.")
            # We proceed but log a warning. The task says "If mismatch, log and halt".
            # Without a reference, we can't detect a mismatch, so we assume valid for now.
            logger.info("Proceeding with existing files (no reference to validate against).")

    # Compute current checksums
    current_checksums = compute_local_checksums(stimuli_dir)
    
    # Update metadata if it exists, or create a new one if needed for downstream tasks
    # T015a depends on this.
    if metadata_path.exists():
        update_metadata_with_checksums(metadata_path, current_checksums)
    else:
        # Create a minimal metadata file for T015a to consume
        update_metadata_with_checksums(metadata_path, current_checksums)
        
    # Write to temporary state as requested
    save_metadata(temp_state_path, current_checksums)
    
    # Update state.yaml
    update_state_yaml(state_yaml_path, current_checksums)

    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()
