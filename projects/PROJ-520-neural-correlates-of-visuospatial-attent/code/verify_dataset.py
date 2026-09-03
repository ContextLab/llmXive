import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from logger import get_logger

class VerificationError(Exception):
    """Raised when dataset verification fails."""
    pass

def check_bids_structure(dataset_path: Path) -> bool:
    """
    Check if the dataset directory contains basic BIDS structure.
    Returns True if valid, raises VerificationError otherwise.
    """
    logger = get_logger(__name__)
    
    if not dataset_path.exists():
        raise VerificationError(f"Dataset path does not exist: {dataset_path}")
    
    # Check for subjects directory (standard BIDS)
    subjects_dir = dataset_path / "sub-*"
    if not any(dataset_path.glob("sub-*")):
        logger.warning("No subject directories (sub-*) found. Checking for single-subject structure...")
        # Allow single-subject datasets that might not have sub-* prefix if it's a specific OpenNeuro format
        # but we expect at least some data files
        if not any(dataset_path.glob("*")):
            raise VerificationError(f"No data files found in dataset path: {dataset_path}")
    
    # Check for dataset_description.json (BIDS requirement)
    desc_file = dataset_path / "dataset_description.json"
    if not desc_file.exists():
        logger.warning("dataset_description.json not found. This is a BIDS violation, but proceeding for OpenNeuro compatibility.")
    
    logger.info(f"BIDS structure check passed for: {dataset_path}")
    return True

def check_event_markers(dataset_path: Path) -> Dict[str, Any]:
    """
    Pre-flight check: Validate that the target dataset contains event markers.
    Specifically looks for events.tsv files OR documented landmark timestamps.
    
    Returns a dict with:
      - 'has_events': bool (True if events.tsv found)
      - 'has_landmarks': bool (True if landmark markers found)
      - 'event_files': list of paths to found event files
      - 'valid': bool (True if at least one marker type is present)
      
    Raises VerificationError if NO event markers are found at all.
    """
    logger = get_logger(__name__)
    result = {
        'has_events': False,
        'has_landmarks': False,
        'event_files': [],
        'valid': False,
        'details': []
    }

    # Strategy 1: Look for standard BIDS events.tsv files
    logger.info(f"Scanning {dataset_path} for events.tsv files...")
    events_files = list(dataset_path.rglob("events.tsv"))
    
    if events_files:
        result['has_events'] = True
        result['event_files'] = [str(f) for f in events_files]
        result['details'].append(f"Found {len(events_files)} events.tsv file(s)")
        logger.info(f"Found events.tsv files: {events_files}")
        
        # Validate at least one file is non-empty
        valid_files = 0
        for ef in events_files:
            if ef.stat().st_size > 0:
                valid_files += 1
        
        if valid_files == 0:
            logger.warning("All events.tsv files are empty.")
        else:
            logger.info(f"{valid_files} events.tsv file(s) are non-empty.")
    
    # Strategy 2: Look for landmark markers (alternative event source)
    # These might be in JSON sidecars or specific metadata files
    logger.info("Checking for landmark timestamp markers...")
    landmark_indicators = []
    
    # Check for common landmark metadata patterns
    json_files = list(dataset_path.rglob("*.json"))
    for jf in json_files:
        try:
            with open(jf, 'r') as f:
                content = f.read().lower()
                # Look for common landmark indicators
                if any(ind in content for ind in ['landmark', 'stimulus_onset', 'trigger', 'event_marker']):
                    landmark_indicators.append(str(jf))
        except Exception as e:
            logger.debug(f"Could not read {jf}: {e}")
    
    if landmark_indicators:
        result['has_landmarks'] = True
        result['details'].append(f"Found landmark indicators in {len(landmark_indicators)} file(s)")
        logger.info(f"Landmark markers found in: {landmark_indicators}")
    
    # Determine validity
    if result['has_events'] or result['has_landmarks']:
        result['valid'] = True
        logger.info("Pre-flight check PASSED: Event markers or landmark timestamps detected.")
    else:
        error_msg = (
            f"CRITICAL: No event markers found in {dataset_path}. "
            "Neither events.tsv files nor landmark timestamp indicators were detected. "
            "The pipeline cannot proceed without event markers. "
            "Please verify the dataset source or provide event marker configuration."
        )
        logger.error(error_msg)
        raise VerificationError(error_msg)
    
    return result

def run_verification(dataset_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full verification pipeline:
    1. Check BIDS structure
    2. Check for event markers (pre-flight)
    
    Returns a comprehensive verification report.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting dataset verification for: {dataset_path}")
    
    dataset_p = Path(dataset_path)
    report = {
        'dataset_path': str(dataset_p),
        'status': 'unknown',
        'bids_valid': False,
        'event_check': None,
        'timestamp': None,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Step 1: BIDS Structure Check
        bids_valid = check_bids_structure(dataset_p)
        report['bids_valid'] = bids_valid
        logger.info("BIDS structure validation complete.")
        
        # Step 2: Event Marker Pre-flight Check (T041 core)
        event_check = check_event_markers(dataset_p)
        report['event_check'] = event_check
        
        if event_check['valid']:
            report['status'] = 'valid'
            logger.info("Dataset verification PASSED. Ready for download/processing.")
        else:
            report['status'] = 'invalid'
            report['errors'].append("No valid event markers found.")
            
    except VerificationError as e:
        report['status'] = 'failed'
        report['errors'].append(str(e))
        logger.error(f"Verification failed: {e}")
        raise
    except Exception as e:
        report['status'] = 'error'
        report['errors'].append(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error during verification")
        raise
    
    # Write report if output path specified
    if output_path:
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)
        with open(output_p, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Verification report written to: {output_path}")
    
    return report

def main():
    """CLI entry point for dataset verification."""
    parser = argparse.ArgumentParser(
        description="Pre-flight check for OpenNeuro dataset event markers."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the dataset directory (local) or dataset ID (OpenNeuro)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the verification report JSON."
    )
    
    args = parser.parse_args()
    
    # Initialize logging
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    
    try:
        report = run_verification(args.dataset, args.output)
        if report['status'] == 'valid':
            print("VERIFICATION PASSED")
            sys.exit(0)
        else:
            print("VERIFICATION FAILED")
            print(json.dumps(report, indent=2))
            sys.exit(1)
    except VerificationError as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"VERIFICATION ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()