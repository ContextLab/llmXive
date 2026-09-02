"""
Thermo Consistency Check Service.

Verifies that loaded surrogate DFT energies align with TCFE9 CALPHAD parameters.
Compares segregation energies against thermodynamic predictions for binary systems.
Flags deviations > 0.1 eV for review.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from code.config import DATA_RAW_PATH, get_logger, PROCESSED_PATH
from code.errors import DataLoadError, ThermodynamicError

# Configure logger
logger = get_logger(__name__)

DEVIATION_THRESHOLD_E_V = 0.1

def load_dft_energies(filepath: Path) -> Dict[str, Any]:
    """Load DFT energies from JSON file."""
    if not filepath.exists():
        raise DataLoadError(f"DFT energies file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Failed to parse DFT energies JSON: {e}")

def load_calphad_params(filepath: Path) -> Dict[str, Any]:
    """Load CALPHAD parameters from JSON file."""
    if not filepath.exists():
        raise DataLoadError(f"CALPHAD parameters file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Failed to parse CALPHAD parameters JSON: {e}")

def estimate_thermodynamic_segregation(
    calphad_data: Dict[str, Any], 
    system: str
) -> Optional[float]:
    """
    Estimate segregation energy from CALPHAD parameters.
    
    For binary systems, we approximate the segregation energy based on
    the difference in Gibbs free energy of the solute in the bulk vs.
    the grain boundary phase (if available) or use a simplified model
    based on mixing enthalpy.
    
    Returns:
        Estimated segregation energy in eV, or None if data unavailable.
    """
    # Extract binary interaction parameters for the system
    # Expected format: calphad_data['parameters'][system]
    if 'parameters' not in calphad_data:
        logger.warning(f"No 'parameters' key in CALPHAD data for system {system}")
        return None
    
    params = calphad_data['parameters']
    if system not in params:
        logger.warning(f"No CALPHAD parameters found for system {system}")
        return None
    
    sys_params = params[system]
    
    # Simplified estimation: use interaction parameter L0 as proxy for segregation tendency
    # This is a heuristic; real calculation would require phase equilibrium computation
    if 'L0' in sys_params:
        l0 = sys_params['L0']
        # Convert from J/mol to eV/atom (1 eV ≈ 96485 J/mol)
        estimated_energy_eV = l0 / 96485.0
        return estimated_energy_eV
    
    logger.warning(f"No L0 parameter found for system {system}, cannot estimate")
    return None

def check_consistency(
    dft_data: Dict[str, Any],
    calphad_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Compare DFT segregation energies against CALPHAD-based estimates.
    
    Returns:
        List of comparison results with pass/fail status and deviation metrics.
    """
    results = []
    
    # Assume DFT data structure: {'systems': [{'name': 'Fe-Cr', 'energy_eV': 0.5}, ...]}
    systems = dft_data.get('systems', [])
    if not systems:
        logger.warning("No systems found in DFT data")
        return results
    
    for entry in systems:
        system_name = entry.get('name') or entry.get('system')
        if not system_name:
            logger.warning("Skipping DFT entry without system name")
            continue
        
        dft_energy = entry.get('energy_eV')
        if dft_energy is None:
            logger.warning(f"Skipping {system_name}: no energy_eV found")
            continue
        
        # Estimate thermodynamic energy from CALPHAD
        thermo_energy = estimate_thermodynamic_segregation(calphad_data, system_name)
        
        if thermo_energy is None:
            # Skip if no CALPHAD data available
            results.append({
                'system': system_name,
                'status': 'skipped',
                'reason': 'No CALPHAD data available',
                'dft_energy_eV': dft_energy,
                'thermo_energy_eV': None,
                'deviation_eV': None
            })
            logger.info(f"Thermo consistency check skipped for {system_name}: no CALPHAD data")
            continue
        
        deviation = abs(dft_energy - thermo_energy)
        status = 'pass' if deviation <= DEVIATION_THRESHOLD_E_V else 'fail'
        
        results.append({
            'system': system_name,
            'status': status,
            'dft_energy_eV': dft_energy,
            'thermo_energy_eV': thermo_energy,
            'deviation_eV': deviation,
            'threshold_eV': DEVIATION_THRESHOLD_E_V
        })
        
        if status == 'fail':
            logger.warning(
                f"Thermo consistency check FAILED for {system_name}: "
                f"DFT={dft_energy:.3f} eV, CALPHAD={thermo_energy:.3f} eV, "
                f"deviation={deviation:.3f} eV (threshold={DEVIATION_THRESHOLD_E_V} eV)"
            )
        else:
            logger.info(
                f"Thermo consistency check PASSED for {system_name}: "
                f"deviation={deviation:.3f} eV"
            )
    
    return results

def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary report from consistency check results."""
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    return {
        'summary': {
            'total_systems': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': passed / total if total > 0 else 0.0
        },
        'details': results,
        'threshold_eV': DEVIATION_THRESHOLD_E_V
    }

def main():
    """Main entry point for thermo consistency check."""
    dft_path = DATA_RAW_PATH / 'dft_energies.json'
    calphad_path = DATA_RAW_PATH / 'calphad_params.json'
    output_path = PROCESSED_PATH / 'thermo_consistency_report.json'
    
    logger.info("Starting thermodynamic consistency check...")
    
    # Check if CALPHAD data is available
    if not calphad_path.exists():
        logger.warning("CALPHAD data not found. Skipping thermo consistency check.")
        # Write a report indicating the check was skipped
        report = {
            'summary': {
                'total_systems': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'pass_rate': 0.0,
                'note': 'No CALPHAD data available'
            },
            'details': [],
            'threshold_eV': DEVIATION_THRESHOLD_E_V
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report written to {output_path}")
        return
    
    try:
        dft_data = load_dft_energies(dft_path)
        calphad_data = load_calphad_params(calphad_path)
    except DataLoadError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    
    results = check_consistency(dft_data, calphad_data)
    report = generate_report(results)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Thermo consistency report written to {output_path}")
    
    # Exit with non-zero code if any checks failed
    if report['summary']['failed'] > 0:
        logger.warning(f"{report['summary']['failed']} systems failed consistency check.")
        # Note: We do not exit with error code here to allow pipeline continuation,
        # but the report flags the issues for review.
    
    logger.info("Thermodynamic consistency check completed.")

if __name__ == '__main__':
    main()