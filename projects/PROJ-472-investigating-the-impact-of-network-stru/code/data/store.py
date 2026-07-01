"""
Unified data store script for saving participant-indexed structural matrices
and cleaned (filtered) EEG time-series.

This script aggregates outputs from the dMRI preprocessing (structural connectomes)
and EEG simulation (filtered time-series) pipelines, saving them in a structured
format for downstream analysis (US2).

Output files are saved to:
  - data/processed/connectomes/{subject_id}_connectome.npy
  - data/processed/eeg/{subject_id}_eeg_cleaned.npy
  - data/results/store_manifest.json (metadata about stored files)
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import from local project modules
from config import ensure_directories, get_data_root
from data.models import Participant, StructuralConnectome
from data.quality_control import run_qc_for_subject, generate_qc_report, calculate_pipeline_completeness
from utils.data_setup import compute_file_checksum, save_checksums, load_checksums
from utils.logger import get_logger

logger = get_logger(__name__)


def load_connectome_matrix(subject_id: str, data_root: Path) -> Optional[np.ndarray]:
    """
    Load the processed adjacency matrix for a given subject.
    Expects file at: data/processed/connectomes/{subject_id}_connectome.npy
    """
    file_path = data_root / "processed" / "connectomes" / f"{subject_id}_connectome.npy"
    if not file_path.exists():
        logger.warning(f"Connectome file not found for {subject_id}: {file_path}")
        return None
    
    try:
        matrix = np.load(file_path)
        logger.info(f"Loaded connectome matrix for {subject_id} with shape {matrix.shape}")
        return matrix
    except Exception as e:
        logger.error(f"Failed to load connectome for {subject_id}: {e}")
        return None


def load_eeg_time_series(subject_id: str, data_root: Path) -> Optional[np.ndarray]:
    """
    Load the cleaned (filtered) EEG time-series for a given subject.
    Expects file at: data/processed/eeg/{subject_id}_eeg_cleaned.npy
    Format: (n_channels, n_timepoints)
    """
    file_path = data_root / "processed" / "eeg" / f"{subject_id}_eeg_cleaned.npy"
    if not file_path.exists():
        logger.warning(f"Cleaned EEG file not found for {subject_id}: {file_path}")
        return None
    
    try:
        eeg_data = np.load(file_path)
        logger.info(f"Loaded cleaned EEG for {subject_id} with shape {eeg_data.shape}")
        return eeg_data
    except Exception as e:
        logger.error(f"Failed to load cleaned EEG for {subject_id}: {e}")
        return None


def store_structural_connectome(subject_id: str, matrix: np.ndarray, data_root: Path) -> str:
    """
    Save a structural connectome matrix to disk with checksum tracking.
    Returns the relative path of the saved file.
    """
    output_dir = data_root / "processed" / "connectomes"
    ensure_directories([output_dir])
    
    file_path = output_dir / f"{subject_id}_connectome.npy"
    np.save(file_path, matrix)
    
    checksum = compute_file_checksum(file_path)
    logger.info(f"Saved structural connectome for {subject_id} to {file_path} (checksum: {checksum[:8]}...)")
    return str(file_path.relative_to(data_root))


def store_cleaned_eeg(subject_id: str, eeg_data: np.ndarray, data_root: Path) -> str:
    """
    Save cleaned (filtered) EEG time-series to disk with checksum tracking.
    Returns the relative path of the saved file.
    """
    output_dir = data_root / "processed" / "eeg"
    ensure_directories([output_dir])
    
    file_path = output_dir / f"{subject_id}_eeg_cleaned.npy"
    np.save(file_path, eeg_data)
    
    checksum = compute_file_checksum(file_path)
    logger.info(f"Saved cleaned EEG for {subject_id} to {file_path} (checksum: {checksum[:8]}...)")
    return str(file_path.relative_to(data_root))


def run_store_pipeline(subject_ids: List[str], data_root: Optional[Path] = None) -> Dict:
    """
    Main entry point to store processed data for a list of subjects.
    
    This function:
    1. Validates that QC has been passed for each subject (skips failed subjects).
    2. Loads structural matrices and cleaned EEG data from intermediate locations.
    3. Saves them to the final organized structure in data/processed.
    4. Generates a manifest of stored files.
    
    Args:
        subject_ids: List of subject identifiers to process.
        data_root: Optional override for data root path. Defaults to config.get_data_root().
        
    Returns:
        Dictionary containing:
          - 'stored_subjects': List of successfully stored subject IDs
          - 'failed_subjects': List of subject IDs that failed storage
          - 'manifest_path': Path to the generated manifest file
    """
    if data_root is None:
        data_root = get_data_root()
    
    results = {
        "stored_subjects": [],
        "failed_subjects": [],
        "files": {},
        "manifest_path": ""
    }
    
    # Load existing QC report to filter out failed subjects
    # Assuming QC report is generated at data/results/qc_report.csv by T012
    qc_report_path = data_root / "results" / "qc_report.csv"
    passed_subjects = set()
    
    if qc_report_path.exists():
        qc_df = pd.read_csv(qc_report_path)
        # Filter for subjects that passed all checks (assuming 'passed' column exists)
        # If 'passed' is boolean or 1/0
        if 'passed' in qc_df.columns:
            passed_subjects = set(qc_df[qc_df['passed'] == True]['subject_id'].tolist())
        else:
            # Fallback: assume all listed in report passed if column missing
            passed_subjects = set(qc_df['subject_id'].tolist())
        logger.info(f"Loaded QC report. {len(passed_subjects)} subjects passed QC.")
    else:
        logger.warning("QC report not found. Proceeding with all subjects, assuming they passed.")
        passed_subjects = set(subject_ids)
    
    manifest_entries = []
    
    for subject_id in subject_ids:
        if subject_id not in passed_subjects:
            logger.info(f"Skipping {subject_id}: failed QC checks.")
            results["failed_subjects"].append(subject_id)
            continue
        
        try:
            # Load structural connectome
            conn_matrix = load_connectome_matrix(subject_id, data_root)
            if conn_matrix is None:
                logger.error(f"Cannot store {subject_id}: missing connectome data.")
                results["failed_subjects"].append(subject_id)
                continue
            
            # Load cleaned EEG
            eeg_data = load_eeg_time_series(subject_id, data_root)
            if eeg_data is None:
                logger.error(f"Cannot store {subject_id}: missing cleaned EEG data.")
                results["failed_subjects"].append(subject_id)
                continue
            
            # Store structural connectome
            conn_path = store_structural_connectome(subject_id, conn_matrix, data_root)
            
            # Store cleaned EEG
            eeg_path = store_cleaned_eeg(subject_id, eeg_data, data_root)
            
            # Record success
            results["stored_subjects"].append(subject_id)
            manifest_entries.append({
                "subject_id": subject_id,
                "connectome_path": conn_path,
                "eeg_path": eeg_path,
                "connectome_shape": list(conn_matrix.shape),
                "eeg_shape": list(eeg_data.shape)
            })
            
            logger.info(f"Successfully stored data for {subject_id}.")
            
        except Exception as e:
            logger.exception(f"Unexpected error storing data for {subject_id}: {e}")
            results["failed_subjects"].append(subject_id)
    
    # Write manifest
    manifest_dir = data_root / "results"
    ensure_directories([manifest_dir])
    manifest_path = manifest_dir / "store_manifest.json"
    
    with open(manifest_path, 'w') as f:
        json.dump({
            "total_subjects": len(subject_ids),
            "stored_count": len(results["stored_subjects"]),
            "failed_count": len(results["failed_subjects"]),
            "entries": manifest_entries
        }, f, indent=2)
    
    results["manifest_path"] = str(manifest_path)
    logger.info(f"Store pipeline complete. Manifest saved to {manifest_path}")
    
    return results


def main():
    """
    CLI entry point for the store script.
    Runs the store pipeline for all subjects found in the processed data directory.
    """
    data_root = get_data_root()
    
    # Discover subjects from the raw/processed directory structure
    # We look for connectome files in data/processed/connectomes/ as the source of truth
    conn_dir = data_root / "processed" / "connectomes"
    eeg_dir = data_root / "processed" / "eeg"
    
    if not conn_dir.exists() or not eeg_dir.exists():
        logger.error("Processed data directories not found. Run preprocessing/simulation first.")
        return 1
    
    # Extract subject IDs from filenames
    subject_ids = set()
    for f in conn_dir.glob("*_connectome.npy"):
        subject_ids.add(f.stem.replace("_connectome", ""))
    
    logger.info(f"Discovered {len(subject_ids)} subjects to process: {sorted(subject_ids)}")
    
    if not subject_ids:
        logger.warning("No subjects found in processed directories.")
        return 0
    
    results = run_store_pipeline(sorted(subject_ids), data_root)
    
    print(f"Store Pipeline Results:")
    print(f"  Stored: {len(results['stored_subjects'])}")
    print(f"  Failed: {len(results['failed_subjects'])}")
    if results['failed_subjects']:
        print(f"  Failed IDs: {results['failed_subjects']}")
    
    return 0 if len(results['failed_subjects']) == 0 else 1


if __name__ == "__main__":
    exit(main())
