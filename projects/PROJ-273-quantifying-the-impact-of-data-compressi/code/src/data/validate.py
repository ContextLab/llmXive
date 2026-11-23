"""
Validation module for GW injection campaign data.

Validates that injected files contain:
- Strain time series
- Detector names
- Event timestamps
- Known true parameters (ground truth)
- Spin metadata (tilt angles)

Operates under Amended FR-001 and FR-009.
"""
import json
import os
import numpy as np
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Required metadata keys for validation
REQUIRED_METADATA_KEYS = [
    'detector_name',
    'event_timestamp',
    'strain_time',
    'strain_data',
    'true_parameters'
]

# Required true parameter keys (ground truth from synthetic injection)
REQUIRED_TRUE_PARAM_KEYS = [
    'mass_1',
    'mass_2',
    'distance',
    'chirp_mass',
    'mass_ratio',
    'spin_1_x',
    'spin_1_y',
    'spin_1_z',
    'spin_2_x',
    'spin_2_y',
    'spin_2_z',
    'tilt_1',
    'tilt_2',
    'phi_12',
    'phi_jl'
]

# Required spin metadata keys (FR-008, FR-009)
REQUIRED_SPIN_KEYS = [
    'tilt_1',
    'tilt_2',
    'phi_12',
    'phi_jl'
]


def check_true_parameters_exist(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if 'true_parameters' exists in metadata and contains all required keys.
    
    Args:
        metadata: Dictionary containing injection metadata.
        
    Returns:
        Tuple of (is_valid, list_of_missing_keys).
    """
    missing_keys = []
    
    if 'true_parameters' not in metadata:
        return False, ['true_parameters']
    
    true_params = metadata['true_parameters']
    
    # Check for required true parameter keys
    for key in REQUIRED_TRUE_PARAM_KEYS:
        if key not in true_params:
            missing_keys.append(key)
    
    # Check specifically for spin metadata (tilt angles) - FR-009
    for key in REQUIRED_SPIN_KEYS:
        if key not in true_params:
            if key not in missing_keys:
                missing_keys.append(key)
    
    is_valid = len(missing_keys) == 0
    return is_valid, missing_keys


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that metadata contains all required fields.
    
    Checks for:
    - detector_name
    - event_timestamp
    - strain_time
    - strain_data
    - true_parameters (with ground truth and spin metadata)
    
    Args:
        metadata: Dictionary containing injection metadata.
        
    Returns:
        Tuple of (is_valid, list_of_missing_or_invalid_keys).
    """
    missing_keys = []
    
    # Check for required top-level metadata keys
    for key in REQUIRED_METADATA_KEYS:
        if key not in metadata:
            missing_keys.append(key)
    
    # If true_parameters is missing, we can't check its contents
    if 'true_parameters' in metadata:
        is_true_params_valid, missing_true_params = check_true_parameters_exist(metadata)
        if not is_true_params_valid:
            # Add the missing true parameter keys to the list
            for key in missing_true_params:
                full_key = f"true_parameters.{key}"
                if full_key not in missing_keys:
                    missing_keys.append(full_key)
    
    # Validate data types and basic structure
    if 'strain_time' in metadata and 'strain_data' in metadata:
        strain_time = metadata['strain_time']
        strain_data = metadata['strain_data']
        
        if not isinstance(strain_time, (list, np.ndarray)) or len(strain_time) == 0:
            missing_keys.append("strain_time (must be non-empty array)")
        
        if not isinstance(strain_data, (list, np.ndarray)) or len(strain_data) == 0:
            missing_keys.append("strain_data (must be non-empty array)")
        
        if len(strain_time) != len(strain_data):
            missing_keys.append("strain_time and strain_data length mismatch")
    
    is_valid = len(missing_keys) == 0
    return is_valid, missing_keys


def validate_file(file_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate an injected event file.
    
    Args:
        file_path: Path to the JSON file containing injected event data.
        
    Returns:
        Tuple of (is_valid, validation_details).
    """
    result = {
        'file_path': file_path,
        'is_valid': False,
        'errors': [],
        'metadata_valid': False,
        'true_params_valid': False,
        'spin_metadata_valid': False
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        result['errors'].append(f"File not found: {file_path}")
        logger.error(f"Validation failed: File not found - {file_path}")
        return False, result
    
    try:
        with open(file_path, 'r') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        result['errors'].append(f"Invalid JSON: {str(e)}")
        logger.error(f"Validation failed: Invalid JSON - {file_path}: {e}")
        return False, result
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
        logger.error(f"Validation failed: Error reading file - {file_path}: {e}")
        return False, result
    
    # Validate metadata structure
    metadata_valid, missing_metadata_keys = validate_metadata(metadata)
    result['metadata_valid'] = metadata_valid
    
    if not metadata_valid:
        for key in missing_metadata_keys:
            result['errors'].append(f"Missing or invalid metadata key: {key}")
    
    # Check true parameters specifically
    if 'true_parameters' in metadata:
        true_params_valid, missing_true_keys = check_true_parameters_exist(metadata)
        result['true_params_valid'] = true_params_valid
        
        if not true_params_valid:
            for key in missing_true_keys:
                result['errors'].append(f"Missing true parameter: {key}")
        
        # Specifically check for spin metadata (tilt angles) - FR-009
        true_params = metadata['true_parameters']
        spin_keys_present = all(key in true_params for key in REQUIRED_SPIN_KEYS)
        result['spin_metadata_valid'] = spin_keys_present
        
        if not spin_keys_present:
            missing_spin = [key for key in REQUIRED_SPIN_KEYS if key not in true_params]
            result['errors'].append(f"Missing spin metadata (tilt angles): {missing_spin}")
    else:
        result['errors'].append("Missing 'true_parameters' in metadata")
    
    # Final validation status
    result['is_valid'] = (
        metadata_valid and 
        result['true_params_valid'] and 
        result['spin_metadata_valid'] and 
        len(result['errors']) == 0
    )
    
    if result['is_valid']:
        logger.info(f"Validation passed: {file_path}")
    else:
        logger.warning(f"Validation failed: {file_path} - {result['errors']}")
    
    return result['is_valid'], result


def validate_batch(file_paths: List[str]) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validate a batch of injected event files.
    
    Args:
        file_paths: List of paths to JSON files containing injected event data.
        
    Returns:
        Tuple of (valid_count, invalid_count, list_of_validation_results).
    """
    valid_count = 0
    invalid_count = 0
    results = []
    
    for file_path in file_paths:
        is_valid, details = validate_file(file_path)
        results.append(details)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
    
    logger.info(f"Batch validation complete: {valid_count} valid, {invalid_count} invalid out of {len(file_paths)} files")
    return valid_count, invalid_count, results


def main():
    """
    Main entry point for validation script.
    
    Validates all injected event files in the data/raw/ directory.
    """
    import sys
    
    # Default path if no argument provided
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = str(Path(__file__).parent.parent.parent / "data" / "raw")
    
    target_path = Path(target_path)
    
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        sys.exit(1)
    
    # Find all JSON files
    json_files = list(target_path.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {target_path}")
        sys.exit(0)
    
    logger.info(f"Found {len(json_files)} JSON files to validate")
    
    # Validate all files
    valid_count, invalid_count, results = validate_batch([str(f) for f in json_files])
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Total files: {len(json_files)}")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    
    if invalid_count > 0:
        print(f"\nInvalid files:")
        for result in results:
            if not result['is_valid']:
                print(f"  - {result['file_path']}: {result['errors']}")
        sys.exit(1)
    else:
        print("\nAll files validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()