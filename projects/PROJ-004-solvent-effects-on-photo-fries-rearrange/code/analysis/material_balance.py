"""Quantitative Material Balance Report Generation.

Reads trial configurations from T053 (sample_tracker.py) and environmental
logs from T014 (environment.py) to produce a comprehensive material balance
report with measurement uncertainties.

Output: data/processed/material_balance_report.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from project utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logging import get_logger, log_operation, setup_logging
from config import get_processed_data_path, get_chemicals_path

# Constants
REPORT_PATH = "data/processed/material_balance_report.csv"
SAMPLE_TRACKER_PATH = "data/processed/sample_quantity_report.csv"
ENVIRONMENT_LOGS_PATH = "data/processed/environment_logs.json"
SOLVENTS_CONFIG_PATH = "data/chemicals/solvents.yaml"

# Measurement uncertainties (standard deviations based on typical instrument precision)
UNCERTAINTY_VOLUME_ML = 0.01  # ±0.01 mL for volumetric pipettes
UNCERTAINTY_MASS_G = 0.0001   # ±0.1 mg for analytical balance
UNCERTAINTY_TIME_MS = 1.0     # ±1 ms for digital timers

logger = get_logger("material_balance")


def load_trial_configurations() -> List[Dict[str, Any]]:
    """Load trial configurations from sample_tracker output.

    Returns:
        List of dictionaries with keys: solvent, solvent_volume_ml, substrate_mass_g,
        integration_time_ms, and associated uncertainties.
    """
    sample_tracker_path = os.path.join(get_processed_data_path(), "sample_quantity_report.csv")

    if not os.path.exists(sample_tracker_path):
        raise FileNotFoundError(
            f"Sample tracker output not found at {sample_tracker_path}. "
            "Ensure T053 (sample_tracker.py) has been executed."
        )

    trials = []
    with open(sample_tracker_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trial = {
                'solvent': row.get('solvent', ''),
                'solvent_volume_ml': float(row.get('solvent_volume_ml', 0.0)),
                'solvent_volume_uncertainty_ml': float(row.get('solvent_volume_uncertainty_ml', UNCERTAINTY_VOLUME_ML)),
                'substrate_mass_g': float(row.get('substrate_mass_g', 0.0)),
                'substrate_mass_uncertainty_g': float(row.get('substrate_mass_uncertainty_g', UNCERTAINTY_MASS_G)),
                'integration_time_ms': float(row.get('integration_time_ms', 0.0)),
                'integration_time_uncertainty_ms': float(row.get('integration_time_uncertainty_ms', UNCERTAINTY_TIME_MS)),
            }
            trials.append(trial)

    if not trials:
        raise ValueError("No trial configurations found in sample tracker output.")

    return trials


def load_environment_logs() -> Dict[str, Any]:
    """Load environmental logs from T014 output.

    Returns:
        Dictionary containing environmental parameters for each run.
    """
    env_logs_path = os.path.join(get_processed_data_path(), "environment_logs.json")

    if not os.path.exists(env_logs_path):
        raise FileNotFoundError(
            f"Environment logs not found at {env_logs_path}. "
            "Ensure T014 (environment.py) has been executed."
        )

    with open(env_logs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_material_balance(
    trials: List[Dict[str, Any]],
    env_logs: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Calculate material balance metrics for each trial.

    Args:
        trials: List of trial configurations from sample_tracker.
        env_logs: Environmental logs containing temperature, humidity, pressure.

    Returns:
        List of dictionaries with calculated material balance metrics.
    """
    report_rows = []

    # Extract environmental summary for the report
    env_summary = env_logs.get('summary', {})
    runs = env_logs.get('runs', [])

    # Create a lookup for run-specific environment data
    run_env_lookup = {}
    for run in runs:
        run_id = run.get('run_id', '')
        run_env_lookup[run_id] = run

    for i, trial in enumerate(trials):
        solvent = trial['solvent']
        volume = trial['solvent_volume_ml']
        volume_unc = trial['solvent_volume_uncertainty_ml']
        mass = trial['substrate_mass_g']
        mass_unc = trial['substrate_mass_uncertainty_g']
        time_ms = trial['integration_time_ms']
        time_unc = trial['integration_time_uncertainty_ms']

        # Calculate derived quantities
        # Concentration (g/mL) = mass / volume
        if volume > 0:
            concentration = mass / volume
            # Propagate uncertainty: dC/C = sqrt((dm/m)^2 + (dV/V)^2)
            rel_unc_mass = mass_unc / mass if mass > 0 else 0
            rel_unc_vol = volume_unc / volume if volume > 0 else 0
            rel_unc_conc = (rel_unc_mass**2 + rel_unc_vol**2)**0.5
            conc_unc = concentration * rel_unc_conc if concentration > 0 else 0
        else:
            concentration = 0.0
            conc_unc = 0.0

        # Link to environmental data if available
        run_env = {}
        if i < len(runs):
            run_env = runs[i].get('environment', {})

        report_row = {
            'solvent': solvent,
            'solvent_volume_ml': f"{volume:.4f}",
            'solvent_volume_uncertainty_ml': f"{volume_unc:.4f}",
            'substrate_mass_g': f"{mass:.6f}",
            'substrate_mass_uncertainty_g': f"{mass_unc:.6f}",
            'integration_time_ms': f"{time_ms:.2f}",
            'integration_time_uncertainty_ms': f"{time_unc:.2f}",
            'concentration_g_ml': f"{concentration:.6f}",
            'concentration_uncertainty_g_ml': f"{conc_unc:.6f}",
            'temperature_c': run_env.get('temperature_c', 'N/A'),
            'temperature_uncertainty_c': run_env.get('temperature_uncertainty_c', 'N/A'),
            'relative_humidity_pct': run_env.get('relative_humidity_pct', 'N/A'),
            'relative_humidity_uncertainty_pct': run_env.get('relative_humidity_uncertainty_pct', 'N/A'),
            'barometric_pressure_hPa': run_env.get('barometric_pressure_hPa', 'N/A'),
            'barometric_pressure_uncertainty_hPa': run_env.get('barometric_pressure_uncertainty_hPa', 'N/A'),
            'timestamp': run_env.get('timestamp', 'N/A'),
        }
        report_rows.append(report_row)

    return report_rows


def write_material_balance_report(report_rows: List[Dict[str, Any]]) -> str:
    """Write the material balance report to CSV.

    Args:
        report_rows: List of dictionaries containing report data.

    Returns:
        Path to the generated CSV file.
    """
    output_path = os.path.join(get_processed_data_path(), "material_balance_report.csv")

    if not report_rows:
        raise ValueError("No data to write to material balance report.")

    fieldnames = [
        'solvent', 'solvent_volume_ml', 'solvent_volume_uncertainty_ml',
        'substrate_mass_g', 'substrate_mass_uncertainty_g',
        'integration_time_ms', 'integration_time_uncertainty_ms',
        'concentration_g_ml', 'concentration_uncertainty_g_ml',
        'temperature_c', 'temperature_uncertainty_c',
        'relative_humidity_pct', 'relative_humidity_uncertainty_pct',
        'barometric_pressure_hPa', 'barometric_pressure_uncertainty_hPa',
        'timestamp'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    logger.info(f"Material balance report written to {output_path}")
    return output_path


def run_material_balance_pipeline() -> str:
    """Execute the full material balance pipeline.

    Returns:
        Path to the generated report file.
    """
    log_operation("material_balance_pipeline_start")

    # Load inputs
    trials = load_trial_configurations()
    env_logs = load_environment_logs()

    # Calculate metrics
    report_rows = calculate_material_balance(trials, env_logs)

    # Write output
    output_path = write_material_balance_report(report_rows)

    log_operation("material_balance_pipeline_complete", output_path=output_path)
    return output_path


def main() -> None:
    """CLI entry point for material balance report generation."""
    parser = argparse.ArgumentParser(
        description="Generate quantitative material balance report from trial and environmental data."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    try:
        output_path = run_material_balance_pipeline()
        print(f"Material balance report generated: {output_path}")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()