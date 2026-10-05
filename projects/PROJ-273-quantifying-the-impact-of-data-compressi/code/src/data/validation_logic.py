"""
Logic for validating injection metadata.
Implements T019.1 Step 2: validate_injection(injection_data).

Specifically checks for 'true_parameters' and 'tilt_angle' as per FR-009.
"""
import json
import os
import numpy as np
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_KEYS = ['true_parameters']
REQUIRED_SPIN_KEYS = ['tilt_angle']

def check_true_parameters_exist(metadata: Dict[str, Any]) -> bool:
    """
    Check if 'true_parameters' exists in metadata.
    """
    return 'true_parameters' in metadata

def check_spin_metadata_complete(true_params: Dict[str, Any]) -> bool:
    """
    Check if spin metadata (specifically tilt_angle) is complete.
    Per FR-009: 'tilt_angle' must be present.
    """
    if not isinstance(true_params, dict):
        return False
    
    for key in REQUIRED_SPIN_KEYS:
        if key not in true_params:
            logger.warning(f"Missing required spin metadata key: {key}")
            return False
        
        value = true_params[key]
        if value is None:
            logger.warning(f"Spin metadata key '{key}' is None")
            return False
            
    return True

def validate_injection(injection_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate an injection file and its metadata.
    
    Args:
        injection_data: Dictionary containing 'injected_path' and 'metadata_path'.
        
    Returns:
        Tuple of (is_valid, reason).
    """
    metadata_path = injection_data.get('metadata_path')
    
    if not metadata_path or not Path(metadata_path).exists():
        return False, "Metadata file missing"
        
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        return False, f"Failed to load metadata: {e}"
        
    # Check for true_parameters
    if not check_true_parameters_exist(metadata):
        return False, "Missing 'true_parameters' in metadata"
        
    true_params = metadata['true_parameters']
    
    # Check for complete spin metadata (tilt_angle)
    if not check_spin_metadata_complete(true_params):
        return False, "Incomplete spin metadata (missing tilt_angle)"
        
    # Check for SNR > 8 (optional but good practice)
    snr = metadata.get('snr', 0)
    if snr <= 8:
        return False, f"SNR too low: {snr} (threshold: 8)"
        
    return True, "Valid"

def validate_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate a single injected event file (expects metadata.json sidecar).
    """
    meta_path = file_path.parent / f"{file_path.stem}_metadata.json"
    
    injection_data = {
        'injected_path': str(file_path),
        'metadata_path': str(meta_path)
    }
    
    return validate_injection(injection_data)

def validate_batch(event_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate a batch of events.
    
    Returns:
        List of valid events with their validation results.
    """
    valid_events = []
    
    for event in event_list:
        is_valid, reason = validate_injection(event)
        event['is_valid'] = is_valid
        event['validation_reason'] = reason
        
        if is_valid:
            valid_events.append(event)
            
    return valid_events
