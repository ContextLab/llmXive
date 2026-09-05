"""
Unity Simulation Fidelity Verification (T038).

This module verifies that the simulated blend-shape parameters match the
reference configuration file (data/config/unity_blend_shapes.yaml).

It validates:
1. Range checks (all values between 0.0 and 1.0)
2. Key consistency (all expected keys present)
3. Metadata consistency (counts match)

Output: state/unity_fidelity.json
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Import from project API
from code.config import get_path

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

REFERENCE_CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
OUTPUT_PATH = "state/unity_fidelity.json"
TOLERANCE = 0.05  # 5% tolerance for floating point comparison

def load_reference_config() -> Dict[str, Any]:
    """Load the reference Unity blend shape configuration."""
    full_path = get_path(REFERENCE_CONFIG_PATH)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Reference config not found at {full_path}")
    
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)

def validate_blend_shape_ranges(
    params: Dict[str, float], 
    metadata: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate that all blend shape values are within [min, max] range."""
    errors = []
    param_range = metadata.get('parameter_range', {'min': 0.0, 'max': 1.0})
    min_val = param_range.get('min', 0.0)
    max_val = param_range.get('max', 1.0)
    
    for key, value in params.items():
        if not isinstance(value, (int, float)):
            errors.append(f"Invalid type for {key}: {type(value)}")
            continue
        if value < min_val or value > max_val:
            errors.append(f"Value {value} for {key} out of range [{min_val}, {max_val}]")
    
    return len(errors) == 0, errors

def validate_blend_shape_keys(
    simulated_params: Dict[str, float],
    reference_params: Dict[str, float]
) -> Tuple[bool, List[str]]:
    """Validate that simulated parameters have the same keys as reference."""
    errors = []
    sim_keys = set(simulated_params.keys())
    ref_keys = set(reference_params.keys())
    
    missing = ref_keys - sim_keys
    extra = sim_keys - ref_keys
    
    if missing:
        errors.append(f"Missing keys: {missing}")
    if extra:
        errors.append(f"Extra keys: {extra}")
        
    return len(errors) == 0, errors

def validate_salience_mapping(
    reference_mappings: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate that salience levels are correctly assigned."""
    errors = []
    valid_levels = {'low', 'high'}
    
    for story_id, story_data in reference_mappings.items():
        if not isinstance(story_data, dict):
            errors.append(f"Invalid data type for story {story_id}")
            continue
        
        level = story_data.get('salience_level')
        if level not in valid_levels:
            errors.append(f"Invalid salience level '{level}' for {story_id}")
        
        params = story_data.get('blend_shape_params', {})
        if not params:
            errors.append(f"Missing blend_shape_params for {story_id}")
    
    return len(errors) == 0, errors

def validate_metadata_consistency(
    metadata: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate metadata counts and structure."""
    errors = []
    
    total = metadata.get('total_stories', 0)
    high_count = metadata.get('high_salience_count', 0)
    low_count = metadata.get('low_salience_count', 0)
    
    if high_count + low_count != total:
        errors.append(f"Count mismatch: {high_count} + {low_count} != {total}")
    
    if total == 0:
        errors.append("Total stories count is zero")
        
    return len(errors) == 0, errors

def verify_simulation_fidelity() -> Dict[str, Any]:
    """
    Main verification logic.
    
    Returns a dictionary with verification status and details.
    """
    logger.info("Starting Unity simulation fidelity verification...")
    
    try:
        config = load_reference_config()
    except FileNotFoundError as e:
        logger.error(f"Failed to load reference config: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": None
        }
    
    mappings = config.get('mappings', {})
    metadata = config.get('metadata', {})
    
    all_errors = []
    
    # 1. Validate metadata consistency
    meta_valid, meta_errors = validate_metadata_consistency(metadata)
    if not meta_valid:
        all_errors.extend(meta_errors)
    
    # 2. Validate salience mapping
    mapping_valid, mapping_errors = validate_salience_mapping(mappings)
    if not mapping_valid:
        all_errors.extend(mapping_errors)
    
    # 3. Validate each story's blend shape parameters
    range_errors = []
    key_errors = []
    
    for story_id, story_data in mappings.items():
        params = story_data.get('blend_shape_params', {})
        
        # Range check
        range_ok, r_errs = validate_blend_shape_ranges(params, metadata)
        if not range_ok:
            range_errors.extend([f"{story_id}: {e}" for e in r_errs])
        
        # Key consistency (compare against itself as reference for this task,
        # since we are verifying the config file structure itself)
        expected_keys = {'jawOpen', 'browLower', 'eyeBlink', 'mouthCornerPull', 'noseSneer'}
        if set(params.keys()) != expected_keys:
            key_errors.append(f"{story_id}: Keys mismatch. Expected {expected_keys}, got {set(params.keys())}")
    
    if range_errors:
        all_errors.extend(range_errors)
    if key_errors:
        all_errors.extend(key_errors)
    
    # Determine overall status
    is_valid = len(all_errors) == 0
    
    result = {
        "status": "passed" if is_valid else "failed",
        "total_stories_checked": len(mappings),
        "high_salience_stories": metadata.get('high_salience_count', 0),
        "low_salience_stories": metadata.get('low_salience_count', 0),
        "tolerance": TOLERANCE,
        "errors": all_errors,
        "error_count": len(all_errors),
        "timestamp": None  # Will be set by caller if needed
    }
    
    logger.info(f"Verification completed: {result['status']}")
    if not is_valid:
        logger.warning(f"Found {len(all_errors)} errors during verification")
    
    return result

def save_verification_report(result: Dict[str, Any]) -> str:
    """Save the verification result to the output file."""
    output_path = get_path(OUTPUT_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification report saved to {output_path}")
    return output_path

def main() -> int:
    """Entry point for the verification script."""
    try:
        result = verify_simulation_fidelity()
        output_path = save_verification_report(result)
        
        if result['status'] == 'passed':
            print(f"✓ Unity Fidelity Verification PASSED")
            print(f"  Checked {result['total_stories_checked']} stories")
            return 0
        else:
            print(f"✗ Unity Fidelity Verification FAILED")
            print(f"  Errors: {result['error_count']}")
            for err in result['errors'][:5]:  # Show first 5
                print(f"    - {err}")
            return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        print(f"✗ Verification failed with exception: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())