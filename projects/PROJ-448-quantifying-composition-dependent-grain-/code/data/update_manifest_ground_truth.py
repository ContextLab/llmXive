import os
import sys
import json
import hashlib
import logging
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import DATA_RAW_PATH, DATA_MANIFEST_PATH
from code.errors import ManifestError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> dict:
    """Load the existing data manifest."""
    if not manifest_path.exists():
        logger.warning(f"Manifest file not found at {manifest_path}. Creating new manifest.")
        return {"sources": []}
    
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ManifestError(f"Failed to parse manifest file: {e}")

def save_manifest(manifest_path: Path, manifest: dict) -> None:
    """Save the updated manifest to disk."""
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved successfully to {manifest_path}")
    except IOError as e:
        raise ManifestError(f"Failed to save manifest file: {e}")

def update_manifest_with_ground_truth(
    manifest: dict, 
    file_path: Path, 
    source_id: str,
    generation_params: dict
) -> dict:
    """
    Update the manifest with the generated ground truth dataset entry.
    
    Args:
        manifest: The current manifest dictionary
        file_path: Path to the generated ground truth file
        source_id: Unique identifier for this data source
        generation_params: Dictionary of parameters used for generation
        
    Returns:
        Updated manifest dictionary
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found at {file_path}")
    
    # Calculate checksum
    checksum = calculate_sha256(file_path)
    logger.info(f"Calculated checksum for {file_path.name}: {checksum}")
    
    # Create new entry
    new_entry = {
        "source_id": source_id,
        "source_type": "generated",
        "file_path": str(file_path.relative_to(project_root)),
        "checksum": checksum,
        "generation_params": generation_params,
        "created_at": str(file_path.stat().st_mtime)
    }
    
    # Check if entry already exists
    existing_entry = next(
        (entry for entry in manifest["sources"] if entry["source_id"] == source_id), 
        None
    )
    
    if existing_entry:
        logger.info(f"Updating existing entry for source_id: {source_id}")
        idx = manifest["sources"].index(existing_entry)
        manifest["sources"][idx] = new_entry
    else:
        logger.info(f"Adding new entry for source_id: {source_id}")
        manifest["sources"].append(new_entry)
    
    return manifest

def main():
    """Main execution function for updating manifest with ground truth."""
    logger.info("Starting manifest update for ground truth dataset")
    
    # Define paths
    ground_truth_file = DATA_RAW_PATH / "generated_ground_truth.csv"
    manifest_path = DATA_MANIFEST_PATH
    
    # Verify ground truth file exists (dependency T091)
    if not ground_truth_file.exists():
        error_msg = f"Ground truth file not found at {ground_truth_file}. " \
                   f"Ensure T091 (execute generate_ground_truth.py) has completed successfully."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Define generation parameters (must match T091 execution)
    # These should ideally be read from the config or the generation script's output
    generation_params = {
        "script": "data/generate_ground_truth.py",
        "task_id": "T090",
        "config_source": "research/synthetic_ground_truth.yaml",
        "mclean_model": True,
        "random_seed": 42,  # Fixed seed as per T090 requirements
        "noise_level": "injected"  # From synthetic_ground_truth.yaml
    }
    
    # Load current manifest
    manifest = load_manifest(manifest_path)
    
    # Update manifest with ground truth entry
    updated_manifest = update_manifest_with_ground_truth(
        manifest=manifest,
        file_path=ground_truth_file,
        source_id="generated_ground_truth",
        generation_params=generation_params
    )
    
    # Save updated manifest
    save_manifest(manifest_path, updated_manifest)
    
    logger.info("Manifest update completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
