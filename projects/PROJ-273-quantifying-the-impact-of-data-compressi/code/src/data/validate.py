"""
Validation module for injected GW data.
Checks for required metadata fields, specifically 'true_parameters' for synthetic injections.
"""
import json
import os
from pathlib import Path
from typing import Tuple, Any, Dict

def check_true_parameters_exist(filepath: str) -> bool:
    """
    Check if the given JSON file contains 'true_parameters'.
    
    Args:
        filepath: Path to the metadata JSON file.
        
    Returns:
        True if 'true_parameters' key exists and is a dict, False otherwise.
    """
    try:
        with open(filepath, 'r') as f:
            metadata = json.load(f)
        
        if 'true_parameters' not in metadata:
            return False
        
        if not isinstance(metadata['true_parameters'], dict):
            return False
            
        # Verify specific required ground truth fields per FR-008/FR-009
        required_keys = ['mass_1', 'mass_2', 'distance', 'spin_1', 'spin_2']
        for key in required_keys:
            if key not in metadata['true_parameters']:
                return False
                
        # Verify spin structure (tilt/azimuth)
        for spin_key in ['spin_1', 'spin_2']:
            spin_data = metadata['true_parameters'][spin_key]
            if 'tilt' not in spin_data or 'azimuth' not in spin_data:
                return False
                
        return True
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return False

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate that the metadata dictionary contains 'true_parameters'.
    
    Args:
        metadata: Dictionary containing event metadata.
        
    Returns:
        True if 'true_parameters' is present and valid, False otherwise.
    """
    if not isinstance(metadata, dict):
        return False
        
    if 'true_parameters' not in metadata:
        return False
        
    if not isinstance(metadata['true_parameters'], dict):
        return False
        
    # Check for essential ground truth keys
    required_keys = ['mass_1', 'mass_2', 'distance', 'spin_1', 'spin_2']
    for key in required_keys:
        if key not in metadata['true_parameters']:
            return False
            
    # Verify spin metadata structure
    for spin_key in ['spin_1', 'spin_2']:
        spin_data = metadata['true_parameters'][spin_key]
        if not isinstance(spin_data, dict):
            return False
        if 'tilt' not in spin_data or 'azimuth' not in spin_data:
            return False
            
    return True

def validate_file(filepath: str) -> Tuple[bool, str]:
    """
    Full validation of a metadata file.
    
    Args:
        filepath: Path to the metadata JSON file.
        
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
        
    try:
        with open(filepath, 'r') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
        
    if not validate_metadata(metadata):
        return False, "Missing or invalid 'true_parameters' in metadata"
        
    # Additional checks for basic event info
    if 'event_id' not in metadata:
        return False, "Missing 'event_id'"
    if 'detector' not in metadata:
        return False, "Missing 'detector'"
    if 'timestamp' not in metadata:
        return False, "Missing 'timestamp'"
        
    return True, "Validation successful"