import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

import numpy as np

# Import from utils as per API surface
from utils import get_logger, safe_mkdir, safe_write_json, save_npy, load_npy, compute_sha256
from config import ensure_dirs

def compute_sha256_file(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_provenance_info() -> dict:
    """Load existing provenance info or initialize a new record."""
    # This function assumes a state file might exist, but for T017
    # we are generating the initial record based on the current run.
    return {
        "created_at": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "task_id": "T017",
        "dependencies": ["T014", "T015"]
    }

def save_with_provenance(data: np.ndarray, output_path: str, matrix_type: str, logger):
    """
    Save a numpy array to disk and generate a provenance metadata file.
    
    Args:
        data: The numpy array to save.
        output_path: The full path where the .npy file will be saved.
        matrix_type: A string identifier (e.g., 'structural', 'rsfc').
        logger: The logger instance to use.
    """
    safe_mkdir(os.path.dirname(output_path))
    
    # Save the matrix
    save_npy(data, output_path)
    logger.info(f"Saved {matrix_type} matrix to {output_path}")
    
    # Compute checksum
    checksum = compute_sha256_file(output_path)
    logger.info(f"Computed SHA256 for {output_path}: {checksum}")
    
    # Prepare provenance metadata
    provenance = load_provenance_info()
    provenance["artifact_name"] = os.path.basename(output_path)
    provenance["matrix_type"] = matrix_type
    provenance["shape"] = list(data.shape)
    provenance["dtype"] = str(data.dtype)
    provenance["checksum"] = checksum
    provenance["file_size_bytes"] = os.path.getsize(output_path)
    
    # Save metadata as JSON next to the file
    json_path = output_path.replace('.npy', '_provenance.json')
    safe_write_json(provenance, json_path)
    logger.info(f"Saved provenance metadata to {json_path}")

def main():
    """
    Main entry point for T017: Save processed matrices with provenance.
    
    Loads the weighted adjacency matrix (structural) and rsfc matrix computed in T014/T015,
    and saves them to data/processed/ with accompanying provenance metadata.
    """
    logger = get_logger("save_outputs")
    logger.info("Starting T017: Save processed matrices with provenance metadata")
    
    # Ensure directories exist
    ensure_dirs()
    
    processed_dir = Path("data/processed")
    
    # Define input paths based on T014 and T015 outputs
    # T014 produces: data/processed/weighted_adjacency.npy (structural)
    # T015 produces: data/processed/rsfc.npy
    structural_input = processed_dir / "weighted_adjacency.npy"
    rsfc_input = processed_dir / "rsfc.npy"
    
    # Define output paths
    structural_output = processed_dir / "structural.npy"
    rsfc_output = processed_dir / "rsfc.npy"
    
    # Load Structural Matrix (from T014)
    if not structural_input.exists():
        logger.error(f"Input file missing: {structural_input}")
        logger.error("T014 (preprocess) must complete successfully before T017 can run.")
        raise FileNotFoundError(f"Missing structural matrix: {structural_input}")
    
    logger.info(f"Loading structural matrix from {structural_input}")
    structural_data = load_npy(str(structural_input))
    
    # Save Structural Matrix with Provenance
    save_with_provenance(structural_data, str(structural_output), "structural", logger)
    
    # Load RSFC Matrix (from T015)
    if not rsfc_input.exists():
        logger.error(f"Input file missing: {rsfc_input}")
        logger.error("T015 (preprocess rsfc) must complete successfully before T017 can run.")
        raise FileNotFoundError(f"Missing rsfc matrix: {rsfc_input}")
    
    logger.info(f"Loading rsfc matrix from {rsfc_input}")
    rsfc_data = load_npy(str(rsfc_input))
    
    # Save RSFC Matrix with Provenance
    # Note: We overwrite rsfc.npy to ensure it is the "saved with provenance" version
    # or we could name it rsfc_final.npy. The task asks to save to data/processed/rsfc.npy.
    # Since rsfc_input IS data/processed/rsfc.npy, we are essentially re-saving it with metadata.
    save_with_provenance(rsfc_data, str(rsfc_output), "rsfc", logger)
    
    logger.info("T017 completed successfully. Artifacts saved with provenance.")

if __name__ == "__main__":
    main()
