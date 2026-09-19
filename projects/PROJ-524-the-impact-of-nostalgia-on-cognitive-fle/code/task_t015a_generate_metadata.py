import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config

def compute_stimuli_checksums(stimuli_dir: Path) -> Optional[Dict[str, str]]:
    """
    Compute SHA-256 checksums for all files in the stimuli directory.
    Returns None if the directory is empty or does not exist.
    """
    if not stimuli_dir.exists():
        log_warning(f"Stimuli directory does not exist: {stimuli_dir}")
        return None

    files = list(stimuli_dir.iterdir())
    # Filter out hidden files and directories
    files = [f for f in files if not f.name.startswith('.')]

    if not files:
        log_info("INFO_SIMULATION_NO_STIMULI: Stimuli directory is empty.")
        return None

    checksums = {}
    for file_path in files:
        if file_path.is_file():
            sha256_hash = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                checksums[file_path.name] = sha256_hash.hexdigest()
            except Exception as e:
                log_error(f"Failed to compute checksum for {file_path}: {e}")
                raise

    return checksums

def load_raw_metadata(raw_data_path: Path) -> Dict[str, Any]:
    """
    Load the raw metadata from the data fetch step.
    This is expected to exist from T010b.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw metadata file not found: {raw_data_path}. "
                                "T010b (Data Ingestion) must run before T015a.")
    
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the final metadata.json for the raw data directory.
    """
    data_root = Path(config.get('data_root', 'data'))
    raw_dir = data_root / 'raw'
    stimuli_dir = data_root / 'stimuli'
    
    # Load existing metadata from T010b if available, otherwise create base
    metadata_path = raw_dir / 'metadata.json'
    base_metadata = {}
    if metadata_path.exists():
        base_metadata = load_raw_metadata(metadata_path)
    
    # Determine dataset source
    dataset_source = base_metadata.get('dataset_source', 'Unknown')
    
    # Determine validation_study_doi
    # Try to extract from source metadata if available, otherwise set to null
    validation_study_doi = base_metadata.get('validation_study_doi')
    if validation_study_doi is None:
        log_warning("WARN_NO_DOI_FOUND: validation_study_doi not found in source metadata. Setting to null.")
    
    # Compute stimuli checksums
    stimuli_checksums = compute_stimuli_checksums(stimuli_dir)
    
    # Determine simulation_mode
    # If base_metadata has simulation_mode, use it. Otherwise, default to False.
    simulation_mode = base_metadata.get('simulation_mode', False)
    
    # If simulation_mode is True and stimuli_checksums is None (empty dir), log info
    if simulation_mode and stimuli_checksums is None:
        log_info("INFO_SIMULATION_NO_STIMULI: Simulation mode is active but no stimuli files found.")
    
    # Construct final metadata
    final_metadata = {
        "dataset_source": dataset_source,
        "validation_study_doi": validation_study_doi,
        "stimuli_checksums": stimuli_checksums,
        "simulation_mode": simulation_mode,
        "timestamp": get_timestamp()
    }
    
    # Include raw_record_count and valid_record_count if they exist in base
    if 'raw_record_count' in base_metadata:
        final_metadata['raw_record_count'] = base_metadata['raw_record_count']
    if 'valid_record_count' in base_metadata:
        final_metadata['valid_record_count'] = base_metadata['valid_record_count']
        
    return final_metadata

def save_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Save the generated metadata to the specified path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Metadata saved to {output_path}")

def main():
    """
    Main entry point for T015a: Generate Metadata.
    """
    setup_logging()
    config = get_config()
    
    try:
        metadata = generate_metadata(config)
        data_root = Path(config.get('data_root', 'data'))
        output_path = data_root / 'raw' / 'metadata.json'
        save_metadata(metadata, output_path)
        log_info("T015a completed successfully.")
    except FileNotFoundError as e:
        log_error(f"Critical error: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during metadata generation: {e}")
        raise

if __name__ == "__main__":
    main()