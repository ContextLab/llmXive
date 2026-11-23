import os
import sys
import json
import time
import hashlib
import logging
from pathlib import Path

# Import from existing API surfaces
from config import ensure_dirs
from utils import get_logger, save_npy, safe_write_json, log_execution_time, safe_mkdir

def compute_sha256_file(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_provenance_info(
    structural_path: str,
    rsfc_path: str,
    weighted_adj_path: str,
    global_eff_path: str
) -> dict:
    """
    Load provenance metadata for the processed matrices.
    Includes checksums, file sizes, timestamps, and source references.
    """
    provenance = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": {}
    }

    files_to_check = {
        "structural_matrix": structural_path,
        "rsfc_matrix": rsfc_path,
        "weighted_adjacency": weighted_adj_path,
        "global_efficiency": global_eff_path
    }

    for key, path in files_to_check.items():
        if os.path.exists(path):
            stat = os.stat(path)
            checksum = compute_sha256_file(path)
            provenance["sources"][key] = {
                "path": path,
                "size_bytes": stat.st_size,
                "checksum_sha256": checksum,
                "modified_timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)
                )
            }
        else:
            logging.warning(f"Source file not found for provenance: {path}")
            provenance["sources"][key] = {
                "path": path,
                "status": "missing"
            }

    return provenance

def save_with_provenance(
    structural_data: any,
    rsfc_data: any,
    output_dir: str,
    subject_id: str
) -> dict:
    """
    Save structural and rsfc matrices to disk with provenance metadata.
    Also appends provenance details to the pipeline log.
    """
    ensure_dirs([output_dir])

    structural_path = os.path.join(output_dir, f"{subject_id}_structural.npy")
    rsfc_path = os.path.join(output_dir, f"{subject_id}_rsfc.npy")
    provenance_path = os.path.join(output_dir, f"{subject_id}_provenance.json")
    log_path = os.path.join(os.path.dirname(output_dir), "logs", "pipeline.log")

    # Save matrices
    save_npy(structural_data, structural_path)
    save_npy(rsfc_data, rsfc_path)

    # Prepare paths for provenance lookup
    # We assume these are in the same processed directory or standard locations
    # For T017, we rely on T014a/T015 having written to data/processed/
    processed_dir = os.path.dirname(structural_path)
    weighted_adj_path = os.path.join(processed_dir, "weighted_adjacency.npy")
    global_eff_path = os.path.join(processed_dir, "global_efficiency.json")

    # Load provenance info
    provenance = load_provenance_info(
        structural_path,
        rsfc_path,
        weighted_adj_path,
        global_eff_path
    )
    provenance["subject_id"] = subject_id

    # Save provenance JSON
    safe_write_json(provenance, provenance_path)

    # Append to pipeline log
    logger = get_logger("pipeline")
    logger.info(f"Saved outputs for subject {subject_id}")
    logger.info(f"Structural matrix: {structural_path} (SHA256: {provenance['sources']['structural_matrix']['checksum_sha256']})")
    logger.info(f"RSFC matrix: {rsfc_path} (SHA256: {provenance['sources']['rsfc_matrix']['checksum_sha256']})")
    logger.info(f"Provenance metadata saved to: {provenance_path}")

    return {
        "structural_path": structural_path,
        "rsfc_path": rsfc_path,
        "provenance_path": provenance_path,
        "provenance": provenance
    }

def main():
    """
    Entry point for saving processed matrices with provenance.
    This script is intended to be called after T014a and T015 have generated
    the weighted adjacency and rsFC data.
    """
    logger = get_logger("pipeline")
    logger.info("Starting T017: Save processed matrices with provenance")

    # Configuration
    processed_dir = "data/processed"
    subject_id = "test_subject" # In real execution, this would be iterated or passed

    # For demonstration, we assume the existence of data from T014a and T015
    # In a real pipeline, these would be passed as arguments or loaded from context
    structural_path = os.path.join(processed_dir, "weighted_adjacency.npy")
    rsfc_path = os.path.join(processed_dir, "rsfc.npy")

    if not os.path.exists(structural_path):
        logger.error(f"Required input file missing: {structural_path}")
        return 1

    if not os.path.exists(rsfc_path):
        logger.error(f"Required input file missing: {rsfc_path}")
        return 1

    try:
        import numpy as np
        structural_data = np.load(structural_path)
        rsfc_data = np.load(rsfc_path)

        result = save_with_provenance(
            structural_data,
            rsfc_data,
            processed_dir,
            subject_id
        )

        logger.info(f"T017 completed successfully. Output: {result['structural_path']}")
        return 0

    except Exception as e:
        logger.error(f"Error in T017: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
