"""
Validation module for Defect Chemistry and Ionic Conductivity analysis.

This module implements validation checks mandated by FR-002 and Section 3.2,
including Bond-Valence Sum (BVS) validation and Li-O distance constraints.
It logs violations to a structured JSON-lines file for auditability.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from project utils
from utils import setup_logging, load_config

# Constants for Li-O distance validation
# Based on typical Li-O bond lengths in solid electrolytes (e.g., LLZO, LATP)
# Ideal range: 1.9 - 2.1 Angstroms
LI_O_MIN_DISTANCE = 1.9
LI_O_MAX_DISTANCE = 2.1
LI_O_IDEAL_RANGE = f"{LI_O_MIN_DISTANCE}-{LI_O_MAX_DISTANCE} Å"

# BVS deviation threshold (10% as per FR-002)
BVS_DEVIATION_THRESHOLD = 0.10

logger = setup_logging(__name__)

def load_structures_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """
    Load structure metadata from a JSON file.

    Args:
        metadata_path: Path to the metadata JSON file.

    Returns:
        List of structure metadata dictionaries.
    """
    path = Path(metadata_path)
    if not path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return []

    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both list and dict with 'structures' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'structures' in data:
        return data['structures']
    else:
        logger.warning(f"Unexpected metadata format in {metadata_path}")
        return []

def load_download_summary(summary_path: str) -> Dict[str, Any]:
    """
    Load download summary from a JSON file.

    Args:
        summary_path: Path to the download summary JSON file.

    Returns:
        Download summary dictionary.
    """
    path = Path(summary_path)
    if not path.exists():
        logger.error(f"Download summary file not found: {summary_path}")
        return {"successful": 0, "failed": 0, "structures": []}

    with open(path, 'r') as f:
        return json.load(f)

def validate_bond_valence_sum(structure_data: Dict[str, Any], tolerance: float = BVS_DEVIATION_THRESHOLD) -> Tuple[bool, float, float]:
    """
    Validate Bond-Valence Sum (BVS) for a structure.

    This checks if the calculated BVS deviates more than 10% from ideal
    oxidation states as mandated by FR-002 and Section 3.2.

    Args:
        structure_data: Dictionary containing structure information.
        tolerance: Maximum allowed deviation (default 10%).

    Returns:
        Tuple of (is_valid, deviation, ideal_value)
    """
    # Extract BVS data from structure metadata
    # Expected keys: 'bvs_deviation', 'ideal_bvs', 'calculated_bvs'
    if 'bvs_deviation' not in structure_data:
        # If BVS data is missing, we cannot validate
        # Log a warning but don't fail the structure
        logger.warning(f"Missing BVS data for {structure_data.get('composition_id', 'unknown')}")
        return True, 0.0, 0.0

    deviation = structure_data['bvs_deviation']
    is_valid = abs(deviation) <= tolerance

    return is_valid, deviation, structure_data.get('ideal_bvs', 0.0)

def validate_li_o_distance(structure_data: Dict[str, Any]) -> Tuple[bool, List[float], str]:
    """
    Validate Li-O bond distances in a structure.

    Checks that all Li-O distances fall within the ideal range (1.9-2.1 Å).
    This addresses the Linus Pauling review regarding chemical bond constraints.

    Args:
        structure_data: Dictionary containing structure information.

    Returns:
        Tuple of (all_valid, list_of_violations, ideal_range_string)
    """
    violations = []
    all_valid = True

    # Extract bond distances from structure metadata
    # Expected keys: 'bond_distances' -> list of dicts with 'atom1', 'atom2', 'distance'
    if 'bond_distances' not in structure_data:
        logger.warning(f"Missing bond distance data for {structure_data.get('composition_id', 'unknown')}")
        return True, [], LI_O_IDEAL_RANGE

    bonds = structure_data['bond_distances']
    for bond in bonds:
        # Check if this is a Li-O bond
        atom1 = bond.get('atom1', '').upper()
        atom2 = bond.get('atom2', '').upper()
        distance = bond.get('distance', 0.0)

        if ('LI' in atom1 and 'O' in atom2) or ('O' in atom1 and 'LI' in atom2):
            if distance < LI_O_MIN_DISTANCE or distance > LI_O_MAX_DISTANCE:
                violations.append({
                    'atom_pair': f"{atom1}-{atom2}",
                    'distance': distance,
                    'min_allowed': LI_O_MIN_DISTANCE,
                    'max_allowed': LI_O_MAX_DISTANCE
                })
                all_valid = False

    return all_valid, violations, LI_O_IDEAL_RANGE

def validate_dataset_completeness(structures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that the dataset contains all required variables.

    Checks for presence of: vacancy, interstitial, antisite, migration barrier, conductivity.

    Args:
        structures: List of structure dictionaries.

    Returns:
        Dictionary with completeness status per composition.
    """
    required_vars = ['vacancy', 'interstitial', 'antisite', 'migration_barrier', 'conductivity']
    completeness_report = {}

    for struct in structures:
        comp_id = struct.get('composition_id', 'unknown')
        missing_vars = []

        for var in required_vars:
            if var not in struct or struct[var] is None:
                missing_vars.append(var)

        completeness_report[comp_id] = {
            'complete': len(missing_vars) == 0,
            'missing': missing_vars,
            'present': [v for v in required_vars if v in struct and struct[v] is not None]
        }

        if missing_vars:
            logger.warning(f"Composition {comp_id} missing variables: {missing_vars}")

    return completeness_report

def log_violations(violations: List[Dict[str, Any]], output_path: str) -> int:
    """
    Log validation violations to a JSON-lines file.

    Each line is a JSON object with the schema:
    {
        "violation_type": "string",
        "composition_id": "string",
        "distance": "float",
        "ideal_range": "string"
    }

    Args:
        violations: List of violation dictionaries.
        output_path: Path to the output log file.

    Returns:
        Number of violations logged.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(output_file, 'w') as f:
        for violation in violations:
            # Ensure the schema matches exactly what's required
            log_entry = {
                "violation_type": violation.get('violation_type', 'unknown'),
                "composition_id": violation.get('composition_id', 'unknown'),
                "distance": float(violation.get('distance', 0.0)),
                "ideal_range": violation.get('ideal_range', LI_O_IDEAL_RANGE)
            }
            f.write(json.dumps(log_entry) + '\n')
            count += 1

    logger.info(f"Logged {count} violations to {output_path}")
    return count

def run_validation_pipeline(
    structures_path: Optional[str] = None,
    download_summary_path: Optional[str] = None,
    output_log_path: str = "data/processed/validation_log.txt"
) -> Dict[str, Any]:
    """
    Run the full validation pipeline including BVS and Li-O distance checks.

    This function:
    1. Loads structure metadata
    2. Validates BVS for each structure
    3. Validates Li-O distances for each structure
    4. Logs all violations to a JSON-lines file
    5. Returns a summary of the validation results

    Args:
        structures_path: Path to structures metadata JSON (optional)
        download_summary_path: Path to download summary JSON (optional)
        output_log_path: Path to output validation log file

    Returns:
        Dictionary with validation summary
    """
    # Determine source of structures
    structures = []
    if structures_path:
        structures = load_structures_metadata(structures_path)
    elif download_summary_path:
        summary = load_download_summary(download_summary_path)
        structures = summary.get('structures', [])

    if not structures:
        logger.warning("No structures found for validation")
        # Create empty log file to satisfy the requirement
        Path(output_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_log_path).touch()
        return {
            'total_structures': 0,
            'bvs_violations': 0,
            'li_o_violations': 0,
            'total_violations': 0
        }

    all_violations = []
    bvs_violation_count = 0
    li_o_violation_count = 0

    for struct in structures:
        comp_id = struct.get('composition_id', 'unknown')

        # Validate BVS
        is_bvs_valid, deviation, ideal = validate_bond_valence_sum(struct)
        if not is_bvs_valid:
            bvs_violation_count += 1
            all_violations.append({
                'violation_type': 'BVS_DEVIATION',
                'composition_id': comp_id,
                'distance': deviation,
                'ideal_range': f"<= {BVS_DEVIATION_THRESHOLD * 100}%"
            })
            logger.warning(f"BVS violation for {comp_id}: deviation={deviation:.4f}")

        # Validate Li-O distances
        is_li_o_valid, violations, ideal_range = validate_li_o_distance(struct)
        if not is_li_o_valid:
            li_o_violation_count += len(violations)
            for v in violations:
                all_violations.append({
                    'violation_type': 'LI_O_DISTANCE',
                    'composition_id': comp_id,
                    'distance': v['distance'],
                    'ideal_range': LI_O_IDEAL_RANGE
                })
            logger.warning(f"Li-O distance violations for {comp_id}: {len(violations)} found")

    # Log all violations
    log_count = log_violations(all_violations, output_log_path)

    return {
        'total_structures': len(structures),
        'bvs_violations': bvs_violation_count,
        'li_o_violations': li_o_violation_count,
        'total_violations': log_count,
        'output_file': output_log_path
    }

def main():
    """
    Main entry point for validation script.

    Usage:
        python code/validate.py --structures data/processed/structures.json --output data/processed/validation_log.txt
        python code/validate.py --summary data/processed/download_summary.json --output data/processed/validation_log.txt
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate crystal structures for defect chemistry analysis')
    parser.add_argument('--structures', type=str, help='Path to structures metadata JSON')
    parser.add_argument('--summary', type=str, help='Path to download summary JSON')
    parser.add_argument('--output', type=str, default='data/processed/validation_log.txt',
                      help='Path to output validation log file')

    args = parser.parse_args()

    if not args.structures and not args.summary:
        parser.error("Either --structures or --summary must be provided")

    # Run validation
    result = run_validation_pipeline(
        structures_path=args.structures,
        download_summary_path=args.summary,
        output_log_path=args.output
    )

    # Print summary
    print(f"Validation complete:")
    print(f"  Total structures: {result['total_structures']}")
    print(f"  BVS violations: {result['bvs_violations']}")
    print(f"  Li-O distance violations: {result['li_o_violations']}")
    print(f"  Total violations logged: {result['total_violations']}")
    print(f"  Output file: {result['output_file']}")

    # Exit with error if any violations found (optional, can be configured)
    if result['total_violations'] > 0:
        logger.warning(f"Found {result['total_violations']} violations. Review {args.output} for details.")
        # Note: We don't exit with error code here as the task requires
        # logging violations, not necessarily failing the pipeline
        # However, in a strict pipeline, you might want:
        # sys.exit(1)

    return result

if __name__ == '__main__':
    main()