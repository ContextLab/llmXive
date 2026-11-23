"""
Detection Threshold Validation Module

Validates that all measured intermediate lifetimes exceed the instrument's
detection limit by a statistically significant margin. Calculates the
signal-to-noise ratio (SNR) for each measurement and flags results that
fall below the detection threshold.

Addresses Marie Curie's concern for detection limits.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import from existing project modules
from config import get_processed_data_path, get_chemicals_path
from utils.logging import setup_logging, log_compliance_check

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MIN_SNR = 3.0  # Minimum acceptable signal-to-noise ratio
DEFAULT_DETECTION_LIMIT = 1.0e-9  # Default detection limit in seconds (1 ns)


def load_kinetic_metrics() -> pd.DataFrame:
    """
    Load kinetic metrics from the processed data directory.

    Returns:
        DataFrame containing lifetime measurements and associated metadata.

    Raises:
        FileNotFoundError: If the kinetic metrics file does not exist.
    """
    processed_path = get_processed_data_path()
    metrics_file = processed_path / "kinetic_metrics.csv"

    if not metrics_file.exists():
        raise FileNotFoundError(
            f"Kinetic metrics file not found at {metrics_file}. "
            "Please ensure T026 (kinetic_metrics) has been completed."
        )

    logger.info(f"Loading kinetic metrics from {metrics_file}")
    df = pd.read_csv(metrics_file)
    return df


def load_detection_limit_config() -> Dict[str, Any]:
    """
    Load instrument detection limit configuration.

    Reads from data/chemicals/instrument_config.yaml or uses defaults.

    Returns:
        Dictionary containing detection limit parameters.
    """
    chemicals_path = get_chemicals_path()
    config_file = chemicals_path / "instrument_config.yaml"

    default_config = {
        "detection_limit_seconds": DEFAULT_DETECTION_LIMIT,
        "minimum_snr": DEFAULT_MIN_SNR,
        "temporal_resolution_ns": 1.0,  # 1 ns resolution
    }

    if not config_file.exists():
        logger.warning(
            f"Instrument config not found at {config_file}. "
            f"Using default detection limit: {DEFAULT_DETECTION_LIMIT} s"
        )
        return default_config

    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Extract detection limit parameters with defaults
        detection_config = config.get('detection_limits', {})
        default_config.update({
            "detection_limit_seconds": detection_config.get(
                "seconds", DEFAULT_DETECTION_LIMIT
            ),
            "minimum_snr": detection_config.get("min_snr", DEFAULT_MIN_SNR),
            "temporal_resolution_ns": detection_config.get(
                "temporal_resolution_ns", 1.0
            ),
        })
        return default_config

    except Exception as e:
        logger.warning(
            f"Error parsing instrument config: {e}. Using defaults."
        )
        return default_config


def calculate_signal_to_noise_ratio(
    lifetime: float,
    uncertainty: float,
    detection_limit: float
) -> Tuple[float, bool]:
    """
    Calculate the signal-to-noise ratio for a lifetime measurement.

    The SNR is calculated as: (lifetime - detection_limit) / uncertainty

    Args:
        lifetime: Measured lifetime in seconds.
        uncertainty: Standard uncertainty of the measurement in seconds.
        detection_limit: Instrument detection limit in seconds.

    Returns:
        Tuple of (snr_value, is_valid) where is_valid is True if
        lifetime > detection_limit and snr >= minimum_snr.
    """
    if uncertainty <= 0:
        logger.warning("Non-positive uncertainty provided, using small default")
        uncertainty = 1.0e-12  # 1 ps default

    # Calculate SNR based on distance from detection limit
    signal = lifetime - detection_limit

    if signal <= 0:
        # Lifetime is at or below detection limit
        return 0.0, False

    snr = signal / uncertainty

    return snr, True


def validate_detection_thresholds(
    metrics_df: pd.DataFrame,
    detection_config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Validate all lifetime measurements against detection thresholds.

    Args:
        metrics_df: DataFrame with kinetic metrics.
        detection_config: Configuration dictionary with detection limits.

    Returns:
        DataFrame with additional columns for SNR, validity flags, and status.
    """
    detection_limit = detection_config["detection_limit_seconds"]
    min_snr = detection_config["minimum_snr"]

    results = []

    for idx, row in metrics_df.iterrows():
        lifetime = row.get('lifetime_s')
        uncertainty = row.get('uncertainty_s', row.get('std_dev_s', 0.0))

        if pd.isna(lifetime) or lifetime == 0:
            logger.warning(f"Skipping row {idx}: invalid lifetime value")
            results.append({
                'solvent': row.get('solvent', 'Unknown'),
                'lifetime_s': lifetime,
                'uncertainty_s': uncertainty,
                'snr': np.nan,
                'above_detection_limit': False,
                'meets_snr_threshold': False,
                'status': 'INVALID_LIFETIME',
                'flag': 'FAIL'
            })
            continue

        snr, is_above_limit = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        meets_snr = is_above_limit and (snr >= min_snr)

        if is_above_limit and meets_snr:
            status = 'VALID'
            flag = 'PASS'
        elif is_above_limit and not meets_snr:
            status = 'WARNINGSNR_LOW'
            flag = 'WARN'
        else:
            status = 'BELOW_DETECTION_LIMIT'
            flag = 'FAIL'

        results.append({
            'solvent': row.get('solvent', 'Unknown'),
            'lifetime_s': lifetime,
            'uncertainty_s': uncertainty,
            'snr': snr,
            'above_detection_limit': is_above_limit,
            'meets_snr_threshold': meets_snr,
            'status': status,
            'flag': flag,
            'detection_limit_s': detection_limit,
            'min_snr_threshold': min_snr
        })

    validation_df = pd.DataFrame(results)
    return validation_df


def generate_summary_statistics(validation_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for the detection threshold validation.

    Args:
        validation_df: DataFrame with validation results.

    Returns:
        Dictionary containing summary statistics.
    """
    total_runs = len(validation_df)
    passed = (validation_df['flag'] == 'PASS').sum()
    warned = (validation_df['flag'] == 'WARN').sum()
    failed = (validation_df['flag'] == 'FAIL').sum()

    avg_snr = validation_df['snr'].mean()
    min_snr = validation_df['snr'].min()
    max_snr = validation_df['snr'].max()

    return {
        'total_runs': int(total_runs),
        'passed_count': int(passed),
        'warned_count': int(warned),
        'failed_count': int(failed),
        'pass_rate': float(passed / total_runs) if total_runs > 0 else 0.0,
        'average_snr': float(avg_snr) if not np.isnan(avg_snr) else None,
        'min_snr_observed': float(min_snr) if not np.isnan(min_snr) else None,
        'max_snr_observed': float(max_snr) if not np.isnan(max_snr) else None,
        'detection_limit_seconds': float(validation_df['detection_limit_s'].iloc[0]) if total_runs > 0 else None,
        'min_snr_threshold': float(validation_df['min_snr_threshold'].iloc[0]) if total_runs > 0 else None
    }


def write_validation_report(
    validation_df: pd.DataFrame,
    summary_stats: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the detection threshold validation report to disk.

    Args:
        validation_df: DataFrame with detailed validation results.
        summary_stats: Dictionary with summary statistics.
        output_path: Path to the output JSON file.
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'validation_type': 'detection_threshold',
        'summary': summary_stats,
        'detailed_results': validation_df.to_dict(orient='records')
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Validation report written to {output_path}")


def run_detection_threshold_validation() -> Dict[str, Any]:
    """
    Main pipeline function to run detection threshold validation.

    Returns:
        Dictionary containing summary statistics and validation results.
    """
    logger.info("Starting detection threshold validation...")

    # Load data
    metrics_df = load_kinetic_metrics()
    detection_config = load_detection_limit_config()

    logger.info(
        f"Using detection limit: {detection_config['detection_limit_seconds']} s, "
        f"min SNR: {detection_config['minimum_snr']}"
    )

    # Validate thresholds
    validation_df = validate_detection_thresholds(metrics_df, detection_config)

    # Generate summary
    summary_stats = generate_summary_statistics(validation_df)

    # Determine overall pass/fail
    if summary_stats['failed_count'] > 0:
        overall_status = 'FAIL'
        logger.warning(
            f"Validation FAILED: {summary_stats['failed_count']} runs "
            "below detection threshold or insufficient SNR."
        )
    elif summary_stats['warned_count'] > 0:
        overall_status = 'WARN'
        logger.warning(
            f"Validation WARN: {summary_stats['warned_count']} runs "
            "have low SNR but are above detection limit."
        )
    else:
        overall_status = 'PASS'
        logger.info("Validation PASSED: All runs exceed detection threshold with sufficient SNR.")

    # Write outputs
    processed_path = get_processed_data_path()
    output_file = processed_path / "detection_threshold_report.json"
    write_validation_report(validation_df, summary_stats, output_file)

    # Log compliance
    log_compliance_check(
        task="detection_threshold_validation",
        status=overall_status,
        details=summary_stats
    )

    return {
        'status': overall_status,
        'summary': summary_stats,
        'report_path': str(output_file)
    }


def main() -> int:
    """
    CLI entry point for detection threshold validation.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Validate lifetime measurements against instrument detection limits."
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    args = parser.parse_args()

    setup_logging(level=args.log_level)

    try:
        result = run_detection_threshold_validation()

        if result['status'] == 'PASS':
            print(f"✓ Detection threshold validation PASSED")
            print(f"  Total runs: {result['summary']['total_runs']}")
            print(f"  Pass rate: {result['summary']['pass_rate']:.1%}")
            print(f"  Report: {result['report_path']}")
            return 0

        elif result['status'] == 'WARN':
            print(f"⚠ Detection threshold validation WARNED")
            print(f"  Total runs: {result['summary']['total_runs']}")
            print(f"  Pass rate: {result['summary']['pass_rate']:.1%}")
            print(f"  Low SNR count: {result['summary']['warned_count']}")
            print(f"  Report: {result['report_path']}")
            return 0

        else:
            print(f"✗ Detection threshold validation FAILED")
            print(f"  Total runs: {result['summary']['total_runs']}")
            print(f"  Failed count: {result['summary']['failed_count']}")
            print(f"  Report: {result['report_path']}")
            return 1

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        logger.exception("Unexpected error during validation")
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
