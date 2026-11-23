"""
Validation module for gravitational wave injection campaigns.

This module validates injected waveform files to ensure they contain:
- Strain time series data
- Detector names
- Event timestamps
- Known true parameters (ground truth) from synthetic injections
- Spin metadata (tilt angles) as required by FR-008 and FR-009

Note: Validates 'known true parameters' from synthetic injections, not posteriors.
"""

import json
import os
import h5py
import numpy as np
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required metadata keys for validation
REQUIRED_METADATA_KEYS = [
    'detector_names',
    'event_timestamp',
    'true_parameters',
    'strain_time_series'
]

# Required true parameter keys (ground truth from injection)
REQUIRED_TRUE_PARAMS = [
    'mass_1',
    'mass_2',
    'distance',
    'chirp_mass',
    'total_mass',
    'mass_ratio'
]

# Required spin metadata keys (tilt angles) per FR-008, FR-009
REQUIRED_SPIN_METADATA = [
    'tilt_1',
    'tilt_2',
    'azimuth_1',
    'azimuth_2',
    'phi_jl'
]

# SNR threshold for valid events
MIN_SNR_THRESHOLD = 8.0

def check_true_parameters_exist(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if true parameters exist in metadata and contain required fields.
    
    Args:
        metadata: Dictionary containing injection metadata
        
    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    missing_keys = []
    
    # Check if true_parameters key exists
    if 'true_parameters' not in metadata:
        return False, ['true_parameters']
    
    true_params = metadata['true_parameters']
    
    # Check for required true parameter keys
    for key in REQUIRED_TRUE_PARAMS:
        if key not in true_params:
            missing_keys.append(f'true_parameters.{key}')
    
    # Check for required spin metadata keys (tilt angles)
    if 'spin_metadata' not in true_params:
        missing_keys.append('true_parameters.spin_metadata')
    else:
        spin_meta = true_params['spin_metadata']
        for key in REQUIRED_SPIN_METADATA:
            if key not in spin_meta:
                missing_keys.append(f'true_parameters.spin_metadata.{key}')
    
    return len(missing_keys) == 0, missing_keys

def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that metadata contains all required keys and structures.
    
    Args:
        metadata: Dictionary containing file metadata
        
    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    missing_keys = []
    
    # Check for required top-level metadata keys
    for key in REQUIRED_METADATA_KEYS:
        if key not in metadata:
            missing_keys.append(key)
    
    # If we're missing basic keys, return early
    if missing_keys:
        return False, missing_keys
    
    # Validate detector names
    if not isinstance(metadata['detector_names'], list) or len(metadata['detector_names']) == 0:
        missing_keys.append('detector_names (must be non-empty list)')
    
    # Validate event timestamp
    if not isinstance(metadata['event_timestamp'], (int, float)):
        missing_keys.append('event_timestamp (must be numeric)')
    
    # Validate true parameters exist and have required structure
    params_valid, params_missing = check_true_parameters_exist(metadata)
    if not params_valid:
        missing_keys.extend(params_missing)
    
    # Validate strain time series exists
    if 'strain_time_series' not in metadata:
        missing_keys.append('strain_time_series')
    elif not isinstance(metadata['strain_time_series'], dict):
        missing_keys.append('strain_time_series (must be dict with time/strain arrays)')
    else:
        strain_data = metadata['strain_time_series']
        if 'time' not in strain_data or 'strain' not in strain_data:
            missing_keys.append('strain_time_series (must contain time and strain)')
        elif not isinstance(strain_data['time'], np.ndarray) or not isinstance(strain_data['strain'], np.ndarray):
            missing_keys.append('strain_time_series (time and strain must be numpy arrays)')
        elif len(strain_data['time']) != len(strain_data['strain']):
            missing_keys.append('strain_time_series (time and strain must have same length)')
    
    return len(missing_keys) == 0, missing_keys

def validate_file(file_path: str) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Validate an injected waveform file.
    
    Args:
        file_path: Path to the HDF5 file to validate
        
    Returns:
        Tuple of (is_valid, metadata_dict, list_of_errors)
    """
    errors = []
    metadata = {}
    
    # Check file exists
    if not os.path.exists(file_path):
        return False, {}, [f"File not found: {file_path}"]
    
    try:
        # Open HDF5 file
        with h5py.File(file_path, 'r') as f:
            # Check for metadata group
            if 'metadata' not in f:
                errors.append("Missing 'metadata' group in HDF5 file")
                return False, {}, errors
            
            metadata_group = f['metadata']
            
            # Read metadata JSON
            if 'metadata.json' not in metadata_group:
                errors.append("Missing 'metadata.json' in metadata group")
                return False, {}, errors
            
            metadata_json = metadata_group['metadata.json'][()]
            if isinstance(metadata_json, bytes):
                metadata_json = metadata_json.decode('utf-8')
            
            metadata = json.loads(metadata_json)
            
            # Validate metadata structure
            is_valid, missing_keys = validate_metadata(metadata)
            
            if not is_valid:
                errors.extend([f"Missing or invalid: {key}" for key in missing_keys])
                return False, metadata, errors
            
            # Additional validation: check SNR > 8
            if 'snr' in metadata:
                if metadata['snr'] <= MIN_SNR_THRESHOLD:
                    errors.append(f"SNR ({metadata['snr']}) is below threshold ({MIN_SNR_THRESHOLD})")
                    return False, metadata, errors
            else:
                errors.append("Missing 'snr' in metadata")
                return False, metadata, errors
            
            # Validate strain data can be read
            if 'strain' in f:
                strain = f['strain'][:]
                if len(strain) == 0:
                    errors.append("Strain data is empty")
                    return False, metadata, errors
            else:
                errors.append("Missing 'strain' dataset in HDF5 file")
                return False, metadata, errors
            
            return True, metadata, []
            
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        return False, metadata, errors

def validate_injection_batch(file_paths: List[str]) -> Dict[str, Any]:
    """
    Validate a batch of injection files.
    
    Args:
        file_paths: List of paths to HDF5 files
        
    Returns:
        Dictionary with validation results summary
    """
    results = {
        'total_files': len(file_paths),
        'valid_files': 0,
        'invalid_files': 0,
        'valid_paths': [],
        'invalid_paths': [],
        'errors_by_file': {}
    }
    
    for file_path in file_paths:
        is_valid, metadata, errors = validate_file(file_path)
        
        if is_valid:
            results['valid_files'] += 1
            results['valid_paths'].append(file_path)
        else:
            results['invalid_files'] += 1
            results['invalid_paths'].append(file_path)
            results['errors_by_file'][file_path] = errors
    
    return results