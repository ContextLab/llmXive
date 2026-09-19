"""
T015: Stimulus Integrity Verification and Generation

Reads simulation_mode from data/raw/metadata.json.
If simulation_mode=True: Generates synthetic stimuli, computes checksums, updates metadata.
If simulation_mode=False: Validates existing stimuli against metadata checksums.
Updates state/state.yaml with artifact_hashes upon success.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from utils import setup_logging, log_info, log_warning, log_error, log_critical, compute_sha256, get_timestamp
from config import get_config, ensure_dirs

# Constants
STIMULI_DIR = "data/stimuli"
METADATA_PATH = "data/raw/metadata.json"
STATE_PATH = "state/state.yaml"

# Synthetic stimuli content definitions (deterministic)
SYNTHETIC_STIMULI = {
    "nostalgia_prompt.txt": "Please recall a specific personal event that evokes strong feelings of nostalgia. Describe the sensory details (sights, sounds, smells) and the emotions you felt during that time.",
    "control_prompt.txt": "Please recall a specific personal event that occurred recently (within the last month). Describe the sensory details (sights, sounds, smells) and the emotions you felt during that time.",
    "instructions.txt": "This study investigates the impact of nostalgia on cognitive flexibility. Participants will be randomly assigned to either a nostalgia recall condition or a control condition."
}

def fetch_canonical_checksum_from_metadata(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Fetch expected checksums from metadata if available."""
    return metadata.get("stimuli_checksums")

def compute_local_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    return compute_sha256(file_path)

def generate_synthetic_stimuli(stimuli_dir: Path) -> Dict[str, str]:
    """Generate synthetic stimuli files if none exist."""
    log_info("Generating synthetic stimuli files...")
    checksums = {}
    
    for filename, content in SYNTHETIC_STIMULI.items():
        file_path = stimuli_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        checksums[filename] = compute_local_checksum(file_path)
        log_info(f"Generated stimulus: {filename}")
    
    return checksums

def check_integrity(stimuli_dir: Path, expected_checksums: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Check integrity of local stimuli against expected checksums."""
    errors = []
    stimuli_path = Path(stimuli_dir)
    
    # Check for missing files
    for filename in expected_checksums.keys():
        file_path = stimuli_path / filename
        if not file_path.exists():
            errors.append(f"ERR_STIMULUS_MISSING: {filename}")
            log_error(f"Missing stimulus file: {filename}")
    
    # Check for checksum mismatches
    for filename, expected_hash in expected_checksums.items():
        file_path = stimuli_path / filename
        if file_path.exists():
            actual_hash = compute_local_checksum(file_path)
            if actual_hash != expected_hash:
                errors.append(f"ERR_STIMULUS_CORRUPT: {filename} (expected: {expected_hash}, got: {actual_hash})")
                log_error(f"Stimulus corruption detected: {filename}")
        
        # Check for extra files not in metadata
        for file_path in stimuli_path.iterdir():
            if file_path.is_file() and file_path.name not in expected_checksums:
                log_warning(f"Extra stimulus file found: {file_path.name} (not in metadata)")
    
    return len(errors) == 0, errors

def update_metadata_with_checksums(metadata: Dict[str, Any], checksums: Dict[str, str]) -> Dict[str, Any]:
    """Update metadata dictionary with new checksums."""
    metadata["stimuli_checksums"] = checksums
    metadata["timestamp"] = get_timestamp()
    return metadata

def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """Save updated metadata to JSON file."""
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Updated metadata saved to {metadata_path}")

def update_state_yaml(state_path: Path, stimulus_checksums: Dict[str, str]) -> None:
    """Update state/state.yaml with stimulus checksums."""
    import yaml
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f) or {}
    
    # Ensure artifact_hashes exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Update stimulus checksums
    state_data["artifact_hashes"]["stimuli"] = stimulus_checksums
    state_data["last_updated"] = get_timestamp()
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    log_info(f"State updated with stimulus checksums in {state_path}")

def main() -> int:
    """Main entry point for T015 stimulus integrity task."""
    setup_logging()
    config = get_config()
    
    stimuli_dir = Path(STIMULI_DIR)
    metadata_path = Path(METADATA_PATH)
    state_path = Path(STATE_PATH)
    
    # Ensure directories exist
    ensure_dirs([STIMULI_DIR, "state"])
    
    # Load metadata
    if not metadata_path.exists():
        log_critical(f"Metadata file not found: {metadata_path}")
        return 1
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    simulation_mode = metadata.get("simulation_mode", False)
    log_info(f"Simulation mode: {simulation_mode}")
    
    if simulation_mode:
        # Generate synthetic stimuli if none exist
        existing_files = list(stimuli_dir.glob("*"))
        if not existing_files:
            log_info("No stimuli found, generating synthetic stimuli...")
            checksums = generate_synthetic_stimuli(stimuli_dir)
            log_info("INFO_SIMULATED_STIMULI_GENERATED")
        else:
            # Compute checksums of existing synthetic stimuli
            checksums = {}
            for file_path in stimuli_dir.iterdir():
                if file_path.is_file():
                    checksums[file_path.name] = compute_local_checksum(file_path)
        
        # Update metadata with checksums
        metadata = update_metadata_with_checksums(metadata, checksums)
        save_metadata(metadata, metadata_path)
        
        # Update state
        update_state_yaml(state_path, checksums)
        log_info("Stimulus integrity verified (synthetic mode)")
        
    else:
        # Real mode: validate existing stimuli
        expected_checksums = fetch_canonical_checksum_from_metadata(metadata)
        
        if not expected_checksums:
            log_warning("WARN_STIMULUS_NO_CHECKSUMS_IN_METADATA")
            # If no checksums in metadata, we can't validate - this is an error condition for real data
            log_error("ERR_STIMULUS_CORRUPT: No checksums found in metadata for validation")
            return 1
        
        # Check integrity
        is_valid, errors = check_integrity(stimuli_dir, expected_checksums)
        
        if not is_valid:
            log_error(f"Stimulus integrity check failed: {errors}")
            return 1
        
        # Update state with validated checksums
        update_state_yaml(state_path, expected_checksums)
        log_info("Stimulus integrity verified (real data mode)")
    
    return 0

if __name__ == "__main__":
    exit(main())
