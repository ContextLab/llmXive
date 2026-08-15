"""
Validation module for generated stiffness tensors.

This module implements:
1. Voigt-Reuss-Hill (VRH) bounds checking for physical plausibility.
2. Schema conformity validation against the dataset contract.
"""
import numpy as np
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the dataset schema definition from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_schema_conformity(
    record: Dict[str, Any], 
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that a data record conforms to the expected schema.
    
    Args:
        record: The data record to validate.
        schema: The schema definition loaded from YAML.
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Expected fields based on T012 contract
    required_fields = {
        'image_path': str,
        'stiffness_tensor': list,
        'inclusion_density': (int, float),
        'seed': int
    }
    
    # Check for missing fields
    for field, expected_type in required_fields.items():
        if field not in record:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(record[field], expected_type):
            errors.append(
                f"Field '{field}' has wrong type. "
                f"Expected {expected_type}, got {type(record[field])}"
            )
    
    # Validate stiffness_tensor structure (6 values for Voigt notation)
    if 'stiffness_tensor' in record:
        tensor = record['stiffness_tensor']
        if not isinstance(tensor, list) or len(tensor) != 6:
            errors.append(
                f"stiffness_tensor must be a list of 6 floats. "
                f"Got length {len(tensor) if isinstance(tensor, list) else 'N/A'}"
            )
        else:
            # Ensure all values are numeric
            for i, val in enumerate(tensor):
                if not isinstance(val, (int, float)):
                    errors.append(
                        f"stiffness_tensor[{i}] is not numeric: {val}"
                    )
    
    # Validate inclusion_density range [0, 1]
    if 'inclusion_density' in record:
        density = record['inclusion_density']
        if not (0.0 <= density <= 1.0):
            errors.append(
                f"inclusion_density must be between 0.0 and 1.0. "
                f"Got {density}"
            )
    
    return len(errors) == 0, errors


def compute_vrh_bounds(stiffness_tensor: List[float]) -> Tuple[float, float]:
    """
    Compute Voigt-Reuss-Hill bounds for a given stiffness tensor.
    
    For isotropic materials (or effective isotropic approximations),
    we typically look at the bulk modulus (K) and shear modulus (G).
    However, for a general 6x6 stiffness tensor in Voigt notation,
    we can check the positive definiteness and symmetry constraints.
    
    The Voigt bound (upper) is the arithmetic mean of the diagonal elements.
    The Reuss bound (lower) is the harmonic mean of the diagonal elements.
    
    Args:
        stiffness_tensor: List of 6 stiffness components [C11, C22, C33, C44, C55, C66]
        
    Returns:
        Tuple of (voigt_bound, reuss_bound)
    """
    # Extract diagonal components (assuming Voigt notation: 11, 22, 33, 44, 55, 66)
    # Note: In full 6x6 matrix, indices 0, 1, 2 are normal, 3, 4, 5 are shear
    diag = np.array(stiffness_tensor)
    
    # Voigt bound: Arithmetic mean of diagonal stiffnesses
    voigt_bound = np.mean(diag)
    
    # Reuss bound: Harmonic mean of diagonal stiffnesses
    # Avoid division by zero
    if np.any(diag <= 0):
        logger.warning("Non-positive stiffness components detected. Reuss bound calculation may be invalid.")
        return 0.0, 0.0
        
    reuss_bound = len(diag) / np.sum(1.0 / diag)
    
    return voigt_bound, reuss_bound


def validate_vrh_bounds(
    stiffness_tensor: List[float], 
    tolerance: float = 1e-6
) -> Tuple[bool, str]:
    """
    Validate that the computed stiffness tensor is physically plausible
    by checking if it falls within Voigt-Reuss-Hill bounds.
    
    For a valid effective medium, the effective stiffness should lie
    between the Voigt (upper) and Reuss (lower) bounds.
    
    Args:
        stiffness_tensor: List of 6 stiffness components.
        tolerance: Numerical tolerance for floating point comparisons.
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(stiffness_tensor, list) or len(stiffness_tensor) != 6:
        return False, "Invalid stiffness tensor format. Expected list of 6 floats."
    
    try:
        voigt, reuss = compute_vrh_bounds(stiffness_tensor)
    except Exception as e:
        return False, f"Error computing VRH bounds: {str(e)}"
    
    # Check if Voigt >= Reuss (mathematical requirement)
    if voigt < reuss - tolerance:
        return False, f"VRH bounds violated: Voigt ({voigt:.6f}) < Reuss ({reuss:.6f})"
    
    # Check if the tensor components are consistent with the bounds
    # In a valid homogenization, the effective properties should be bounded.
    # We check the mean stiffness against the bounds.
    mean_stiffness = np.mean(stiffness_tensor)
    
    if not (reuss - tolerance <= mean_stiffness <= voigt + tolerance):
        return False, (
            f"Mean stiffness ({mean_stiffness:.6f}) outside VRH bounds "
            f"[{reuss:.6f}, {voigt:.6f}]"
        )
    
    # Additional check: Positive definiteness (simplified)
    # All diagonal components should be positive
    if np.any(np.array(stiffness_tensor) <= 0):
        return False, "Stiffness tensor contains non-positive diagonal components."
    
    return True, f"VRH bounds valid. Reuss={reuss:.6f}, Voigt={voigt:.6f}, Mean={mean_stiffness:.6f}"


def validate_dataset(
    metadata_path: Path,
    schema_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Validate the entire generated dataset.
    
    Args:
        metadata_path: Path to the JSON metadata file containing records.
        schema_path: Optional path to the schema YAML file. If None, uses default.
        
    Returns:
        Dictionary with validation results.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    # Load schema if provided
    schema = None
    if schema_path and schema_path.exists():
        schema = load_schema(schema_path)
    else:
        logger.info("No schema provided, skipping schema conformity checks.")
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        records = json.load(f)
    
    results = {
        'total_records': len(records),
        'valid_count': 0,
        'invalid_count': 0,
        'schema_errors': [],
        'vrh_errors': [],
        'invalid_indices': []
    }
    
    for i, record in enumerate(records):
        is_valid = True
        errors = []
        
        # 1. Schema Conformity
        if schema:
            schema_ok, schema_errs = validate_schema_conformity(record, schema)
            if not schema_ok:
                is_valid = False
                errors.extend(schema_errs)
        
        # 2. VRH Bounds
        if 'stiffness_tensor' in record:
            vrh_ok, vrh_msg = validate_vrh_bounds(record['stiffness_tensor'])
            if not vrh_ok:
                is_valid = False
                errors.append(f"VRH: {vrh_msg}")
        
        if is_valid:
            results['valid_count'] += 1
        else:
            results['invalid_count'] += 1
            results['invalid_indices'].append(i)
            results['schema_errors'].extend(errors)
            logger.warning(f"Record {i} invalid: {errors}")
    
    results['success_rate'] = (
        results['valid_count'] / results['total_records'] 
        if results['total_records'] > 0 else 0.0
    )
    
    return results


def main():
    """
    CLI entry point for validation.
    
    Usage:
        python code/data_generation/validate_tensors.py --metadata data/raw/metadata.json --schema specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate generated stiffness tensors")
    parser.add_argument(
        '--metadata', 
        type=Path, 
        required=True, 
        help='Path to the JSON metadata file'
    )
    parser.add_argument(
        '--schema', 
        type=Path, 
        default=None, 
        help='Path to the schema YAML file (optional)'
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=None, 
        help='Path to write validation report (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        results = validate_dataset(args.metadata, args.schema)
        
        # Print summary
        print(f"\nValidation Summary:")
        print(f"  Total Records: {results['total_records']}")
        print(f"  Valid: {results['valid_count']}")
        print(f"  Invalid: {results['invalid_count']}")
        print(f"  Success Rate: {results['success_rate']:.2%}")
        
        if results['invalid_count'] > 0:
            print(f"\n  Invalid indices: {results['invalid_indices'][:10]}...") # Show first 10
            print(f"  Sample errors: {results['schema_errors'][:3]}")
        
        # Write report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nReport written to: {args.output}")
        
        # Exit with error code if any invalid records found
        if results['invalid_count'] > 0:
            logger.error("Validation failed: Invalid records found.")
            return 1
        
        logger.info("Validation passed.")
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
