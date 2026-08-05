"""
Validation module for defect chemistry and ionic conductivity analysis.
Implements BVS validation, Li-O distance constraints, and dataset completeness checks.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from sibling modules using the defined API surface
try:
    from utils import setup_logging
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import setup_logging

# Constants
IDEAL_LI_O_DISTANCE_MIN = 1.9  # Angstroms
IDEAL_LI_O_DISTANCE_MAX = 2.1  # Angstroms
BVS_DEVIATION_THRESHOLD = 0.10  # 10%
VALIDATION_LOG_PATH = "data/processed/validation_log.txt"

# Initialize logger
logger = setup_logging(__name__)

def load_structures_metadata(metadata_path: str = "data/processed/structures_metadata.json") -> List[Dict[str, Any]]:
    """
    Load structure metadata from the processed data directory.
    """
    path = Path(metadata_path)
    if not path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return []

    with open(path, 'r') as f:
        data = json.load(f)

    if isinstance(data, dict) and 'structures' in data:
        return data['structures']
    elif isinstance(data, list):
        return data
    else:
        logger.warning(f"Unexpected metadata format in {metadata_path}")
        return []

def load_download_summary(summary_path: str = "data/processed/download_summary.json") -> Dict[str, Any]:
    """
    Load the download summary report.
    """
    path = Path(summary_path)
    if not path.exists():
        logger.warning(f"Download summary not found: {summary_path}")
        return {"total": 0, "successful": 0, "failed": 0}

    with open(path, 'r') as f:
        return json.load(f)

def validate_bond_valence_sum(structures: List[Dict[str, Any]], log_violations: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate Bond-Valence Sum (BVS) for all structures.
    Filters out structures where BVS deviates >10% from ideal oxidation states.

    Args:
        structures: List of structure dictionaries with 'composition_id' and 'bvs_deviation'
        log_violations: If True, log violations to the validation log file

    Returns:
        Tuple of (valid_structures, violations)
    """
    valid = []
    violations = []

    for struct in structures:
        comp_id = struct.get('composition_id', 'unknown')
        bvs_dev = struct.get('bvs_deviation', 1.0)  # Default to failure if missing

        if bvs_dev <= BVS_DEVIATION_THRESHOLD:
            valid.append(struct)
        else:
            violation = {
                "violation_type": "BVS_DEVIATION",
                "composition_id": comp_id,
                "value": bvs_dev,
                "threshold": BVS_DEVIATION_THRESHOLD,
                "ideal_range": f"<= {BVS_DEVIATION_THRESHOLD*100}%"
            }
            violations.append(violation)
            if log_violations:
                logger.warning(f"BVS Violation for {comp_id}: {bvs_dev:.4f} > {BVS_DEVIATION_THRESHOLD}")

    if log_violations and violations:
        _write_violations_to_log(violations)

    return valid, violations

def validate_li_o_distance(structures: List[Dict[str, Any]], log_violations: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate Li-O bond distances against ideal ranges.
    Mandated by FR-002 and Section 3.2 (Linus Pauling review).

    Args:
        structures: List of structure dictionaries with 'composition_id' and 'li_o_distances'
        log_violations: If True, log violations to the validation log file

    Returns:
        Tuple of (valid_structures, violations)
    """
    valid = []
    violations = []

    for struct in structures:
        comp_id = struct.get('composition_id', 'unknown')
        distances = struct.get('li_o_distances', [])

        # Check if any distance is outside the ideal range
        has_violation = False
        min_dist = float('inf')
        max_dist = float('-inf')

        for d in distances:
            if d < IDEAL_LI_O_DISTANCE_MIN or d > IDEAL_LI_O_DISTANCE_MAX:
                has_violation = True
                min_dist = min(min_dist, d)
                max_dist = max(max_dist, d)

        if not has_violation:
            valid.append(struct)
        else:
            # Determine the specific distance that caused the violation
            # If min_dist is still inf, it means no distances were found
            if min_dist == float('inf'):
                violation_distance = 0.0
            elif min_dist < IDEAL_LI_O_DISTANCE_MIN:
                violation_distance = min_dist
            else:
                violation_distance = max_dist

            violation = {
                "violation_type": "LI_O_DISTANCE",
                "composition_id": comp_id,
                "distance": violation_distance,
                "ideal_range": f"{IDEAL_LI_O_DISTANCE_MIN}-{IDEAL_LI_O_DISTANCE_MAX} Angstroms"
            }
            violations.append(violation)
            if log_violations:
                logger.warning(f"Li-O Distance Violation for {comp_id}: {violation_distance:.3f} Å outside {IDEAL_LI_O_DISTANCE_MIN}-{IDEAL_LI_O_DISTANCE_MAX} Å")

    if log_violations and violations:
        _write_violations_to_log(violations)

    return valid, violations

def _write_violations_to_log(violations: List[Dict[str, Any]], log_path: str = VALIDATION_LOG_PATH):
    """
    Write violations to the validation log file in JSON Lines format.
    Creates the directory if it doesn't exist.
    """
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'a') as f:
        for v in violations:
            f.write(json.dumps(v) + '\n')

    logger.info(f"Wrote {len(violations)} violations to {log_path}")

def validate_dataset_completeness(structures: List[Dict[str, Any]], required_vars: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Check for required variables in the dataset.
    Required variables: vacancy, interstitial, antisite, migration_barrier, conductivity

    Args:
        structures: List of structure dictionaries
        required_vars: Optional list of required variable names

    Returns:
        Completeness report dictionary
    """
    if required_vars is None:
        required_vars = ['vacancy', 'interstitial', 'antisite', 'migration_barrier', 'conductivity']

    report = {
        "total_structures": len(structures),
        "completeness": {},
        "missing_data": []
    }

    for var in required_vars:
        count = 0
        missing_ids = []
        for struct in structures:
            if var in struct and struct[var] is not None:
                count += 1
            else:
                missing_ids.append(struct.get('composition_id', 'unknown'))

        completeness = (count / len(structures) * 100) if structures else 0
        report["completeness"][var] = {
            "count": count,
            "percentage": completeness,
            "missing_ids": missing_ids
        }

        if completeness < 100:
            report["missing_data"].append({
                "variable": var,
                "missing_count": len(missing_ids)
            })

    return report

def main():
    """
    Main entry point for validation.
    Runs BVS and Li-O distance validation, then generates a completeness report.
    """
    logger.info("Starting validation pipeline...")

    # Load structures
    structures = load_structures_metadata()
    if not structures:
        logger.error("No structures found to validate. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded {len(structures)} structures for validation.")

    # Clear previous log file for this run (optional, but ensures clean state)
    log_path = Path(VALIDATION_LOG_PATH)
    if log_path.exists():
        log_path.unlink()
        logger.info(f"Cleared previous validation log: {VALIDATION_LOG_PATH}")

    # Run BVS validation
    logger.info("Running Bond-Valence Sum (BVS) validation...")
    bvs_valid, bvs_violations = validate_bond_valence_sum(structures, log_violations=True)
    logger.info(f"BVS Validation: {len(bvs_valid)} valid, {len(bvs_violations)} violations.")

    # Run Li-O distance validation
    logger.info("Running Li-O distance validation...")
    li_o_valid, li_o_violations = validate_li_o_distance(structures, log_violations=True)
    logger.info(f"Li-O Distance Validation: {len(li_o_valid)} valid, {len(li_o_violations)} violations.")

    # Determine final valid set (intersection of both validations)
    valid_ids = {s['composition_id'] for s in bvs_valid} & {s['composition_id'] for s in li_o_valid}
    final_valid = [s for s in structures if s['composition_id'] in valid_ids]

    logger.info(f"Final valid structures after both checks: {len(final_valid)}")

    # Generate completeness report
    logger.info("Generating dataset completeness report...")
    completeness_report = validate_dataset_completeness(final_valid)

    # Save completeness report
    report_path = Path("data/processed/completeness_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(completeness_report, f, indent=2)
    logger.info(f"Completeness report saved to {report_path}")

    # Verification: Ensure log file exists and is valid JSON lines
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    json.loads(line.strip()) # Verify JSON
            logger.info(f"Verification passed: {VALIDATION_LOG_PATH} contains valid JSON lines.")
        except json.JSONDecodeError as e:
            logger.error(f"Verification FAILED: Invalid JSON in {VALIDATION_LOG_PATH}: {e}")
            sys.exit(1)
    else:
        # If no violations, the file might not exist if we didn't create it
        # But the task requires the file to exist. Create empty if no violations.
        if not (bvs_violations or li_o_violations):
            log_path.touch()
            logger.info(f"No violations found. Created empty log file: {VALIDATION_LOG_PATH}")
        else:
            logger.error(f"Verification FAILED: {VALIDATION_LOG_PATH} does not exist.")
            sys.exit(1)

    logger.info("Validation pipeline completed successfully.")

if __name__ == "__main__":
    main()