"""
Script to calculate checksums for all downloaded datasets and record them
in the project state YAML file.

This script implements Task T017:
"Calculate checksums for all downloaded datasets and record them ONLY in 
state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml 
artifact_hashes map (Principle III); do NOT write to separate text files"

Usage:
    python scripts/calculate_dataset_checksums.py
"""
import sys
import os
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksum_manager import update_artifact_checksum
from src.utils.logging import log_info, log_error, setup_logger

# Project configuration
PROJECT_ID = "PROJ-088-predicting-reaction-mechanisms-from-spec"

# Define the artifacts to checksum based on the pipeline stages
# These paths are relative to the project root
ARTIFACTS = [
    {
        "name": "nist_raw_data",
        "path": "data/raw/nist_webbook.jsonl",
        "description": "Raw NIST WebBook JSONL data"
    },
    {
        "name": "pubchem_raw_data",
        "path": "data/raw/pubchem_nmr.parquet",
        "description": "Raw PubChem NMR data"
    },
    {
        "name": "preprocessed_data",
        "path": "data/processed/preprocessed_spectra.csv",
        "description": "Preprocessed and binned spectra"
    },
    {
        "name": "literature_db",
        "path": "data/reference/literature_db.json",
        "description": "Literature reference database for DFT validation"
    }
]

def main():
    setup_logger(level="INFO")
    log_info(f"Starting checksum calculation for project: {PROJECT_ID}")
    log_info(f"Project root: {project_root}")

    failed_artifacts = []
    success_count = 0

    for artifact in ARTIFACTS:
        name = artifact["name"]
        relative_path = artifact["path"]
        description = artifact.get("description", "")
        
        full_path = project_root / relative_path
        
        log_info(f"Processing: {name}")
        log_info(f"  Path: {full_path}")
        log_info(f"  Description: {description}")

        if not full_path.exists():
            log_error(f"  SKIP: Artifact not found at {full_path}")
            # We do not fail the whole script if a data file is missing, 
            # as the pipeline might not have run yet. We just log it.
            # However, if the task requires verifying existing downloads, 
            # we might want to be stricter. For now, we log and continue.
            failed_artifacts.append((name, "File not found"))
            continue

        try:
            checksum = update_artifact_checksum(
                artifact_name=name,
                artifact_path=full_path,
                project_root=project_root,
                project_id=PROJECT_ID
            )
            log_info(f"  SUCCESS: Checksum recorded -> {checksum}")
            success_count += 1
        except Exception as e:
            log_error(f"  ERROR: Failed to calculate/update checksum: {e}")
            failed_artifacts.append((name, str(e)))

    log_info("-" * 50)
    log_info(f"Summary: {success_count} artifacts processed successfully.")
    if failed_artifacts:
        log_info(f"Failed to process {len(failed_artifacts)} artifacts:")
        for name, reason in failed_artifacts:
            log_info(f"  - {name}: {reason}")
        # If critical artifacts are missing, we might consider this a failure
        # but for T017, the goal is to record what exists.
    
    log_info(f"State file updated: state/projects/{PROJECT_ID}.yaml")

if __name__ == "__main__":
    main()