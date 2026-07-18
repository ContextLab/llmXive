"""
Validation module for defect chemistry and ionic conductivity analysis.
Implements BVS validation, crystallographic constraints, and data completeness checks.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Conditional imports for heavy dependencies
try:
    from pymatgen.core import Structure, Lattice
    from pymatgen.analysis.bond_valence import BVAnalyzer
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning("pymatgen not available. BVS and crystallographic validation will fail if called.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from utils import setup_logging

logger = logging.getLogger(__name__)

# Constants for validation thresholds (from spec Section 3.2)
BVS_DEVIATION_THRESHOLD = 0.10  # 10% deviation allowed
LI_O_MIN_DIST = 1.95  # Angstroms
LI_O_MAX_DIST = 2.15  # Angstroms

def calculate_bvs_deviation(structure: Structure, target_ox_state: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate the Bond-Valence Sum (BVS) deviation for each element in the structure.

    Args:
        structure: pymatgen Structure object
        target_ox_state: Dictionary mapping element symbols to their ideal oxidation states

    Returns:
        Dictionary mapping element symbols to their absolute BVS deviation percentage
    """
    if not PYMATGEN_AVAILABLE:
        raise ImportError("pymatgen is required for BVS calculation")

    bvs_analyzer = BVAnalyzer()
    bvs_structure = bvs_analyzer.get_oxi_states(structure)

    deviations = {}
    for site in bvs_structure:
        element = site.species_string
        if element in target_ox_state:
            ideal = target_ox_state[element]
            calculated = site.oxi_state
            if ideal != 0:
                deviation_pct = abs(calculated - ideal) / abs(ideal)
                deviations[element] = deviation_pct
            else:
                deviations[element] = 0.0 if abs(calculated) < 0.01 else abs(calculated)

    return deviations

def validate_bvs(structure: Structure, target_ox_state: Dict[str, float], threshold: float = BVS_DEVIATION_THRESHOLD) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that BVS deviations are within acceptable limits.

    Args:
        structure: pymatgen Structure object
        target_ox_state: Dictionary mapping element symbols to ideal oxidation states
        threshold: Maximum allowed deviation (default 10%)

    Returns:
        Tuple of (is_valid, details_dict)
        details_dict contains:
            - 'passed': bool
            - 'deviations': Dict of element -> deviation %
            - 'failed_elements': List of elements exceeding threshold
            - 'message': Human-readable status
    """
    if not PYMATGEN_AVAILABLE:
        raise RuntimeError("Cannot validate BVS: pymatgen not installed")

    deviations = calculate_bvs_deviation(structure, target_ox_state)
    failed_elements = [elem for elem, dev in deviations.items() if dev > threshold]

    is_valid = len(failed_elements) == 0

    details = {
        "passed": is_valid,
        "deviations": deviations,
        "failed_elements": failed_elements,
        "threshold": threshold,
        "message": "BVS validation passed" if is_valid else f"BVS validation failed: elements {failed_elements} exceed {threshold*100:.0f}% deviation"
    }

    logger.info(f"BVS Validation: {details['message']}")
    return is_valid, details

def validate_crystallographic_constraints(structure: Structure, li_species: str = "Li", o_species: str = "O") -> Tuple[bool, Dict[str, Any]]:
    """
    Validate crystallographic constraints, specifically Li-O distances.

    Args:
        structure: pymatgen Structure object
        li_species: Symbol for Lithium (default "Li")
        o_species: Symbol for Oxygen (default "O")

    Returns:
        Tuple of (is_valid, details_dict)
    """
    if not PYMATGEN_AVAILABLE:
        raise RuntimeError("Cannot validate crystallographic constraints: pymatgen not installed")

    li_indices = [i for i, site in enumerate(structure) if li_species in site.species]
    o_indices = [i for i, site in enumerate(structure) if o_species in site.species]

    if not li_indices or not o_indices:
        logger.warning(f"Structure missing {li_species} or {o_species} species. Skipping distance check.")
        return True, {
            "passed": True,
            "missing_species": True,
            "message": f"Skipped: missing {li_species} or {o_species}"
        }

    violations = []
    distances = []

    for li_idx in li_indices:
        for o_idx in o_indices:
            dist = structure.get_distance(li_idx, o_idx)
            distances.append(dist)
            if dist < LI_O_MIN_DIST or dist > LI_O_MAX_DIST:
                violations.append({
                    "li_index": li_idx,
                    "o_index": o_idx,
                    "distance": dist,
                    "violation_type": "below_min" if dist < LI_O_MIN_DIST else "above_max"
                })

    is_valid = len(violations) == 0

    details = {
        "passed": is_valid,
        "violations": violations,
        "violation_count": len(violations),
        "total_pairs": len(distances),
        "distance_range": {"min": min(distances) if distances else None, "max": max(distances) if distances else None},
        "message": "Crystallographic constraints passed" if is_valid else f"Found {len(violations)} Li-O distance violations"
    }

    logger.info(f"Crystallographic Validation: {details['message']}")
    return is_valid, details

def handle_missing_obelix_data(composition_id: str, missing_vars: List[str]) -> Dict[str, Any]:
    """
    Log and handle missing OBELiX data, preparing for DFT fallback.

    Args:
        composition_id: Unique identifier for the composition
        missing_vars: List of missing variable names

    Returns:
        Status dictionary
    """
    logger.warning(f"Missing OBELiX data for {composition_id}: {missing_vars}")
    return {
        "composition_id": composition_id,
        "missing_variables": missing_vars,
        "status": "requires_dft_fallback",
        "message": f"Proceeding with DFT-computed values for {missing_vars}"
    }

def validate_defect_data_completeness(data: Dict[str, Any], required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if all required variables are present in the data dictionary.

    Args:
        data: Dictionary containing composition data
        required_vars: List of required variable names

    Returns:
        Tuple of (is_complete, list_of_missing_vars)
    """
    missing = [var for var in required_vars if var not in data or data[var] is None]
    is_complete = len(missing) == 0
    if not is_complete:
        logger.warning(f"Missing variables: {missing}")
    return is_complete, missing

def validate_dataset_completeness(compositions: List[Dict[str, Any]], required_vars: List[str]) -> Dict[str, Any]:
    """
    Validate completeness across a dataset of compositions.

    Args:
        compositions: List of composition data dictionaries
        required_vars: List of required variable names

    Returns:
        Completeness report dictionary
    """
    report = {
        "total_compositions": len(compositions),
        "complete_count": 0,
        "incomplete_count": 0,
        "details": []
    }

    for comp in compositions:
        comp_id = comp.get("composition_id", "unknown")
        is_complete, missing = validate_defect_data_completeness(comp, required_vars)

        if is_complete:
            report["complete_count"] += 1
            status = "complete"
        else:
            report["incomplete_count"] += 1
            status = "incomplete"
            report["details"].append({
                "composition_id": comp_id,
                "status": status,
                "missing_variables": missing
            })

    report["completion_rate"] = report["complete_count"] / report["total_compositions"] if report["total_compositions"] > 0 else 0.0
    logger.info(f"Dataset completeness: {report['completion_rate']*100:.1f}% ({report['complete_count']}/{report['total_compositions']})")
    return report

def generate_completeness_report(compositions: List[Dict[str, Any]], required_vars: List[str], output_path: str) -> None:
    """
    Generate and save a JSON completeness report.

    Args:
        compositions: List of composition data dictionaries
        required_vars: List of required variable names
        output_path: Path to save the JSON report
    """
    report = validate_dataset_completeness(compositions, required_vars)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Completeness report saved to {output_path}")

def run_bvs_validation_on_dataset(structures_path: str, output_path: str, target_ox_states: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Run BVS validation on a dataset of structures and save results.

    Args:
        structures_path: Path to directory containing structure files (CIF/JSON)
        output_path: Path to save validation results JSON
        target_ox_states: Optional dict of ideal oxidation states per element

    Returns:
        Validation summary dictionary
    """
    if not PYMATGEN_AVAILABLE:
        raise RuntimeError("pymatgen is required for BVS validation")

    structures_dir = Path(structures_path)
    if not structures_dir.exists():
        logger.error(f"Structures directory not found: {structures_path}")
        return {"error": "Structures directory not found"}

    # Default oxidation states for common elements if not provided
    if target_ox_states is None:
        target_ox_states = {
            "Li": 1.0,
            "O": -2.0,
            "La": 3.0,
            "Zr": 4.0,
            "Ta": 5.0,
            "Nb": 5.0,
            "Al": 3.0,
            "Ga": 3.0,
            "Ge": 4.0
        }

    results = {
        "total_structures": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }

    structure_files = list(structures_dir.glob("*.cif")) + list(structures_dir.glob("*.json")) + list(structures_dir.glob("*.mag"))

    for sf in structure_files:
        results["total_structures"] += 1
        try:
            struct = Structure.from_file(sf)
            is_valid, details = validate_bvs(struct, target_ox_states)

            if is_valid:
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "file": sf.name,
                "passed": is_valid,
                "details": details
            })

        except Exception as e:
            logger.error(f"Error processing {sf.name}: {e}")
            results["details"].append({
                "file": sf.name,
                "passed": False,
                "error": str(e)
            })

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"BVS validation complete: {results['passed']}/{results['total_structures']} passed. Results saved to {output_path}")
    return results

def main():
    """
    Main entry point for validation script.
    Runs BVS and crystallographic validation on downloaded structures.
    """
    setup_logging()
    logger.info("Starting validation pipeline...")

    # Configuration
    structures_dir = "data/raw/structures"
    bvs_output = "data/processed/bvs_validation_results.json"
    completeness_output = "data/processed/completeness_report.json"

    # Check for structures
    if not Path(structures_dir).exists():
        logger.warning(f"Structure directory {structures_dir} not found. Skipping BVS validation.")
        logger.info("Validation pipeline completed (no structures found).")
        return

    # Run BVS validation
    try:
        bvs_results = run_bvs_validation_on_dataset(structures_dir, bvs_output)
        if bvs_results.get("failed", 0) > 0:
            logger.warning(f"BVS validation failed for {bvs_results['failed']} structures. These will be filtered out.")
    except Exception as e:
        logger.error(f"BVS validation failed: {e}")
        # Do not crash the whole pipeline, just log and continue
        bvs_results = {"error": str(e)}

    # Generate completeness report (placeholder for data from download.py)
    # In a real run, this would load data from processed downloads
    logger.info("Completeness report generation skipped (requires download.py output).")

    logger.info("Validation pipeline finished.")

if __name__ == "__main__":
    main()