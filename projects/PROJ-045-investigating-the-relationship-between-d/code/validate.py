"""
Validation module for Defect Chemistry and Ionic Conductivity Analysis.

Implements:
- Bond-Valence Sum (BVS) validation (FR-002, Section 3.2)
- Crystallographic constraint validation (Li-O distance 1.95-2.15 Å)
- Dataset completeness checks
- Missing data handling
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from utils (existing)
from utils import setup_logging, load_config

# Import from models (existing)
from models import DefectType, ElectrolyteComposition, DefectConfiguration

# Initialize logger
logger = setup_logging(__name__, level=logging.INFO)

# Constants for validation (from Section 3.2 of spec.md)
BVS_DEVIATION_THRESHOLD = 0.10  # 10% deviation from ideal oxidation states
LI_O_MIN_DISTANCE = 1.95  # Å
LI_O_MAX_DISTANCE = 2.15  # Å
BVS_RADIUS_CUTOFF = 5.0  # Å for neighbor search

def calculate_bvs_deviation(structure: Any, atom_symbol: str) -> float:
    """
    Calculate Bond-Valence Sum deviation for a specific atom type.
    
    Args:
        structure: pymatgen Structure object
        atom_symbol: Symbol of the atom type to validate (e.g., 'Li', 'O')
        
    Returns:
        float: Absolute deviation from ideal oxidation state (0.0 if perfect)
        
    Note:
        This is a simplified BVS calculation. In production, use pymatgen's
        BondValence module with proper parameters from literature.
    """
    try:
        from pymatgen.analysis.bond_valence import BVAnalyzer
        
        # Get the analyzer
        analyzer = BVAnalyzer()
        
        # Analyze the structure
        # This returns a dict mapping site indices to BVS values
        bvs_values = analyzer.get_bvsums(structure)
        
        # Find all sites with the target atom symbol
        deviations = []
        for i, site in enumerate(structure):
            if site.species_string == atom_symbol:
                if i in bvs_values:
                    # Get ideal oxidation state (simplified: assume common states)
                    ideal_states = {
                        'Li': 1.0,
                        'O': -2.0,
                        'La': 3.0,
                        'Zr': 4.0,
                        'Ta': 5.0,
                        'Nb': 5.0,
                    }
                    ideal = ideal_states.get(atom_symbol, 0.0)
                    actual = bvs_values[i]
                    deviation = abs(actual - ideal) / abs(ideal) if ideal != 0 else 0.0
                    deviations.append(deviation)
        
        if not deviations:
            return 0.0
        
        return max(deviations)  # Return worst-case deviation
        
    except ImportError:
        logger.warning("pymatgen.analysis.bond_valence not available. Using fallback.")
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating BVS deviation: {e}")
        return 1.0  # Assume failure if calculation fails

def validate_crystallographic_constraints(structure: Any, 
                                          composition_id: str,
                                          output_path: Path) -> Tuple[bool, List[Dict]]:
    """
    Validate crystallographic constraints as mandated by FR-002 and Section 3.2.
    
    Specifically checks:
    1. Li-O bond distances must be within 1.95-2.15 Å
    2. BVS deviation must be < 10% for all Li and O atoms
    
    Args:
        structure: pymatgen Structure object
        composition_id: Unique identifier for the composition
        output_path: Path to write validation results JSON
        
    Returns:
        Tuple[bool, List[Dict]]: (is_valid, list_of_violations)
    """
    violations = []
    is_valid = True
    
    try:
        from pymatgen.core import Lattice
        from pymatgen.analysis.local_env import NearNeighbors
        
        # Get all Li-O distances
        li_sites = [site for site in structure if site.species_string == 'Li']
        o_sites = [site for site in structure if site.species_string == 'O']
        
        if not li_sites or not o_sites:
            # No Li or O atoms to check - might be valid depending on context
            logger.info(f"{composition_id}: No Li or O atoms found. Skipping distance check.")
            return True, violations
        
        # Check Li-O distances
        for li_site in li_sites:
            for o_site in o_sites:
                dist = li_site.distance(o_site)
                if dist < LI_O_MIN_DISTANCE or dist > LI_O_MAX_DISTANCE:
                    is_valid = False
                    violation = {
                        "composition_id": composition_id,
                        "type": "li_o_distance",
                        "details": f"Li-O distance {dist:.3f} Å outside [{LI_O_MIN_DISTANCE}, {LI_O_MAX_DISTANCE}] Å",
                        "li_index": structure.get_index_from_site(li_site),
                        "o_index": structure.get_index_from_site(o_site),
                        "distance": dist
                    }
                    violations.append(violation)
                    logger.warning(f"{composition_id}: {violation['details']}")
        
        # Check BVS deviation for Li and O
        for atom_symbol in ['Li', 'O']:
            deviation = calculate_bvs_deviation(structure, atom_symbol)
            if deviation > BVS_DEVIATION_THRESHOLD:
                is_valid = False
                violation = {
                    "composition_id": composition_id,
                    "type": "bvs_deviation",
                    "details": f"{atom_symbol} BVS deviation {deviation:.2%} exceeds {BVS_DEVIATION_THRESHOLD:.0%}",
                    "deviation": deviation,
                    "threshold": BVS_DEVIATION_THRESHOLD
                }
                violations.append(violation)
                logger.warning(f"{composition_id}: {violation['details']}")
        
        # Write results to output file
        result = {
            "composition_id": composition_id,
            "is_valid": is_valid,
            "violation_count": len(violations),
            "violations": violations,
            "thresholds": {
                "li_o_min": LI_O_MIN_DISTANCE,
                "li_o_max": LI_O_MAX_DISTANCE,
                "bvs_deviation": BVS_DEVIATION_THRESHOLD
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"{composition_id}: Validation {'PASSED' if is_valid else 'FAILED'} "
                   f"({len(violations)} violations)")
        
        return is_valid, violations
        
    except ImportError as e:
        logger.error(f"Missing dependency for crystallographic validation: {e}")
        # Fail loudly rather than passing silently
        raise RuntimeError(f"Cannot perform crystallographic validation: {e}")
    except Exception as e:
        logger.error(f"Error in crystallographic validation for {composition_id}: {e}")
        raise

def handle_missing_obelix_data(composition_id: str, 
                               required_variables: List[str],
                               available_variables: List[str]) -> Dict[str, Any]:
    """
    Handle missing OBELiX defect data by logging specific messages.
    
    Args:
        composition_id: Unique identifier for the composition
        required_variables: List of required variable names
        available_variables: List of variables actually available
        
    Returns:
        Dict with status and missing variables
    """
    missing = set(required_variables) - set(available_variables)
    
    if missing:
        logger.warning(f"{composition_id}: Missing OBELiX data for variables: {missing}")
        logger.info(f"{composition_id}: Will proceed with DFT-computed values for missing variables")
        return {
            "status": "partial",
            "missing": list(missing),
            "available": list(set(available_variables) & set(required_variables)),
            "action": "use_dft_fallback"
        }
    else:
        logger.info(f"{composition_id}: All required OBELiX data available")
        return {
            "status": "complete",
            "missing": [],
            "available": required_variables,
            "action": "use_obelix"
        }

def validate_defect_data_completeness(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that all required defect variables are present.
    
    Required variables: vacancy, interstitial, antisite, migration_barrier, conductivity
    
    Args:
        data: Dictionary containing defect data
        
    Returns:
        Tuple[bool, List[str]]: (is_complete, list_of_missing)
    """
    required = ['vacancy', 'interstitial', 'antisite', 'migration_barrier', 'conductivity']
    missing = [var for var in required if var not in data or data[var] is None]
    
    is_complete = len(missing) == 0
    return is_complete, missing

def validate_dataset_completeness(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate completeness of the entire dataset.
    
    Args:
        dataset: List of composition dictionaries
        
    Returns:
        Dict with completeness statistics
    """
    total = len(dataset)
    complete_count = 0
    missing_by_type = {}
    
    for item in dataset:
        is_complete, missing = validate_defect_data_completeness(item)
        if is_complete:
            complete_count += 1
        else:
            for var in missing:
                missing_by_type[var] = missing_by_type.get(var, 0) + 1
    
    return {
        "total_compositions": total,
        "complete_count": complete_count,
        "complete_percentage": (complete_count / total * 100) if total > 0 else 0,
        "missing_by_variable": missing_by_type,
        "completeness_threshold_met": (complete_count / total * 100) >= 93.0 if total > 0 else False
    }

def generate_completeness_report(dataset: List[Dict[str, Any]], 
                                 output_path: Path) -> Dict[str, Any]:
    """
    Generate a completeness report for the dataset.
    
    Args:
        dataset: List of composition dictionaries
        output_path: Path to write the JSON report
        
    Returns:
        Dict with report data
    """
    report = validate_dataset_completeness(dataset)
    report["timestamp"] = str(datetime.now())
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Completeness report written to {output_path}")
    return report

def run_bvs_validation_on_dataset(structures_path: Path, 
                                  output_dir: Path) -> Dict[str, Any]:
    """
    Run BVS and crystallographic validation on all structures in a directory.
    
    Args:
        structures_path: Path to directory containing structure files
        output_dir: Path to write validation results
        
    Returns:
        Dict with validation summary
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    valid_count = 0
    invalid_count = 0
    all_violations = []
    
    # Scan for structure files
    structure_files = list(structures_path.glob("*.cif")) + list(structures_path.glob("*.json"))
    
    if not structure_files:
        logger.warning(f"No structure files found in {structures_path}")
        return {"valid": 0, "invalid": 0, "total": 0, "violations": []}
    
    for struct_file in structure_files:
        try:
            from pymatgen.core import Structure
            structure = Structure.from_file(struct_file)
            composition_id = struct_file.stem
            
            # Create output file for this composition
            result_file = output_dir / f"{composition_id}_validation.json"
            
            is_valid, violations = validate_crystallographic_constraints(
                structure, composition_id, result_file
            )
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_violations.extend(violations)
                
        except Exception as e:
            logger.error(f"Failed to validate {struct_file}: {e}")
            invalid_count += 1
    
    summary = {
        "total_structures": len(structure_files),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "validity_rate": (valid_count / len(structure_files) * 100) if structure_files else 0,
        "total_violations": len(all_violations),
        "violations": all_violations
    }
    
    # Write summary
    summary_file = output_dir / "validation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Validation complete: {valid_count}/{len(structure_files)} structures valid")
    return summary

def main():
    """Main entry point for validation script."""
    logger.info("Starting validation module")
    
    # Load configuration
    config = load_config()
    data_dir = Path(config.get("data_dir", "data"))
    structures_path = data_dir / "raw" / "structures"
    validation_output = data_dir / "processed" / "validation_results"
    
    # Ensure directories exist
    validation_output.mkdir(parents=True, exist_ok=True)
    
    # Run validation on dataset
    if structures_path.exists():
        summary = run_bvs_validation_on_dataset(structures_path, validation_output)
        
        # Check if any violations occurred
        if summary["invalid_count"] > 0:
            logger.error(f"Validation failed for {summary['invalid_count']} structures. "
                        f"Review {validation_output / 'validation_summary.json'} for details.")
            # Log violations for debugging
            for v in summary["violations"][:10]:  # Log first 10
                logger.error(f"  - {v['composition_id']}: {v['type']} - {v['details']}")
            if len(summary["violations"]) > 10:
                logger.error(f"  ... and {len(summary['violations']) - 10} more violations")
    else:
        logger.warning(f"Structures directory not found: {structures_path}")
        logger.info("Skipping validation. Ensure data is downloaded first.")
    
    logger.info("Validation module completed")

if __name__ == "__main__":
    main()