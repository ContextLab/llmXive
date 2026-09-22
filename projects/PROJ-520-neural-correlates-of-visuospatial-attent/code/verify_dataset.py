"""
Dataset verification module for PROJ-520.
Implements BIDS validation and event marker checks.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import logger from project
try:
    from logger import get_logger
except ImportError:
    # Fallback for standalone execution
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

class VerificationError(Exception):
    """Custom exception for dataset verification failures."""
    pass

def check_bids_structure(dataset_path: Path) -> Dict[str, Any]:
    """
    Validates that the dataset follows BIDS structure requirements.
    
    Args:
        dataset_path: Path to the dataset root directory
        
    Returns:
        Dictionary with validation results
        
    Raises:
        VerificationError: If BIDS structure is invalid
    """
    logger.info(f"Validating BIDS structure at: {dataset_path}")
    
    if not dataset_path.exists():
        raise VerificationError(f"Dataset path does not exist: {dataset_path}")
    
    if not dataset_path.is_dir():
        raise VerificationError(f"Dataset path is not a directory: {dataset_path}")
    
    # Check for required BIDS files
    required_files = ['dataset_description.json']
    missing_files = []
    
    for file_name in required_files:
        if not (dataset_path / file_name).exists():
            missing_files.append(file_name)
    
    result = {
        'valid': len(missing_files) == 0,
        'missing_files': missing_files,
        'path': str(dataset_path)
    }
    
    if missing_files:
        logger.warning(f"Missing required BIDS files: {missing_files}")
        # BIDS validation is lenient for this project - we proceed if data exists
        # but log the warning
    
    # Check for subject directories
    subject_dirs = [d for d in dataset_path.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    result['subject_count'] = len(subject_dirs)
    
    if len(subject_dirs) == 0:
        logger.warning("No subject directories found (sub-*)")
    
    logger.info(f"BIDS validation complete: {result['valid']}, subjects: {len(subject_dirs)}")
    return result

def check_event_markers(dataset_path: Path) -> Dict[str, Any]:
    """
    Validates the presence of event markers (events.tsv or landmarks.tsv).
    
    Args:
        dataset_path: Path to the dataset root directory
        
    Returns:
        Dictionary with event marker validation results
        
    Raises:
        VerificationError: If no event markers are found
    """
    logger.info(f"Checking for event markers at: {dataset_path}")
    
    found_markers = []
    marker_details = []
    
    # Search for events.tsv files
    for subdir in dataset_path.rglob('sub-*'):
        if subdir.is_dir():
            # Check for events.tsv in func or eeg directories
            for event_file in subdir.rglob('events.tsv'):
                if event_file.exists():
                    found_markers.append(str(event_file))
                    try:
                        with open(event_file, 'r') as f:
                            import csv
                            reader = csv.DictReader(f, delimiter='\t')
                            rows = list(reader)
                            marker_details.append({
                                'file': str(event_file),
                                'count': len(rows),
                                'type': 'events.tsv',
                                'columns': list(rows[0].keys()) if rows else []
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse events.tsv at {event_file}: {e}")
    
    # Search for landmarks.tsv files (fallback)
    for subdir in dataset_path.rglob('sub-*'):
        if subdir.is_dir():
            for landmark_file in subdir.rglob('landmarks.tsv'):
                if landmark_file.exists():
                    found_markers.append(str(landmark_file))
                    try:
                        with open(landmark_file, 'r') as f:
                            import csv
                            reader = csv.DictReader(f, delimiter='\t')
                            rows = list(reader)
                            marker_details.append({
                                'file': str(landmark_file),
                                'count': len(rows),
                                'type': 'landmarks.tsv',
                                'columns': list(rows[0].keys()) if rows else []
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse landmarks.tsv at {landmark_file}: {e}")
    
    result = {
        'valid': len(found_markers) > 0,
        'marker_files': found_markers,
        'marker_details': marker_details,
        'total_markers_found': len(found_markers)
    }
    
    if not found_markers:
        error_msg = "Missing event markers: Neither events.tsv nor landmarks.tsv found in dataset."
        logger.error(error_msg)
        raise VerificationError(error_msg)
    
    logger.info(f"Event marker validation complete: {result['valid']}, files: {len(found_markers)}")
    return result

def run_verification(dataset_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs complete dataset verification (BIDS + event markers).
    
    Args:
        dataset_path: Path to the dataset root directory
        output_path: Optional path to save verification results JSON
        
    Returns:
        Combined verification results dictionary
        
    Raises:
        VerificationError: If any verification step fails
    """
    logger.info(f"Starting full dataset verification for: {dataset_path}")
    
    path = Path(dataset_path)
    results = {
        'dataset_path': dataset_path,
        'bids_validation': None,
        'event_validation': None,
        'overall_status': 'pending'
    }
    
    try:
        # Step 1: BIDS Structure Validation
        bids_result = check_bids_structure(path)
        results['bids_validation'] = bids_result
        
        # Step 2: Event Marker Validation
        event_result = check_event_markers(path)
        results['event_validation'] = event_result
        
        # Determine overall status
        if bids_result['valid'] and event_result['valid']:
            results['overall_status'] = 'passed'
            logger.info("Dataset verification PASSED")
        else:
            results['overall_status'] = 'failed'
            logger.warning("Dataset verification FAILED")
            
    except VerificationError as e:
        results['overall_status'] = 'failed'
        results['error'] = str(e)
        logger.error(f"Verification failed: {e}")
        raise
    except Exception as e:
        results['overall_status'] = 'error'
        results['error'] = str(e)
        logger.error(f"Unexpected error during verification: {e}")
        raise VerificationError(f"Verification error: {e}")
    
    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Verification results saved to: {output_file}")
    
    return results

def main():
    """Main entry point for dataset verification."""
    parser = argparse.ArgumentParser(description='Verify dataset structure and event markers')
    parser.add_argument('--dataset', type=str, required=True, help='Path to dataset root directory')
    parser.add_argument('--output', type=str, default=None, help='Path to save verification results JSON')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = run_verification(args.dataset, args.output)
        print(f"\nVerification Status: {results['overall_status']}")
        
        if results['overall_status'] == 'passed':
            print("✓ BIDS Structure: Valid")
            print(f"✓ Event Markers: Found {results['event_validation']['total_markers_found']} file(s)")
            sys.exit(0)
        else:
            print("✗ Verification Failed")
            if 'error' in results:
                print(f"Error: {results['error']}")
            sys.exit(1)
            
    except VerificationError as e:
        print(f"Verification Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()