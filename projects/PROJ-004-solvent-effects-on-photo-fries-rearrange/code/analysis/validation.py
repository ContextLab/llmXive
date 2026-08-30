"""
Validation module for solvent series and environmental compliance.
Addresses SC-010 (dielectric deviation), SC-004 (compliance percentage),
and edge case tolerance checks.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import yaml

from config import get_processed_data_path, get_chemicals_path

# Configure logging
logger = logging.getLogger(__name__)

def load_solvent_reference() -> Dict[str, float]:
    """
    Load the reference dielectric constants from the solvents.yaml file.
    Returns a dictionary mapping solvent name to dielectric constant.
    """
    chemicals_path = get_chemicals_path()
    solvents_file = chemicals_path / "solvents.yaml"

    if not solvents_file.exists():
        raise FileNotFoundError(f"Solvent reference file not found: {solvents_file}")

    with open(solvents_file, 'r') as f:
        data = yaml.safe_load(f)

    reference = {}
    if 'solvents' in data:
        for entry in data['solvents']:
            name = entry['name']
            dielectric = entry['dielectric_constant']
            reference[name] = dielectric

    return reference

def check_dielectric_deviation(
    solvent: str,
    logged_value: float,
    tolerance_percent: float = 2.0
) -> Tuple[bool, float]:
    """
    Check if the logged dielectric constant deviates more than tolerance_percent
    from the reference value.

    Returns:
        Tuple of (is_valid, deviation_percent)
    """
    reference = load_solvent_reference()

    if solvent not in reference:
        logger.warning(f"Solvent '{solvent}' not found in reference table.")
        return False, float('inf')

    ref_value = reference[solvent]
    if ref_value == 0:
        return False, float('inf')

    deviation = abs((logged_value - ref_value) / ref_value) * 100
    is_valid = deviation <= tolerance_percent

    return is_valid, deviation

def validate_solvent_series_runs(
    logs_path: Optional[Path] = None,
    tolerance_percent: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Validate a list of run logs against the solvent reference table.
    Returns a list of validation results including deviation flags.
    """
    if logs_path is None:
        logs_path = get_processed_data_path() / "environment_logs.json"

    if not logs_path.exists():
        raise FileNotFoundError(f"Environment logs not found: {logs_path}")

    with open(logs_path, 'r') as f:
        logs = json.load(f)

    results = []
    for run in logs:
        solvent = run['solvent']
        logged_dielectric = run['logged_dielectric']
        is_valid, deviation = check_dielectric_deviation(
            solvent, logged_dielectric, tolerance_percent
        )

        results.append({
            'run_id': run['run_id'],
            'solvent': solvent,
            'logged_dielectric': logged_dielectric,
            'reference_dielectric': load_solvent_reference().get(solvent),
            'deviation_percent': deviation,
            'is_valid': is_valid
        })

    return results

def write_validation_report(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the validation results to a JSON report file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "validation_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return output_path

def calculate_environmental_compliance(
    logs_path: Optional[Path] = None,
    dielectric_tolerance: float = 2.0,
    temp_tolerance: float = 1.0,
    humidity_tolerance: float = 2.0
) -> Dict[str, Any]:
    """
    Calculate the percentage of runs that are compliant with all environmental
    tolerances (dielectric, temperature, humidity).

    Args:
        logs_path: Path to environment_logs.json. If None, uses default path.
        dielectric_tolerance: Max allowed % deviation for dielectric constant.
        temp_tolerance: Max allowed deviation for temperature (degrees C).
        humidity_tolerance: Max allowed deviation for humidity (% RH).

    Returns:
        Dictionary containing compliance statistics.
    """
    if logs_path is None:
        logs_path = get_processed_data_path() / "environment_logs.json"

    if not logs_path.exists():
        raise FileNotFoundError(f"Environment logs not found: {logs_path}")

    with open(logs_path, 'r') as f:
        logs = json.load(f)

    if not logs:
        return {
            'total_runs': 0,
            'compliant_runs': 0,
            'environmental_compliance_percent': 0.0,
            'details': []
        }

    reference = load_solvent_reference()

    compliant_count = 0
    details = []

    for run in logs:
        run_id = run['run_id']
        solvent = run['solvent']
        
        # Check dielectric
        ref_dielectric = reference.get(solvent)
        dielectric_compliant = False
        if ref_dielectric is not None and ref_dielectric != 0:
            dev = abs((run['logged_dielectric'] - ref_dielectric) / ref_dielectric) * 100
            dielectric_compliant = dev <= dielectric_tolerance
        
        # Check temperature (assuming 25.0 C target, +/- tolerance)
        temp_compliant = abs(run['logged_temperature'] - 25.0) <= temp_tolerance

        # Check humidity (assuming 45.0% target, +/- tolerance)
        humidity_compliant = abs(run['logged_humidity'] - 45.0) <= humidity_tolerance

        is_compliant = dielectric_compliant and temp_compliant and humidity_compliant

        if is_compliant:
            compliant_count += 1

        details.append({
            'run_id': run_id,
            'solvent': solvent,
            'dielectric_compliant': dielectric_compliant,
            'temperature_compliant': temp_compliant,
            'humidity_compliant': humidity_compliant,
            'is_compliant': is_compliant
        })

    compliance_percent = (compliant_count / len(logs)) * 100

    return {
        'total_runs': len(logs),
        'compliant_runs': compliant_count,
        'environmental_compliance_percent': compliance_percent,
        'details': details
    }

def write_compliance_report(
    compliance_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the compliance report to a JSON file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "compliance_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(compliance_data, f, indent=2)

    logger.info(f"Compliance report written to {output_path}")
    return output_path

def main():
    """
    CLI entry point for calculating and writing the environmental compliance report.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Calculate compliance
        compliance_data = calculate_environmental_compliance()
        
        # Write report
        output_path = write_compliance_report(compliance_data)
        
        print(f"Compliance Report Generated: {output_path}")
        print(f"Total Runs: {compliance_data['total_runs']}")
        print(f"Compliant Runs: {compliance_data['compliant_runs']}")
        print(f"Environmental Compliance: {compliance_data['environmental_compliance_percent']:.2f}%")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during compliance calculation: {e}")
        raise

if __name__ == "__main__":
    main()
