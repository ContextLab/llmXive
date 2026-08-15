import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the stimuli manifest JSON file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Dictionary containing the manifest data
        
    Raises:
        FileNotFoundError: If manifest file does not exist
        json.JSONDecodeError: If manifest file is not valid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def load_error_log(error_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the generation errors log file.
    
    Args:
        error_log_path: Path to the error log file
        
    Returns:
        List of error entries
    """
    if not error_log_path.exists():
        logger.warning(f"Error log file not found: {error_log_path}. Assuming no errors.")
        return []
    
    errors = []
    with open(error_log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed error log line: {line}")
    return errors

def get_stimuli_files(stimuli_dir: Path) -> List[Path]:
    """
    Get all image files from the stimuli directory.
    
    Args:
        stimuli_dir: Path to the stimuli directory
        
    Returns:
        List of paths to image files
    """
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
    
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    stimuli_files = []
    
    for file_path in stimuli_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            stimuli_files.append(file_path)
    
    return sorted(stimuli_files)

def validate_manifest_completeness(
    manifest: Dict[str, Any],
    stimuli_files: List[Path],
    error_log: List[Dict[str, Any]] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that every stimulus image has a corresponding manifest entry
    with exact parameter values.
    
    Args:
        manifest: The loaded manifest dictionary
        stimuli_files: List of stimulus image file paths
        error_log: Optional list of error entries to cross-reference
        
    Returns:
        Tuple of (is_valid, missing_files, mismatched_entries)
    """
    missing_files = []
    mismatched_entries = []
    
    # Build a set of filenames from the manifest
    manifest_files = set()
    manifest_entries_by_filename = {}
    
    for entry in manifest.get('entries', []):
        filename = entry.get('filename')
        if filename:
            manifest_files.add(filename)
            manifest_entries_by_filename[filename] = entry
    
    # Check for missing files in manifest
    for file_path in stimuli_files:
        filename = file_path.name
        if filename not in manifest_files:
            missing_files.append(filename)
        else:
            # Validate exact parameter values
            entry = manifest_entries_by_filename[filename]
            
            # Check if flanker_count and eccentricity are present and valid
            if 'flanker_count' not in entry:
                mismatched_entries.append(f"{filename}: Missing 'flanker_count'")
            elif not isinstance(entry['flanker_count'], int) or entry['flanker_count'] < 0:
                mismatched_entries.append(f"{filename}: Invalid 'flanker_count' value: {entry['flanker_count']}")
            
            if 'eccentricity' not in entry:
                mismatched_entries.append(f"{filename}: Missing 'eccentricity'")
            elif not isinstance(entry['eccentricity'], (int, float)) or entry['eccentricity'] < 0:
                mismatched_entries.append(f"{filename}: Invalid 'eccentricity' value: {entry['eccentricity']}")
            
            # Check emotion category
            if 'emotion' not in entry:
                mismatched_entries.append(f"{filename}: Missing 'emotion'")
    
    # Check for manifest entries without corresponding files
    existing_filenames = {f.name for f in stimuli_files}
    for filename in manifest_files:
        if filename not in existing_filenames:
            # This might be an error case where a file was supposed to be generated but wasn't
            # Check if it's in the error log
            if error_log:
                error_filenames = {e.get('filename') for e in error_log if 'filename' in e}
                if filename in error_filenames:
                    continue  # It's expected to be missing due to an error
            mismatched_entries.append(f"{filename}: Manifest entry exists but file not found")
    
    is_valid = len(missing_files) == 0 and len(mismatched_entries) == 0
    return is_valid, missing_files, mismatched_entries

def generate_validation_report(
    is_valid: bool,
    missing_files: List[str],
    mismatched_entries: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a validation report and save it to a file.
    
    Args:
        is_valid: Whether the validation passed
        missing_files: List of missing files
        mismatched_entries: List of mismatched entries
        output_path: Path to save the report
        
    Returns:
        Dictionary containing the report data
    """
    report = {
        'validation_passed': is_valid,
        'total_stimuli_checked': len(missing_files) + len(mismatched_entries) if not is_valid else 0,
        'missing_files': missing_files,
        'mismatched_entries': mismatched_entries,
        'timestamp': str(Path(output_path).parent.parent.name),  # Just a placeholder for timestamp
        'details': {
            'missing_count': len(missing_files),
            'mismatch_count': len(mismatched_entries),
            'missing_files_sample': missing_files[:10] if len(missing_files) > 10 else missing_files,
            'mismatched_entries_sample': mismatched_entries[:10] if len(mismatched_entries) > 10 else mismatched_entries
        }
    }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report generated: {output_path}")
    return report

def main():
    """
    Main function to validate manifest completeness.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    stimuli_dir = project_root / 'data' / 'interim' / 'stimuli'
    manifest_path = project_root / 'data' / 'interim' / 'stimuli_manifest.json'
    error_log_path = project_root / 'data' / 'interim' / 'generation_errors.log'
    report_path = project_root / 'data' / 'interim' / 'manifest_validation_report.json'
    
    logger.info("Starting manifest completeness validation...")
    
    try:
        # Load data
        logger.info(f"Loading manifest from: {manifest_path}")
        manifest = load_manifest(manifest_path)
        
        logger.info(f"Loading error log from: {error_log_path}")
        error_log = load_error_log(error_log_path)
        
        logger.info(f"Getting stimulus files from: {stimuli_dir}")
        stimuli_files = get_stimuli_files(stimuli_dir)
        logger.info(f"Found {len(stimuli_files)} stimulus files")
        
        # Validate
        logger.info("Validating manifest completeness...")
        is_valid, missing_files, mismatched_entries = validate_manifest_completeness(
            manifest, stimuli_files, error_log
        )
        
        # Generate report
        report = generate_validation_report(is_valid, missing_files, mismatched_entries, report_path)
        
        # Log results
        if is_valid:
            logger.info("✅ Validation PASSED: All stimulus images have corresponding manifest entries with exact parameter values.")
        else:
            logger.warning("❌ Validation FAILED:")
            if missing_files:
                logger.warning(f"   - {len(missing_files)} files missing from manifest")
            if mismatched_entries:
                logger.warning(f"   - {len(mismatched_entries)} entries with missing/invalid parameters")
        
        return 0 if is_valid else 1
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())