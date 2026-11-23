import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import logger from existing module
from logger import get_logger

class VerificationError(Exception):
    """Raised when dataset verification fails."""
    pass

def check_bids_structure(dataset_path: str) -> Dict[str, Any]:
    """
    Validates that the dataset follows BIDS structure.
    Returns a status dict with 'valid' (bool) and 'issues' (list).
    """
    logger = get_logger("verify_dataset")
    path = Path(dataset_path)
    
    if not path.exists():
        raise VerificationError(f"Dataset path does not exist: {dataset_path}")

    # Required BIDS root files
    required_files = ['dataset_description.json', 'participants.tsv']
    issues = []
    
    for f in required_files:
        if not (path / f).exists():
            issues.append(f"Missing required BIDS file: {f}")
    
    # Check for subject directories
    subjects = [d for d in path.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    if not subjects:
        issues.append("No subject directories found (sub-*)")
    
    valid = len(issues) == 0
    logger.info(f"BIDS structure check: {'PASS' if valid else 'FAIL'} ({len(issues)} issues)")
    
    return {
        'valid': valid,
        'issues': issues,
        'subject_count': len(subjects)
    }

def check_event_markers(dataset_path: str) -> Dict[str, Any]:
    """
    Validates the presence of event markers (events.tsv or landmarks.tsv).
    Returns a status dict with 'valid' (bool), 'markers' (list), and 'source' (str).
    """
    logger = get_logger("verify_dataset")
    path = Path(dataset_path)
    
    markers_found = []
    source = "none"
    
    # Check for events.tsv in subject directories
    for sub_dir in path.glob('sub-*'):
        if sub_dir.is_dir():
            # Look in func or eig directories
            for task_dir in sub_dir.rglob('events.tsv'):
                markers_found.append(str(task_dir.relative_to(path)))
                source = "events.tsv"
            
            # Look for landmarks.tsv (fallback)
            for lm_dir in sub_dir.rglob('landmarks.tsv'):
                markers_found.append(str(lm_dir.relative_to(path)))
                if source == "none":
                    source = "landmarks.tsv"
    
    valid = len(markers_found) > 0
    
    if not valid:
        logger.warning("No event markers found. Pipeline will halt.")
        raise VerificationError(
            "Missing event markers: Neither events.tsv nor landmarks.tsv found in dataset."
        )
    
    logger.info(f"Event marker check: PASS ({len(markers_found)} markers found, source: {source})")
    
    return {
        'valid': valid,
        'markers': markers_found,
        'source': source
    }

def run_verification(dataset_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the full verification suite (BIDS + Event Markers).
    Returns a comprehensive result dict.
    """
    logger = get_logger("verify_dataset")
    logger.info(f"Starting verification for: {dataset_path}")
    
    result = {
        'dataset_path': str(dataset_path),
        'status': 'PASS',
        'details': {}
    }
    
    try:
        bids_result = check_bids_structure(dataset_path)
        result['details']['bids'] = bids_result
        
        if not bids_result['valid']:
            result['status'] = 'WARN'
            logger.warning("BIDS validation passed with warnings.")
        
        event_result = check_event_markers(dataset_path)
        result['details']['events'] = event_result
        
        # Hard gate logic: Must have events to proceed
        if not event_result['valid']:
            result['status'] = 'FAIL'
            raise VerificationError("Hard Gate Failed: Event markers missing.")
        
        if result['status'] == 'PASS':
            logger.info("T005 Gate: VERIFIED. Proceeding to T010.")
        
    except VerificationError as e:
        result['status'] = 'FAIL'
        result['error'] = str(e)
        logger.error(f"Verification failed: {e}")
        raise
    
    # Write output file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Verification report written to: {output_path}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Verify OpenNeuro dataset for T005 Gate")
    parser.add_argument('--dataset', type=str, required=True, help='Path to dataset directory')
    parser.add_argument('--output', type=str, default=None, help='Path to output JSON report')
    
    args = parser.parse_args()
    
    logger = get_logger("verify_dataset")
    logger.info("T005c: Executing T005 Gate Verification")
    
    try:
        result = run_verification(args.dataset, args.output)
        if result['status'] == 'PASS':
            print("T005 Gate: PASSED")
            sys.exit(0)
        else:
            print(f"T005 Gate: FAILED - {result.get('error', 'Unknown error')}")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Verification execution failed: {e}")
        print(f"T005 Gate: CRITICAL FAILURE - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
