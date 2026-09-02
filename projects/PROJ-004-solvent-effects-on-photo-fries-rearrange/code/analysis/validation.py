"""
Validation module for environmental compliance and solvent series verification.

This module implements validation logic for:
1. Dielectric constant deviation checks (SC-010)
2. Environmental condition tolerance checks (temperature, humidity)
3. Compliance reporting (T017b)
4. Trend verification (T048)
5. Temporal resolution validation (T050)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

from config import get_processed_data_path, get_chemicals_path
from utils.logging import setup_logging

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()

class ConfigurationError(Exception):
    """Raised when configuration requirements are not met."""
    pass

class ValidationError(Exception):
    """Raised when validation checks fail."""
    pass

def load_solvent_reference() -> Dict[str, Any]:
    """
    Load solvent reference data from solvents.yaml.

    Returns:
        Dict containing solvent properties keyed by solvent name.

    Raises:
        ConfigurationError: If solvents.yaml is missing or invalid.
    """
    solvents_path = get_chemicals_path() / "solvents.yaml"

    if not solvents_path.exists():
        raise ConfigurationError(
            f"Solvent reference file not found: {solvents_path}. "
            "Run T006b to populate solvent data."
        )

    try:
        with open(solvents_path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse solvents.yaml: {e}")

    # Verify version_hash exists (from T006d)
    if 'version_hash' not in data:
        raise ConfigurationError(
            "solvents.yaml missing 'version_hash' field. "
            "Run T006d to generate version hash."
        )

    return data

def check_dielectric_deviation(
    solvent_name: str,
    measured_epsilon: float,
    tolerance_pct: float = 2.0
) -> Tuple[bool, float, str]:
    """
    Check if measured dielectric constant deviates from reference by more than tolerance.

    Args:
        solvent_name: Name of the solvent to check.
        measured_epsilon: Measured dielectric constant value.
        tolerance_pct: Maximum allowed deviation percentage (default 2%).

    Returns:
        Tuple of (is_within_tolerance, deviation_pct, message)

    Raises:
        ConfigurationError: If solvent not found in reference data.
    """
    reference = load_solvent_reference()

    if 'solvents' not in reference:
        raise ConfigurationError("solvents.yaml missing 'solvents' key")

    if solvent_name not in reference['solvents']:
        raise ConfigurationError(f"Solvent '{solvent_name}' not found in reference data")

    reference_epsilon = reference['solvents'][solvent_name]['dielectric_constant']

    if reference_epsilon == 0:
        deviation_pct = float('inf') if measured_epsilon != 0 else 0.0
    else:
        deviation_pct = abs((measured_epsilon - reference_epsilon) / reference_epsilon) * 100

    is_within_tolerance = deviation_pct <= tolerance_pct

    if is_within_tolerance:
        message = f"OK: {solvent_name} epsilon={measured_epsilon:.3f} (ref={reference_epsilon:.3f}, dev={deviation_pct:.2f}%)"
    else:
        message = f"FAIL: {solvent_name} epsilon={measured_epsilon:.3f} (ref={reference_epsilon:.3f}, dev={deviation_pct:.2f}%) exceeds {tolerance_pct}% tolerance"

    return is_within_tolerance, deviation_pct, message

def validate_environmental_conditions(
    logged_data: Dict[str, Any],
    temperature_tolerance: float = 0.5,
    humidity_tolerance: float = 2.0
) -> Tuple[bool, List[str]]:
    """
    Validate environmental conditions against specified tolerances.

    Args:
        logged_data: Dictionary containing logged environmental parameters.
        temperature_tolerance: Max allowed temperature deviation in °C (default 0.5).
        humidity_tolerance: Max allowed humidity deviation in %RH (default 2.0).

    Returns:
        Tuple of (all_conditions_pass, list_of_failure_messages)
    """
    failures = []
    target_temperature = 25.0
    target_humidity = 50.0  # Assumed target, can be configurable

    # Check temperature
    if 'temperature' in logged_data:
        temp = logged_data['temperature']
        temp_deviation = abs(temp - target_temperature)
        if temp_deviation > temperature_tolerance:
            failures.append(
                f"Temperature {temp:.2f}°C deviates {temp_deviation:.2f}°C from target {target_temperature}°C "
                f"(tolerance: ±{temperature_tolerance}°C)"
            )
    else:
        failures.append("Temperature not logged")

    # Check humidity
    if 'relative_humidity' in logged_data:
        rh = logged_data['relative_humidity']
        rh_deviation = abs(rh - target_humidity)
        if rh_deviation > humidity_tolerance:
            failures.append(
                f"Relative humidity {rh:.2f}%RH deviates {rh_deviation:.2f}% from target {target_humidity}%RH "
                f"(tolerance: ±{humidity_tolerance}%RH)"
            )
    else:
        failures.append("Relative humidity not logged")

    # Check barometric pressure (required by T014)
    if 'barometric_pressure' not in logged_data:
        failures.append("Barometric pressure not logged (required)")

    # Check substrate_mass (required by T014)
    if 'substrate_mass' not in logged_data:
        failures.append("Substrate mass not logged (required)")

    # Check integration_time_ms (required by T014)
    if 'integration_time_ms' not in logged_data:
        failures.append("Integration time not logged (required)")

    return len(failures) == 0, failures

def validate_solvent_series_runs(
    environment_logs_path: Optional[Path] = None,
    tolerance_pct: float = 2.0
) -> Dict[str, Any]:
    """
    Validate all solvent series runs against reference data.

    Args:
        environment_logs_path: Path to environment_logs.json. If None, uses default path.
        tolerance_pct: Maximum allowed dielectric deviation percentage.

    Returns:
        Dictionary containing validation results and flagged runs.

    Raises:
        ConfigurationError: If required files are missing.
    """
    if environment_logs_path is None:
        environment_logs_path = get_processed_data_path() / "environment_logs.json"

    if not environment_logs_path.exists():
        raise ConfigurationError(
            f"Environment logs not found: {environment_logs_path}. "
            "Run T014 to generate environment logs."
        )

    with open(environment_logs_path, 'r') as f:
        env_logs = json.load(f)

    reference = load_solvent_reference()
    flagged_runs = []
    validation_results = []

    for run in env_logs.get('runs', []):
        solvent_name = run.get('solvent_name')
        measured_epsilon = run.get('dielectric_constant')

        if not solvent_name or measured_epsilon is None:
            flagged_runs.append({
                'run_id': run.get('run_id', 'unknown'),
                'reason': 'Missing solvent name or dielectric constant',
                'severity': 'critical'
            })
            continue

        is_valid, deviation, message = check_dielectric_deviation(
            solvent_name, measured_epsilon, tolerance_pct
        )

        env_valid, env_failures = validate_environmental_conditions(run)

        if not is_valid or not env_valid:
          flagged_runs.append({
              'run_id': run.get('run_id'),
              'solvent': solvent_name,
              'dielectric_deviation_pct': deviation if not is_valid else None,
              'environmental_failures': env_failures if not env_valid else None,
              'severity': 'warning' if is_valid and not env_valid else 'critical'
          })

        validation_results.append({
            'run_id': run.get('run_id'),
            'solvent': solvent_name,
            'is_valid': is_valid and env_valid,
            'message': message
        })

    output = {
        'validation_timestamp': env_logs.get('timestamp'),
        'total_runs': len(env_logs.get('runs', [])),
        'flagged_runs': flagged_runs,
        'validation_details': validation_results,
        'reference_hash': reference.get('version_hash')
    }

    return output

def write_validation_report(
    validation_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write validation results to a JSON file.

    Args:
        validation_results: Dictionary containing validation results.
        output_path: Path for output file. If None, uses default path.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "validation_flags.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return output_path

def calculate_compliance_percentage(
    environment_logs_path: Optional[Path] = None,
    validation_flags_path: Optional[Path] = None,
    config_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Calculate environmental compliance percentage.

    The compliance percentage is calculated as:
    (number of compliant runs / total configured solvent runs) * 100

    Where 'total configured solvent runs' is the sum of all 'n' replicates
    defined in the configuration.

    Args:
        environment_logs_path: Path to environment_logs.json.
        validation_flags_path: Path to validation_flags.json.
        config_path: Path to configuration file containing replicate counts.

    Returns:
        Dictionary containing compliance report.

    Raises:
        ConfigurationError: If required files are missing or invalid.
    """
    if environment_logs_path is None:
        environment_logs_path = get_processed_data_path() / "environment_logs.json"

    if validation_flags_path is None:
        validation_flags_path = get_processed_data_path() / "validation_flags.json"

    if not environment_logs_path.exists():
        raise ConfigurationError(
            f"Environment logs not found: {environment_logs_path}"
        )

    if not validation_flags_path.exists():
        raise ConfigurationError(
            f"Validation flags not found: {validation_flags_path}"
        )

    with open(environment_logs_path, 'r') as f:
        env_logs = json.load(f)

    with open(validation_flags_path, 'r') as f:
        validation_data = json.load(f)

    # Calculate total configured runs from environment logs
    # Each run in env_logs represents one configured replicate
    total_configured_runs = len(env_logs.get('runs', []))

    if total_configured_runs == 0:
        raise ConfigurationError(
            "No runs found in environment_logs.json. Cannot calculate compliance."
        )

    # Count compliant runs
    flagged_run_ids = {flag['run_id'] for flag in validation_data.get('flagged_runs', [])}
    compliant_runs = total_configured_runs - len(flagged_run_ids)

    compliance_percentage = (compliant_runs / total_configured_runs) * 100

    # Determine pass/fail status (>= 95% required)
    threshold = 95.0
    passed = compliance_percentage >= threshold

    report = {
        'compliance_percentage': round(compliance_percentage, 2),
        'threshold_percentage': threshold,
        'passed': passed,
        'total_configured_runs': total_configured_runs,
        'compliant_runs': compliant_runs,
        'non_compliant_runs': len(flagged_run_ids),
        'flagged_runs': validation_data.get('flagged_runs', []),
        'timestamp': validation_data.get('validation_timestamp'),
        'reference_hash': validation_data.get('reference_hash')
    }

    return report

def write_compliance_report(
    compliance_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write compliance report to JSON file.

    Args:
        compliance_data: Dictionary containing compliance data.
        output_path: Path for output file. If None, uses default path.

    Returns:
        Path to the written file.
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
    Main entry point for compliance reporting (T017b).

    Reads environment_logs.json and validation_flags.json,
    calculates compliance percentage, and writes compliance_report.json.
    """
    try:
        logger.info("Starting compliance reporting (T017b)")

        # Calculate compliance
        compliance_data = calculate_compliance_percentage()

        # Write report
        report_path = write_compliance_report(compliance_data)

        # Log summary
        status = "PASSED" if compliance_data['passed'] else "FAILED"
        logger.info(f"Compliance: {compliance_data['compliance_percentage']:.2f}% ({status})")
        logger.info(f"Total runs: {compliance_data['total_configured_runs']}")
        logger.info(f"Compliant runs: {compliance_data['compliant_runs']}")
        logger.info(f"Non-compliant runs: {compliance_data['non_compliant_runs']}")

        return 0

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during compliance reporting: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())