import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure parent directory is in path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.stimuli_manifest import load_error_log

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the stimuli manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def get_stimuli_files(stimuli_dir: Path) -> List[str]:
    """
    Get a list of all image files in the stimuli directory.
    Returns list of filenames (strings).
    """
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
    
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    files = []
    for file_path in stimuli_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            files.append(file_path.name)
    
    return sorted(files)

def validate_manifest_completeness(manifest: Dict[str, Any], stimuli_files: List[str]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that every image file in the stimuli directory has a corresponding
    entry in the manifest with exact parameter values.
    
    Returns:
        Tuple of (is_valid, missing_files, invalid_entries)
        - is_valid: True if all files are present and valid
        - missing_files: List of filenames found on disk but missing in manifest
        - invalid_entries: List of filenames where manifest entry exists but parameters are missing/invalid
    """
    missing_files = []
    invalid_entries = []
    
    # Create a set of filenames in the manifest for quick lookup
    manifest_filenames = set()
    
    for entry in manifest:
        filename = entry.get('file')
        if not filename:
            invalid_entries.append(f"Entry missing 'file' field: {entry}")
            continue
        
        manifest_filenames.add(filename)
        
        # Check for required parameter fields
        required_params = ['emotion', 'flanker_count', 'eccentricity']
        missing_params = []
        for param in required_params:
            if param not in entry or entry[param] is None:
                missing_params.append(param)
        
        if missing_params:
            invalid_entries.append(f"File '{filename}' missing parameters: {missing_params}")
    
    # Check for files on disk that are not in manifest
    for filename in stimuli_files:
        if filename not in manifest_filenames:
            missing_files.append(filename)
    
    is_valid = len(missing_files) == 0 and len(invalid_entries) == 0
    return is_valid, missing_files, invalid_entries

def generate_validation_report(
    manifest_path: Path,
    stimuli_dir: Path,
    error_log_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report and write it to a JSON file.
    
    Args:
        manifest_path: Path to the stimuli manifest JSON file
        stimuli_dir: Path to the directory containing generated stimuli images
        error_log_path: Path to the generation errors log file
        output_path: Path where the validation report will be written
    
    Returns:
        Dictionary containing the validation report
    """
    report = {
        'status': 'incomplete',
        'manifest_path': str(manifest_path),
        'stimuli_dir': str(stimuli_dir),
        'error_log_path': str(error_log_path),
        'summary': {},
        'missing_files': [],
        'invalid_entries': [],
        'error_log_entries': []
    }
    
    try:
        # Load manifest
        logger.info(f"Loading manifest from {manifest_path}")
        manifest = load_manifest(manifest_path)
        report['summary']['manifest_entries'] = len(manifest)
        
        # Load error log if it exists
        if error_log_path.exists():
            error_log = load_error_log(error_log_path)
            report['error_log_entries'] = error_log
            report['summary']['error_log_entries'] = len(error_log)
        else:
            report['summary']['error_log_entries'] = 0
            logger.warning(f"Error log not found at {error_log_path}")
        
        # Get stimuli files
        logger.info(f"Scanning stimuli directory: {stimuli_dir}")
        stimuli_files = get_stimuli_files(stimuli_dir)
        report['summary']['stimuli_files_on_disk'] = len(stimuli_files)
        
        # Validate completeness
        logger.info("Validating manifest completeness...")
        is_valid, missing_files, invalid_entries = validate_manifest_completeness(manifest, stimuli_files)
        
        report['missing_files'] = missing_files
        report['invalid_entries'] = invalid_entries
        
        if is_valid:
            report['status'] = 'complete'
            logger.info("Validation PASSED: All stimuli files have valid manifest entries.")
        else:
            report['status'] = 'incomplete'
            if missing_files:
                logger.error(f"Found {len(missing_files)} files missing from manifest")
            if invalid_entries:
                logger.error(f"Found {len(invalid_entries)} entries with missing/invalid parameters")
        
        # Update summary
        report['summary']['validation_passed'] = is_valid
        report['summary']['missing_files_count'] = len(missing_files)
        report['summary']['invalid_entries_count'] = len(invalid_entries)
        
        # Write report to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        report['status'] = 'error'
        report['error'] = str(e)
        
        # Still try to write the error report
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as write_error:
            logger.error(f"Failed to write error report: {str(write_error)}")
            raise
    
    return report

def main():
    """Main entry point for the manifest validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate stimuli manifest completeness')
    parser.add_argument(
        '--manifest',
        type=str,
        default='data/interim/stimuli_manifest.json',
        help='Path to the stimuli manifest JSON file'
    )
    parser.add_argument(
        '--stimuli-dir',
        type=str,
        default='data/interim/stimuli',
        help='Path to the directory containing generated stimuli images'
    )
    parser.add_argument(
        '--error-log',
        type=str,
        default='data/interim/generation_errors.log',
        help='Path to the generation errors log file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/interim/manifest_validation_report.json',
        help='Path for the output validation report'
    )
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    stimuli_dir = Path(args.stimuli_dir)
    error_log_path = Path(args.error_log)
    output_path = Path(args.output)
    
    report = generate_validation_report(manifest_path, stimuli_dir, error_log_path, output_path)
    
    # Exit with error code if validation failed
    if report['status'] != 'complete':
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
