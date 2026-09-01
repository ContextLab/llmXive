"""
Validation module for solvent effects on Photo-Fries rearrangement kinetics.

This module provides functions to validate solvent series runs, environmental
conditions, and trend consistency across multiple solvent conditions.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

from config import get_processed_data_path, get_chemicals_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration files are missing or invalid."""
    pass


def load_solvent_reference() -> Dict[str, Any]:
    """
    Load solvent reference data from solvents.yaml.

    Returns:
        Dict containing solvent properties keyed by solvent name.

    Raises:
        ConfigurationError: If the file is missing or invalid.
    """
    chemicals_path = get_chemicals_path()
    solvent_file = chemicals_path / "solvents.yaml"

    if not solvent_file.exists():
        raise ConfigurationError(
            f"Solvent reference file not found: {solvent_file}. "
            "Run T006 to generate the solvent lookup table."
        )

    try:
        with open(solvent_file, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse solvents.yaml: {e}")

    if 'solvents' not in data:
        raise ConfigurationError("solvents.yaml must contain a 'solvents' key")

    return {s['name']: s for s in data['solvents']}


def check_dielectric_deviation(
    solvent_name: str,
    measured_dielectric: float,
    tolerance_percent: float = 2.0
) -> Tuple[bool, float]:
    """
    Check if measured dielectric constant deviates from reference by more than tolerance.

    Args:
        solvent_name: Name of the solvent.
        measured_dielectric: Measured dielectric constant.
        tolerance_percent: Maximum allowed deviation in percent.

    Returns:
        Tuple of (is_valid, deviation_percent).
    """
    reference = load_solvent_reference()

    if solvent_name not in reference:
        logger.warning(f"Solvent '{solvent_name}' not found in reference table.")
        return False, float('inf')

    reference_value = reference[solvent_name].get('dielectric_constant')
    if reference_value is None:
        logger.warning(f"No dielectric constant for '{solvent_name}' in reference.")
        return False, float('inf')

    deviation = abs(measured_dielectric - reference_value) / reference_value * 100
    is_valid = deviation <= tolerance_percent

    return is_valid, deviation


def validate_solvent_series_runs(
    environment_logs: List[Dict],
    tolerance_percent: float = 2.0
) -> Dict[str, Any]:
    """
    Validate all solvent series runs against reference dielectric constants.

    Args:
        environment_logs: List of environment log entries.
        tolerance_percent: Maximum allowed deviation.

    Returns:
        Validation report with pass/fail status and details.
    """
    results = {
        'total_runs': len(environment_logs),
        'passed_runs': 0,
        'failed_runs': 0,
        'details': [],
        'all_passed': True
    }

    for log in environment_logs:
        solvent_name = log.get('solvent_name', 'unknown')
        measured_dielectric = log.get('dielectric_constant')

        if measured_dielectric is None:
            logger.warning(f"Missing dielectric constant for {solvent_name}")
            results['failed_runs'] += 1
            results['details'].append({
                'solvent': solvent_name,
                'status': 'failed',
                'reason': 'Missing dielectric constant'
            })
            results['all_passed'] = False
            continue

        is_valid, deviation = check_dielectric_deviation(
            solvent_name, measured_dielectric, tolerance_percent
        )

        if is_valid:
            results['passed_runs'] += 1
            results['details'].append({
                'solvent': solvent_name,
                'status': 'passed',
                'deviation': deviation
            })
        else:
            results['failed_runs'] += 1
            results['details'].append({
                'solvent': solvent_name,
                'status': 'failed',
                'deviation': deviation,
                'reason': f'Deviation {deviation:.2f}% exceeds tolerance {tolerance_percent}%'
            })
            results['all_passed'] = False

    return results


def validate_environmental_conditions(
    environment_logs: List[Dict],
    temp_tolerance: float = 0.5,
    humidity_tolerance: float = 2.0
) -> Dict[str, Any]:
    """
    Validate temperature and humidity are within specified tolerances.

    Args:
        environment_logs: List of environment log entries.
        temp_tolerance: Temperature tolerance in °C.
        humidity_tolerance: Humidity tolerance in % RH.

    Returns:
        Validation report with pass/fail status and details.
    """
    results = {
        'total_runs': len(environment_logs),
        'passed_runs': 0,
        'failed_runs': 0,
        'details': [],
        'all_passed': True
    }

    for log in environment_logs:
        temperature = log.get('temperature_c')
        humidity = log.get('relative_humidity_percent')

        temp_ok = True
        humidity_ok = True
        reasons = []

        if temperature is not None:
            if abs(temperature - 25.0) > temp_tolerance:
                temp_ok = False
                reasons.append(
                    f"Temperature {temperature}°C outside 25±{temp_tolerance}°C"
                )

        if humidity is not None:
            if abs(humidity - 50.0) > humidity_tolerance:
                humidity_ok = False
                reasons.append(
                    f"Humidity {humidity}% outside 50±{humidity_tolerance}% RH"
                )

        if temp_ok and humidity_ok:
            results['passed_runs'] += 1
            results['details'].append({
                'run_id': log.get('run_id', 'unknown'),
                'status': 'passed'
            })
        else:
            results['failed_runs'] += 1
            results['details'].append({
                'run_id': log.get('run_id', 'unknown'),
                'status': 'failed',
                'reasons': reasons
            })
            results['all_passed'] = False

    return results


def calculate_environmental_compliance(
    environment_logs: List[Dict],
    temp_tolerance: float = 0.5,
    humidity_tolerance: float = 2.0
) -> float:
    """
    Calculate the percentage of runs within environmental tolerances.

    Args:
        environment_logs: List of environment log entries.
        temp_tolerance: Temperature tolerance in °C.
        humidity_tolerance: Humidity tolerance in % RH.

    Returns:
        Compliance percentage (0-100).
    """
    if not environment_logs:
        return 0.0

    validation = validate_environmental_conditions(
        environment_logs, temp_tolerance, humidity_tolerance
    )
    return (validation['passed_runs'] / validation['total_runs']) * 100


def write_compliance_report(
    report: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write compliance report to JSON file.

    Args:
        report: Compliance report dictionary.
        output_path: Optional output path. Defaults to data/processed/compliance_report.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "compliance_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Compliance report written to {output_path}")
    return output_path


def write_validation_report(
    report: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write validation report to JSON file.

    Args:
        report: Validation report dictionary.
        output_path: Optional output path. Defaults to data/processed/validation_report.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "validation_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return output_path


def verify_trend_consistency(
    min_solvents: int = 5,
    correlation_results_path: Optional[Path] = None,
    kinetic_metrics_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verify that consistent trends are observed across >= min_solvents solvent conditions.

    This implements SC-002: verify trend consistency across solvent series.

    Args:
        min_solvents: Minimum number of solvent conditions required.
        correlation_results_path: Path to correlation_results.json.
        kinetic_metrics_path: Path to kinetic_metrics.csv.

    Returns:
        Trend verification report with pass/fail status.
    """
    processed_path = get_processed_data_path()

    # Load correlation results
    if correlation_results_path is None:
        correlation_results_path = processed_path / "correlation_results.json"

    if not correlation_results_path.exists():
        raise ConfigurationError(
            f"Correlation results file not found: {correlation_results_path}. "
            "Run T030b to generate correlation results."
        )

    with open(correlation_results_path, 'r') as f:
        correlation_data = json.load(f)

    # Load kinetic metrics
    if kinetic_metrics_path is None:
        kinetic_metrics_path = processed_path / "kinetic_metrics.csv"

    if not kinetic_metrics_path.exists():
        raise ConfigurationError(
            f"Kinetic metrics file not found: {kinetic_metrics_path}. "
            "Run T026 to generate kinetic metrics."
        )

    import pandas as pd
    kinetic_df = pd.read_csv(kinetic_metrics_path)

    # Count unique solvents
    unique_solvents = kinetic_df['solvent_name'].nunique()

    # Check if we have enough solvents
    has_enough_solvents = unique_solvents >= min_solvents

    # Check if correlation is significant
    posterior_slope = correlation_data.get('posterior_slope', 0)
    bayesian_p_value = correlation_data.get('bayesian_p_value', 1.0)
    frequentist_p_value = correlation_data.get('frequentist_anova_p_value', 1.0)

    # Determine if trend is consistent (slope is non-zero and p-value is significant)
    # Using a threshold of 0.05 for p-value
    is_significant = frequentist_p_value < 0.05 or bayesian_p_value < 0.05

    # Check directionality (slope should be consistent)
    # For Photo-Fries, we expect lifetime to decrease with increasing polarity
    # So we check if the slope has a consistent sign
    trend_direction = "decreasing" if posterior_slope < 0 else "increasing" if posterior_slope > 0 else "neutral"

    # Build report
    report = {
        'min_solvents_required': min_solvents,
        'solvents_analyzed': unique_solvents,
        'has_enough_solvents': has_enough_solvents,
        'posterior_slope': posterior_slope,
        'bayesian_p_value': bayesian_p_value,
        'frequentist_anova_p_value': frequentist_p_value,
        'is_significant': is_significant,
        'trend_direction': trend_direction,
        'passes_trend_verification': has_enough_solvents and is_significant,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': {
            'solvent_list': kinetic_df['solvent_name'].unique().tolist(),
            'mean_lifetimes': kinetic_df.groupby('solvent_name')['lifetime_ns'].mean().to_dict(),
            'std_lifetimes': kinetic_df.groupby('solvent_name')['lifetime_ns'].std().to_dict()
        }
    }

    return report


def write_trend_verification_report(
    report: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write trend verification report to JSON file.

    Args:
        report: Trend verification report dictionary.
        output_path: Optional output path. Defaults to data/processed/trend_verification_report.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "trend_verification_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Trend verification report written to {output_path}")
    return output_path


def main():
    """Main entry point for trend verification."""
    from datetime import datetime, timezone

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting trend verification for SC-002")

    try:
        report = verify_trend_consistency()
        write_trend_verification_report(report)

        # Print summary
        status = "PASS" if report['passes_trend_verification'] else "FAIL"
        print(f"\n{'='*60}")
        print(f"Trend Verification Status: {status}")
        print(f"{'='*60}")
        print(f"Solvents analyzed: {report['solvents_analyzed']} (min required: {report['min_solvents_required']})")
        print(f"Has enough solvents: {report['has_enough_solvents']}")
        print(f"Trend direction: {report['trend_direction']}")
        print(f"Significant trend: {report['is_significant']}")
        print(f"Posterior slope: {report['posterior_slope']:.6f}")
        print(f"Bayesian p-value: {report['bayesian_p_value']:.6f}")
        print(f"Frequentist p-value: {report['frequentist_anova_p_value']:.6f}")
        print(f"{'='*60}\n")

        if not report['passes_trend_verification']:
            logger.warning("Trend verification FAILED")
            sys.exit(1)
        else:
            logger.info("Trend verification PASSED")
            sys.exit(0)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()