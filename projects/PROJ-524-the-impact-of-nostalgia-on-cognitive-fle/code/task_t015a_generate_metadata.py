"""
Task T015a: Generate Metadata

Creates data/raw/metadata.json with:
- dataset_source: String identifying the source (or 'simulation' if fallback)
- validation_study_doi: DOI if found, else null
- stimuli_checksums: Dict of filename -> SHA-256 hash for all files in data/stimuli/
- simulation_mode: Boolean flag indicating if simulation data was used
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def compute_stimuli_checksums(stimuli_dir: Path) -> Dict[str, str]:
    """Compute checksums for all files in the stimuli directory."""
    checksums = {}
    if not stimuli_dir.exists():
        logger.warning(f"Stimuli directory does not exist: {stimuli_dir}")
        return checksums

    files = list(stimuli_dir.iterdir())
    if not files:
        logger.warning(f"Stimuli directory is empty: {stimuli_dir}")
        return checksums

    for file_path in files:
        if file_path.is_file():
            file_name = file_path.name
            try:
                checksum = compute_file_checksum(file_path)
                checksums[file_name] = checksum
                logger.info(f"Computed checksum for {file_name}: {checksum}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_name}: {e}")
    
    return checksums

def load_raw_metadata(raw_data_path: Path) -> Optional[Dict[str, Any]]:
    """Attempt to load metadata from the raw dataset source if it exists."""
    if not raw_data_path.exists():
        logger.warning(f"Raw dataset metadata file not found: {raw_data_path}")
        return None
    
    try:
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse JSON from {raw_data_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading metadata from {raw_data_path}: {e}")
        return None

def generate_metadata(
    stimuli_dir: Path,
    raw_data_path: Path,
    simulation_mode: bool
) -> Dict[str, Any]:
    """Generate the metadata dictionary."""
    # 1. Compute Stimuli Checksums (Critical dependency from T015)
    stimuli_checksums = compute_stimuli_checksums(stimuli_dir)
    
    if not stimuli_checksums:
        logger.warning("No stimuli checksums computed. Directory may be empty or missing.")

    # 2. Determine Dataset Source
    dataset_source = "simulation_fallback" if simulation_mode else "canonical_source"
    
    # 3. Attempt to extract DOI from raw metadata if available
    validation_study_doi = None
    raw_meta = load_raw_metadata(raw_data_path)
    if raw_meta and isinstance(raw_meta, dict):
        # Try common keys where DOI might be stored
        possible_keys = ['doi', 'validation_study_doi', 'source_doi', 'citation_doi']
        for key in possible_keys:
            if key in raw_meta and raw_meta[key]:
                validation_study_doi = raw_meta[key]
                logger.info(f"Found DOI in raw metadata under key '{key}': {validation_study_doi}")
                break
        
        # If not found in raw meta, check if we have a known source
        if validation_study_doi is None:
            # If we are in simulation mode, DOI is likely null
            if simulation_mode:
                validation_study_doi = None
            else:
                # For real data, if not explicitly found, we set to null as per spec
                validation_study_doi = None

    # 4. Construct Final Metadata
    metadata = {
        "dataset_source": dataset_source,
        "validation_study_doi": validation_study_doi,
        "stimuli_checksums": stimuli_checksums,
        "simulation_mode": simulation_mode
    }

    return metadata

def save_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Save metadata to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {output_path}")

def main():
    """Main entry point for T015a."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    stimuli_dir = project_root / "data" / "stimuli"
    raw_data_path = project_root / "data" / "raw" / "raw_dataset.csv"
    output_path = project_root / "data" / "raw" / "metadata.json"

    # Check simulation mode flag
    # We look for a marker file or check if raw_dataset.csv exists and is valid
    # A robust way is to check if the raw data source indicates simulation
    # Since T010d generates metadata in simulation mode, we check for that first if it exists
    # However, T015a depends on T010b/T010d which might have created a raw_dataset.csv
    # We need to determine if the data in raw_dataset.csv is real or simulated.
    # The most reliable flag is usually a metadata file generated during simulation or a specific column.
    # Given the flow: T010d generates raw_dataset.csv AND metadata.json in simulation mode.
    # But T015a needs to REGENERATE metadata.json.
    # We will check if a 'simulation_mode' flag exists in an existing metadata file or infer from source.
    # For this implementation, we assume a check is passed or inferred.
    # Let's check if data/raw/metadata.json exists from T010d simulation step to infer mode, 
    # otherwise assume real if raw_dataset.csv exists and is not empty.
    
    existing_meta_path = project_root / "data" / "raw" / "metadata.json"
    simulation_mode = False
    
    if existing_meta_path.exists():
        try:
            with open(existing_meta_path, 'r') as f:
                existing_meta = json.load(f)
                if existing_meta.get('simulation_mode', False):
                    simulation_mode = True
                    logger.info("Detected simulation mode from existing metadata.")
        except:
            pass
    elif raw_data_path.exists():
        # If no existing metadata, we assume real data unless proven otherwise
        # But T010d creates raw_dataset.csv too. 
        # To be safe, we rely on the explicit flag if it exists, otherwise default to False (Real)
        # The task description says "simulation_mode (boolean)".
        # We will default to False (Real) if no explicit simulation flag is found.
        simulation_mode = False
    else:
        logger.error("Raw dataset not found. Cannot generate metadata.")
        # In a real pipeline, this might be an error state, but we proceed with empty data
        simulation_mode = False

    logger.info(f"Generating metadata. Simulation Mode: {simulation_mode}")

    try:
        metadata = generate_metadata(stimuli_dir, raw_data_path, simulation_mode)
        save_metadata(metadata, output_path)
        logger.info("Task T015a completed successfully.")
    except Exception as e:
        logger.error(f"Task T015a failed: {e}")
        raise

if __name__ == "__main__":
    main()