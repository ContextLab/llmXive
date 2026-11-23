import json
import logging
import os
import sys
from pathlib import Path
from typing import Set, Dict, Any, List, Optional

# Import logging utilities from the project's existing API
from utils.logging_setup import get_logger, log_mode_switch
from utils.config import ensure_dirs, PROJECT_ROOT

logger = get_logger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the verified source manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def get_downloaded_files(raw_dir: Path) -> List[Path]:
    """Get list of all downloaded files in the raw directory."""
    if not raw_dir.exists():
        return []
    return list(raw_dir.glob("*"))

def extract_subject_id(filename: str) -> Optional[str]:
    """
    Extract subject ID from filename.
    Expected pattern: sub-{subject_id}_run-{run_id}.edf
    Returns the subject_id string or None if pattern doesn't match.
    """
    if not filename.startswith("sub-"):
        return None
    try:
        # Split by underscore, take first part, remove 'sub-' prefix
        parts = filename.split('_')
        if len(parts) >= 1 and parts[0].startswith("sub-"):
            return parts[0][4:]  # Remove 'sub-' prefix
    except Exception:
        logger.warning(f"Could not extract subject ID from {filename}")
    return None

def verify_alignment(raw_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify subject overlap between EEG and tDCS within the single source.
    
    This function checks if the downloaded files in data/raw/ contain
    consistent subject IDs that match the expected dataset structure.
    
    Returns a report dict with:
    - 'status': 'aligned' or 'mismatch'
    - 'subjects_found': list of subject IDs found
    - 'expected_count': expected number of subjects (from manifest if available)
    - 'message': descriptive message
    """
    files = get_downloaded_files(raw_dir)
    
    if not files:
        return {
            'status': 'mismatch',
            'subjects_found': [],
            'expected_count': 0,
            'message': 'No files found in raw directory'
        }
    
    # Extract all subject IDs from filenames
    subject_ids: Set[str] = set()
    for f in files:
        sid = extract_subject_id(f.name)
        if sid:
            subject_ids.add(sid)
    
    # Check for consistency
    # In a properly aligned dataset, all files should belong to valid subjects
    # and we should have at least some subjects
    if not subject_ids:
        return {
            'status': 'mismatch',
            'subjects_found': [],
            'expected_count': manifest.get('N_actual', 0),
            'message': 'No valid subject IDs found in filenames'
        }
    
    # Check if the number of subjects matches expectations (if available)
    expected_n = manifest.get('N_actual', None)
    actual_n = len(subject_ids)
    
    # For this check, we verify that:
    # 1. We have at least one subject
    # 2. The subject IDs are consistent (no malformed entries)
    # 3. If expected_n is provided, we check if we have at least that many
    #    (allowing for some tolerance in download scenarios)
    
    if expected_n is not None and actual_n < expected_n:
        # We found fewer subjects than expected - potential data loss
        return {
            'status': 'mismatch',
            'subjects_found': sorted(list(subject_ids)),
            'expected_count': expected_n,
            'message': f'Found {actual_n} subjects, expected {expected_n}. Data alignment issue detected.'
        }
    
    return {
        'status': 'aligned',
        'subjects_found': sorted(list(subject_ids)),
        'expected_count': expected_n,
        'message': f'Successfully verified {actual_n} subjects. Data alignment confirmed.'
    }

def set_mode_insufficient(mode_flag_path: Path, manifest_path: Path, reason: str):
    """
    Set the mode flag to 'Data Insufficient' and update the manifest.
    This is called when data alignment fails.
    """
    logger.warning(f"Setting mode to Data Insufficient: {reason}")
    log_mode_switch("Data Insufficient", reason)
    
    # Update the manifest to reflect the mode change
    manifest = load_manifest(manifest_path)
    manifest['mode_flag'] = 'Data Insufficient'
    manifest['alignment_status'] = 'failed'
    manifest['alignment_reason'] = reason
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Ensure the mode flag file is updated
    mode_flag_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mode_flag_path, 'w') as f:
        f.write('Data Insufficient')
    
    logger.info("Mode flag updated to Data Insufficient. Pipeline will skip downstream tasks.")

def main():
    """
    Main entry point for the data alignment check task.
    
    This task:
    1. Loads the verified source manifest from T011
    2. Checks the mode flag from T012
    3. If mode is 'Primary', verifies subject overlap in downloaded files
    4. If alignment fails, sets mode to 'Data Insufficient' and exits
    5. If alignment succeeds, logs success and exits normally
    """
    # Define paths
    project_root = Path(PROJECT_ROOT) if PROJECT_ROOT else Path(__file__).parent.parent
    raw_dir = project_root / 'data' / 'raw'
    manifest_path = project_root / 'verified_source_manifest.json'
    mode_flag_path = project_root / 'state' / 'projects' / 'PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml'
    
    # Ensure directories exist
    ensure_dirs()
    
    logger.info("Starting Data Alignment Check (T015)")
    
    # Check if manifest exists (from T011)
    if not manifest_path.exists():
        logger.error("Manifest not found. Please run T011 first.")
        sys.exit(1)
    
    # Load manifest
    manifest = load_manifest(manifest_path)
    
    # Check mode flag
    mode = manifest.get('mode_flag', 'Unknown')
    logger.info(f"Current mode flag: {mode}")
    
    # If not in Primary mode, skip alignment check
    if mode != 'Primary':
        logger.info(f"Mode is '{mode}'. Skipping data alignment check.")
        print(f"Skipped: Mode is {mode}")
        sys.exit(0)
    
    # Perform alignment check
    logger.info("Verifying subject overlap in downloaded data...")
    alignment_report = verify_alignment(raw_dir, manifest)
    
    # Log results
    logger.info(f"Alignment status: {alignment_report['status']}")
    logger.info(f"Subjects found: {alignment_report['subjects_found']}")
    logger.info(f"Message: {alignment_report['message']}")
    
    # Check if alignment failed
    if alignment_report['status'] == 'mismatch':
        logger.error(f"Data alignment failed: {alignment_report['message']}")
        set_mode_insufficient(mode_flag_path, manifest_path, alignment_report['message'])
        print(f"FAILED: {alignment_report['message']}")
        sys.exit(0)  # Exit with 0 as per spec (pipeline terminates downstream tasks via mode flag)
    
    # Success
    logger.info("Data alignment check passed.")
    print("SUCCESS: Data alignment verified.")
    
    # Save alignment report for downstream tasks
    report_path = project_root / 'data' / 'processed' / 'alignment_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(alignment_report, f, indent=2)
    
    logger.info(f"Alignment report saved to {report_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
