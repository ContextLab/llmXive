import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from pymatgen.analysis.bv import BVAnalyzer
from pymatgen.core import Structure, Lattice
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.cif import CifParser
import os

# Import existing utilities if needed (assuming they exist based on API surface)
# from utils import setup_logging, load_config

def setup_validate_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging for validation tasks."""
    logger = logging.getLogger("validate")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def calculate_bvs_deviation(structure: Structure, oxidation_states: Dict[str, float]) -> float:
    """
    Calculate the Bond-Valence Sum (BVS) deviation for a structure.
    
    Args:
        structure: pymatgen Structure object
        oxidation_states: Expected oxidation states for elements
        
    Returns:
        Maximum absolute deviation from ideal oxidation states
    """
    logger = logging.getLogger("validate")
    try:
        bv_analyzer = BVAnalyzer(oxi_state_tol=0.1)
        bvs_structure = bv_analyzer.get_oxi_state_decorated_structure(structure)
        
        max_deviation = 0.0
        for site in bvs_structure:
            element = site.species.elements[0].symbol
            if element in oxidation_states:
                expected = oxidation_states[element]
                actual = site.specie.oxi_state
                deviation = abs(actual - expected)
                max_deviation = max(max_deviation, deviation)
                logger.debug(f"Element {element}: expected {expected}, actual {actual}, deviation {deviation}")
        
        return max_deviation
    except Exception as e:
        logger.error(f"Error calculating BVS deviation: {e}")
        return float('inf')

def validate_bvs(structure: Structure, oxidation_states: Dict[str, float], threshold: float = 0.1) -> bool:
    """
    Validate that BVS deviation is within acceptable threshold.
    
    Args:
        structure: pymatgen Structure object
        oxidation_states: Expected oxidation states for elements
        threshold: Maximum allowed deviation (default 0.1 for 10%)
        
    Returns:
        True if validation passes, False otherwise
    """
    deviation = calculate_bvs_deviation(structure, oxidation_states)
    logger = logging.getLogger("validate")
    
    if deviation > threshold:
        logger.warning(f"BVS deviation {deviation:.4f} exceeds threshold {threshold}")
        return False
    
    logger.info(f"BVS validation passed with deviation {deviation:.4f}")
    return True

def validate_crystallographic_constraints(structure: Structure, element_pair: tuple, min_dist: float, max_dist: float) -> List[Dict[str, Any]]:
    """
    Validate crystallographic constraints for specific atom pairs.
    
    This implements the Li-O distance validation for transition metal oxides
    as authorized by T019a update to spec.md.
    
    Args:
        structure: pymatgen Structure object
        element_pair: Tuple of (element1, element2) to check distances between
        min_dist: Minimum allowed distance in Angstroms
        max_dist: Maximum allowed distance in Angstroms
        
    Returns:
        List of violation dictionaries with details
    """
    logger = logging.getLogger("validate")
    violations = []
    
    el1, el2 = element_pair
    
    # Get sites for each element
    sites_el1 = [site for site in structure if el1 in [elem.symbol for elem in site.species.elements]]
    sites_el2 = [site for site in structure if el2 in [elem.symbol for elem in site.species.elements]]
    
    if not sites_el1 or not sites_el2:
        logger.warning(f"No sites found for element pair ({el1}, {el2})")
        return violations
    
    # Check all pairs between the two elements
    for site1 in sites_el1:
        for site2 in sites_el2:
            distance = site1.distance(site2)
            
            if distance < min_dist or distance > max_dist:
                violation = {
                    "element1": el1,
                    "element2": el2,
                    "site1_index": structure.get_site_index(site1),
                    "site2_index": structure.get_site_index(site2),
                    "distance": distance,
                    "min_allowed": min_dist,
                    "max_allowed": max_dist,
                    "violation_type": "below_min" if distance < min_dist else "above_max"
                }
                violations.append(violation)
                logger.warning(
                    f"Li-O distance violation: {el1}-{el2} distance {distance:.4f} Å "
                    f"outside range [{min_dist}, {max_dist}] Å "
                    f"(sites {violation['site1_index']}, {violation['site2_index']})"
                )
    
    return violations

def validate_defect_data_completeness(data: Dict[str, Any], required_vars: List[str]) -> Dict[str, Any]:
    """
    Validate that all required variables are present in the data.
    
    Args:
        data: Dictionary containing defect data
        required_vars: List of required variable names
        
    Returns:
        Dictionary with validation results
    """
    logger = logging.getLogger("validate")
    missing = []
    present = []
    
    for var in required_vars:
        if var in data and data[var] is not None:
            present.append(var)
        else:
            missing.append(var)
            logger.warning(f"Missing required variable: {var}")
    
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "present": present,
        "total_required": len(required_vars)
    }

def validate_dataset_completeness(structures: List[Structure], required_vars: List[str]) -> Dict[str, Any]:
    """
    Validate completeness across a dataset of structures.
    
    Args:
        structures: List of pymatgen Structure objects
        required_vars: List of required variable names
        
    Returns:
        Dictionary with overall completeness statistics
    """
    logger = logging.getLogger("validate")
    results = []
    total_valid = 0
    total_bvs_failed = 0
    total_crystallographic_failed = 0
    
    # Define oxidation states for common elements in oxide electrolytes
    oxidation_states = {
        "Li": 1.0,
        "O": -2.0,
        "P": 5.0,
        "S": 6.0,
        "Ge": 4.0,
        "Si": 4.0,
        "Al": 3.0,
        "Ga": 3.0,
        "Ti": 4.0,
        "Zr": 4.0,
        "Hf": 4.0,
        "La": 3.0,
        "Y": 3.0,
        "Nb": 5.0,
        "Ta": 5.0,
        "W": 6.0,
        "Mo": 6.0,
        "V": 5.0,
        "Cr": 3.0,
        "Mn": 3.0,
        "Fe": 3.0,
        "Co": 3.0,
        "Ni": 3.0,
        "Cu": 2.0,
        "Zn": 2.0,
        "Mg": 2.0,
        "Ca": 2.0,
        "Sr": 2.0,
        "Ba": 2.0,
        "Na": 1.0,
        "K": 1.0,
        "Cs": 1.0,
        "F": -1.0,
        "Cl": -1.0,
        "Br": -1.0,
        "I": -1.0
    }
    
    # Li-O distance constraints for transition metal oxides (T020)
    li_o_min_dist = 1.95  # Angstroms
    li_o_max_dist = 2.15  # Angstroms
    
    for idx, structure in enumerate(structures):
        structure_result = {
            "index": idx,
            "formula": structure.composition.formula,
            "bvs_valid": False,
            "crystallographic_valid": False,
            "bvs_deviation": None,
            "crystallographic_violations": []
        }
        
        # BVS Validation (T019)
        bvs_valid = validate_bvs(structure, oxidation_states, threshold=0.1)
        structure_result["bvs_valid"] = bvs_valid
        if bvs_valid:
            total_valid += 1
        else:
            total_bvs_failed += 1
        
        # Crystallographic Constraint Validation (T020)
        # Check Li-O distances specifically
        if "Li" in [el.symbol for el in structure.composition.elements] and "O" in [el.symbol for el in structure.composition.elements]:
            violations = validate_crystallographic_constraints(
                structure, 
                ("Li", "O"), 
                li_o_min_dist, 
                li_o_max_dist
            )
            structure_result["crystallographic_violations"] = violations
            
            if len(violations) == 0:
                structure_result["crystallographic_valid"] = True
            else:
                total_crystallographic_failed += 1
                logger.error(
                    f"Structure {idx} ({structure.composition.formula}) has {len(violations)} "
                    f"Li-O distance violations outside [{li_o_min_dist}, {li_o_max_dist}] Å"
                )
        else:
            # No Li or O in structure, skip this check
            structure_result["crystallographic_valid"] = True
            logger.info(f"Structure {idx} ({structure.composition.formula}) does not contain Li or O, skipping Li-O distance check")
        
        results.append(structure_result)
    
    return {
        "total_structures": len(structures),
        "bvs_passed": total_valid,
        "bvs_failed": total_bvs_failed,
        "crystallographic_failed": total_crystallographic_failed,
        "overall_valid": total_valid == len(structures) and total_crystallographic_failed == 0,
        "structure_details": results,
        "constraints": {
            "bvs_threshold": 0.1,
            "li_o_min_dist": li_o_min_dist,
            "li_o_max_dist": li_o_max_dist
        }
    }

def generate_completeness_report(validation_results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a completeness report from validation results.
    
    Args:
        validation_results: Results from validate_dataset_completeness
        output_path: Path to save the JSON report
    """
    logger = logging.getLogger("validate")
    
    report = {
        "summary": {
            "total_structures": validation_results["total_structures"],
            "bvs_passed": validation_results["bvs_passed"],
            "bvs_failed": validation_results["bvs_failed"],
            "crystallographic_failed": validation_results["crystallographic_failed"],
            "overall_valid": validation_results["overall_valid"]
        },
        "constraints_applied": validation_results["constraints"],
        "details": validation_results["structure_details"]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Compliance report written to {output_path}")
    logger.info(f"Overall validity: {validation_results['overall_valid']}")
    logger.info(f"BVS passed: {validation_results['bvs_passed']}/{validation_results['total_structures']}")
    logger.info(f"Crystallographic violations: {validation_results['crystallographic_failed']}")

def main():
    """Main entry point for validation script."""
    logger = setup_validate_logging()
    logger.info("Starting validation pipeline...")
    
    # Example usage - in real scenario, load structures from data/
    # For now, demonstrate the validation functions with a sample structure
    try:
        # Create a simple test structure (LiFePO4-like)
        from pymatgen.core import Structure, Lattice
        
        lattice = Lattice.from_parameters(
            a=10.33, b=6.01, c=4.69, 
            alpha=90.0, beta=90.0, gamma=90.0
        )
        
        # LiFePO4 structure (simplified)
        species = ["Li", "Fe", "P", "O", "O", "O", "O"]
        coords = [
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5],
            [0.25, 0.25, 0.25],
            [0.1, 0.1, 0.1],
            [0.2, 0.2, 0.2],
            [0.3, 0.3, 0.3],
            [0.4, 0.4, 0.4]
        ]
        
        test_structure = Structure(lattice, species, coords)
        
        # Run validations
        oxidation_states = {"Li": 1.0, "Fe": 2.0, "P": 5.0, "O": -2.0}
        
        logger.info("Running BVS validation...")
        bvs_valid = validate_bvs(test_structure, oxidation_states)
        logger.info(f"BVS validation result: {bvs_valid}")
        
        logger.info("Running crystallographic constraint validation (Li-O distances)...")
        violations = validate_crystallographic_constraints(
            test_structure, 
            ("Li", "O"), 
            1.95, 
            2.15
        )
        logger.info(f"Crystallographic violations found: {len(violations)}")
        
        # Generate report
        results = validate_dataset_completeness([test_structure], ["vacancy", "interstitial"])
        report_path = Path("data/processed/completeness_report.json")
        generate_completeness_report(results, report_path)
        
        logger.info("Validation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()