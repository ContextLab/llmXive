"""
Hashing and Checksum Management Module.

This module provides utilities for calculating SHA-256 checksums of artifacts,
verifying data integrity, and maintaining a persistent state file (pipeline_state.yaml)
that tracks the checksums of all processed data files.

It implements the "Constitution Principle V" by ensuring every data transformation
is recorded and verifiable.
"""

import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

# Import from local config to ensure path consistency
# We use a relative import pattern that works when run as a module or script
try:
    from code.config import get_path
except ImportError:
    # Fallback for direct execution or different import context
    from config import get_path

# Configure logging
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def update_state_yaml(state_file: str, artifact_name: str, checksum: str) -> None:
    """
    Update the pipeline state YAML file with a new artifact checksum.

    Args:
        state_file: Path to the state YAML file.
        artifact_name: Name/identifier of the artifact.
        checksum: SHA-256 checksum of the artifact.
    """
    state_path = Path(state_file)
    
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            logger.warning(f"Corrupt state file {state_file}, resetting.")
            state = {}
    else:
        state = {}
    
    # Ensure 'artifact_hashes' key exists
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    # Update checksum
    state['artifact_hashes'][artifact_name] = {
        'checksum': checksum,
        'updated_at': str(Path(file_path).stat().st_mtime) if (file_path := state.get('_temp_path_map', {}).get(artifact_name)) else 'unknown'
    }
    
    # Clean up temp map if exists
    if '_temp_path_map' in state:
        del state['_temp_path_map']
    
    # Write back
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state: {artifact_name} -> {checksum[:16]}...")

def verify_artifact(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = calculate_sha256(file_path)
        return actual_checksum == expected_checksum
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return False

def checksum_derived_datasets(
    files: List[str],
    state_file: Optional[str] = None,
    base_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Calculate checksums for a list of derived data files and update the state file.

    Args:
        files: List of relative or absolute file paths to checksum.
        state_file: Optional path to the state YAML file. Defaults to state/pipeline_state.yaml.
        base_dir: Optional base directory if files are relative.

    Returns:
        Dictionary mapping artifact names to their checksums.
    """
    results = {}
    
    if state_file is None:
        state_file = str(get_path("state", "pipeline_state.yaml"))
    
    for file_path in files:
        # Resolve full path if relative
        if base_dir and not os.path.isabs(file_path):
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path
        
        artifact_name = os.path.basename(file_path)
        
        try:
            checksum = calculate_sha256(full_path)
            results[artifact_name] = checksum
            logger.debug(f"Checksummed {artifact_name}: {checksum[:16]}...")
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping {file_path}: {e}")
            continue
    
    # Update state file if we have results
    if results:
        try:
            # We need to load the state, update it, and save it.
            # Since update_state_yaml handles the file I/O, we iterate.
            for name, cksum in results.items():
                update_state_yaml(state_file, name, cksum)
        except Exception as e:
            logger.error(f"Failed to update state file: {e}")
    
    return results

def update_state_checksums(
    files: List[str],
    state_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Main entry point for checksumming simulation-derived CSVs and updating state.
    This function is specifically designed to satisfy T018 requirements.

    Args:
        files: List of file paths (relative to project root or absolute) to checksum.
        state_file: Optional path to state file. Defaults to 'state/pipeline_state.yaml'.

    Returns:
        Dictionary of artifact names to checksums.
    """
    # Resolve state file path if not provided
    if state_file is None:
        state_file = str(get_path("state", "pipeline_state.yaml"))
    
    # Ensure state directory exists
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate checksums
    return checksum_derived_datasets(files, state_file=state_file)

def main():
    """
    Main execution for command-line usage.
    Expects file paths as arguments.
    """
    # Example usage for testing
    logger.info("Running hashing module main()...")
    
    # Get state file path using the robust get_path helper
    state_file = str(get_path("state", "pipeline_state.yaml"))
    
    # Define a list of potential simulation outputs to checksum
    # In a real run, these would be passed as arguments or read from a manifest
    potential_files = [
        "data/raw/synthetic_mfq.csv",
        "data/raw/synthetic_stories.csv",
        "data/raw/synthetic_vr_logs.csv",
        "data/processed/merged_data.csv",
        "data/processed/preprocessed_data.csv",
        "data/processed/model_results.json"
    ]
    
    # Filter to existing files
    existing_files = [f for f in potential_files if os.path.exists(f)]
    
    if not existing_files:
        logger.warning("No simulation-derived files found to checksum.")
        # Create a minimal state file to indicate the run happened
        if not os.path.exists(state_file):
            with open(state_file, 'w') as f:
                yaml.dump({'artifact_hashes': {}, 'run_status': 'no_files_found'}, f)
        return {}
    
    logger.info(f"Checksumming {len(existing_files)} files...")
    results = update_state_checksums(existing_files, state_file=state_file)
    
    logger.info(f"Checksumming complete. Results: {list(results.keys())}")
    return results

if __name__ == "__main__":
    main()