"""
Task T015: Stimulus Integrity & Generation

Checks the data/stimuli/ directory.
- If empty: Generates valid placeholder stimuli (text files with checksums) to satisfy Constitution Principle VI.
- If non-empty: Validates existing files against metadata checksums (if available).
- Computes SHA-256 checksums for all files in data/stimuli/.
- Writes stimuli_checksums to a temporary state (to be read by T015a).
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Import utilities from existing modules
try:
    from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    from datetime import datetime

    def setup_logging(level=logging.INFO):
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    def log_info(msg):
        logging.info(msg)

    def log_warning(msg):
        logging.warning(msg)

    def log_error(msg):
        logging.error(msg)

    def get_timestamp():
        return datetime.now().isoformat()


def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        log_error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        log_error(f"Error computing checksum for {file_path}: {e}")
        raise


def compute_local_checksums(stimuli_dir: Path) -> Dict[str, str]:
    """
    Computes checksums for all files in the stimuli directory.

    Args:
        stimuli_dir: Path to the stimuli directory.

    Returns:
        Dictionary mapping filename to SHA-256 checksum.
    """
    checksums = {}
    if not stimuli_dir.exists():
        log_warning(f"Stimuli directory does not exist: {stimuli_dir}")
        return checksums

    for file_path in stimuli_dir.iterdir():
        if file_path.is_file():
            checksum = compute_file_checksum(file_path)
            checksums[file_path.name] = checksum
            log_info(f"Computed checksum for {file_path.name}: {checksum}")

    return checksums


def generate_synthetic_stimuli(stimuli_dir: Path) -> Dict[str, str]:
    """
    Generates placeholder stimuli files if the directory is empty.
    Creates text files with deterministic content to ensure reproducibility.

    Args:
        stimuli_dir: Path to the stimuli directory.

    Returns:
        Dictionary mapping filename to SHA-256 checksum.
    """
    log_info(f"Stimuli directory is empty or missing. Generating placeholder stimuli in {stimuli_dir}.")
    stimuli_dir.mkdir(parents=True, exist_ok=True)

    # Define placeholder stimuli content
    # Nostalgia condition
    nostalgia_content = (
        "Nostalgia Induction Script: \n"
        "Please recall a specific moment from your past that you feel nostalgic about. "
        "Think about the sights, sounds, and feelings associated with that memory. "
        "Focus on the warmth and comfort of that time. (Duration: 2 minutes)"
    )
    
    # Control condition
    control_content = (
        "Control Induction Script: \n"
        "Please recall a specific moment from your past that is neutral in emotional tone. "
        "Think about the facts of what happened, without focusing on feelings. "
        "Describe the sequence of events objectively. (Duration: 2 minutes)"
    )

    files_created = {}

    # Create nostalgia stimulus
    nostalgia_path = stimuli_dir / "nostalgia_induction.txt"
    with open(nostalgia_path, "w", encoding="utf-8") as f:
        f.write(nostalgia_content)
    files_created["nostalgia_induction.txt"] = compute_file_checksum(nostalgia_path)

    # Create control stimulus
    control_path = stimuli_dir / "control_induction.txt"
    with open(control_path, "w", encoding="utf-8") as f:
        f.write(control_content)
    files_created["control_induction.txt"] = compute_file_checksum(control_path)

    log_info(f"Generated {len(files_created)} placeholder stimuli files.")
    return files_created


def fetch_canonical_checksum_from_metadata(metadata_path: Path) -> Optional[Dict[str, str]]:
    """
    Attempts to fetch canonical checksums from a metadata file if it exists.

    Args:
        metadata_path: Path to the metadata file.

    Returns:
        Dictionary of checksums if found, None otherwise.
    """
    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata.get("stimuli_checksums")
    except Exception as e:
        log_warning(f"Could not load canonical checksums from {metadata_path}: {e}")
        return None


def check_integrity(local_checksums: Dict[str, str], canonical_checksums: Optional[Dict[str, str]]) -> bool:
    """
    Compares local checksums against canonical checksums.

    Args:
        local_checksums: Checksums computed from local files.
        canonical_checksums: Checksums from metadata (if available).

    Returns:
        True if integrity is verified or no canonical checksums exist.
        False if mismatch found.
    """
    if not canonical_checksums:
        log_info("No canonical checksums found to verify against. Integrity check skipped (or passed by default).")
        return True

    if set(local_checksums.keys()) != set(canonical_checksums.keys()):
        log_error("Stimulus file mismatch: Local files do not match canonical list.")
        return False

    for filename, local_hash in local_checksums.items():
        canonical_hash = canonical_checksums.get(filename)
        if canonical_hash and local_hash != canonical_hash:
            log_error(f"Checksum mismatch for {filename}: Local={local_hash}, Canonical={canonical_hash}")
            return False

    log_info("Stimulus integrity verified successfully.")
    return True


def update_metadata_with_checksums(metadata_path: Path, checksums: Dict[str, str]) -> None:
    """
    Updates or creates a metadata file with the computed checksums.

    Args:
        metadata_path: Path to the metadata file.
        checksums: Dictionary of filename to checksum.
    """
    metadata = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            log_warning(f"Could not read existing metadata: {e}")

    metadata["stimuli_checksums"] = checksums
    metadata["stimuli_integrity_timestamp"] = get_timestamp()

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    log_info(f"Updated metadata with checksums at {metadata_path}")


def save_metadata(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Saves the checksums to a temporary state file for T015a to read.

    Args:
        checksums: Dictionary of filename to checksum.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"stimuli_checksums": checksums, "timestamp": get_timestamp()}, f, indent=2)
    log_info(f"Saved stimuli checksums to {output_path}")


def update_state_yaml(checksums: Dict[str, str], state_path: Path) -> None:
    """
    Updates the state.yaml file with the new checksums (if yaml module is available).
    Since yaml is in requirements, we can try to import it.

    Args:
        checksums: Dictionary of filename to checksum.
        state_path: Path to the state.yaml file.
    """
    try:
        import yaml
    except ImportError:
        log_warning("PyYAML not installed. Skipping state.yaml update.")
        return

    state = {}
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}
        except Exception as e:
            log_warning(f"Could not read state.yaml: {e}")

    state["stimuli_checksums"] = checksums
    state["last_stimulus_check"] = get_timestamp()

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False)
    
    log_info(f"Updated state.yaml at {state_path}")


def main():
    """
    Main entry point for Task T015.
    """
    setup_logging()
    
    # Define paths
    root_dir = Path(__file__).resolve().parent.parent
    stimuli_dir = root_dir / "data" / "stimuli"
    metadata_path = root_dir / "data" / "raw" / "metadata.json"
    temp_state_path = root_dir / "data" / "raw" / "stimuli_checksums_temp.json"
    state_yaml_path = root_dir / "state" / "state.yaml"

    log_info("Starting Task T015: Stimulus Integrity & Generation")

    # Ensure stimuli directory exists
    stimuli_dir.mkdir(parents=True, exist_ok=True)

    # Check if directory is empty
    files_in_dir = list(stimuli_dir.iterdir())
    existing_files = [f for f in files_in_dir if f.is_file()]

    if not existing_files:
        log_info("Stimuli directory is empty. Generating placeholder stimuli.")
        checksums = generate_synthetic_stimuli(stimuli_dir)
    else:
        log_info(f"Found {len(existing_files)} existing files in stimuli directory.")
        # Compute local checksums
        checksums = compute_local_checksums(stimuli_dir)

        # Fetch canonical checksums if available
        canonical_checksums = fetch_canonical_checksum_from_metadata(metadata_path)
        
        # Verify integrity
        if not check_integrity(checksums, canonical_checksums):
            log_error("Stimulus integrity check failed. Halting.")
            # In a strict pipeline, we might exit here. 
            # For this task, we log the error and proceed to save what we have,
            # but the pipeline orchestrator should handle the failure.
            # However, per task description: "If mismatch, log ERR_STIMULUS_CORRUPT and halt."
            # We will raise an exception to halt the process.
            raise RuntimeError("Stimulus integrity check failed.")

    # Save checksums to temporary state for T015a
    save_metadata(checksums, temp_state_path)

    # Update state.yaml if possible
    update_state_yaml(checksums, state_yaml_path)

    # Also update the main metadata.json if it exists or create it
    # T015a will read this, so we ensure it's there or at least the temp file is.
    # The task says "Write stimuli_checksums ... to a temporary state."
    # T015a then reads that.
    
    log_info("Task T015 completed successfully.")
    return checksums


if __name__ == "__main__":
    main()