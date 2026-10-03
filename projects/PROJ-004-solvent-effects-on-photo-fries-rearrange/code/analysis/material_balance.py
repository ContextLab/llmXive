"""
Quantitative Material Balance Report Implementation.

Reads trial configurations from sample_tracker (T053) and environmental logs
from environment.py (T014) to produce a comprehensive material balance report.

Output: data/processed/material_balance_report.csv
Columns: solvent, solvent_volume_ml, substrate_mass_g, integration_time_ms,
         volume_uncertainty_ml, mass_uncertainty_g, time_uncertainty_ms
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

# Import project utilities
from config import get_processed_data_path, get_raw_data_path
from utils.logging import setup_logging

# Configure logger immediately
logger = setup_logging(level=logging.INFO)


class MaterialBalanceError(Exception):
    """Raised when material balance calculations or data loading fail."""
    pass


def load_trial_configurations() -> List[Dict[str, Any]]:
    """
    Load trial configurations from the sample tracker output.

    Returns:
        List of dictionaries containing solvent, volume, mass, and time data.

    Raises:
        MaterialBalanceError: If the file is missing or malformed.
    """
    sample_tracker_path = get_processed_data_path() / "sample_quantity_report.csv"

    if not sample_tracker_path.exists():
        raise MaterialBalanceError(
            f"Sample tracker output not found at {sample_tracker_path}. "
            "Ensure T053 (sample_tracker.py) has been executed."
        )

    trials = []
    try:
        with open(sample_tracker_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse numeric values with defaults for missing/invalid data
                try:
                    volume = float(row.get('solvent_volume_ml', 0.0))
                    mass = float(row.get('substrate_mass_g', 0.0))
                    time_ms = float(row.get('integration_time_ms', 0.0))
                    # Parse uncertainties if present, default to small values if missing
                    vol_unc = float(row.get('volume_uncertainty_ml', 0.01))
                    mass_unc = float(row.get('mass_uncertainty_g', 0.001))
                    time_unc = float(row.get('time_uncertainty_ms', 1.0))
                except ValueError as e:
                    logger.warning(f"Invalid numeric value in row {row}: {e}. Using defaults.")
                    volume, mass, time_ms = 0.0, 0.0, 0.0
                    vol_unc, mass_unc, time_unc = 0.01, 0.001, 1.0

                trials.append({
                    'solvent': row.get('solvent', 'unknown'),
                    'solvent_volume_ml': volume,
                    'substrate_mass_g': mass,
                    'integration_time_ms': time_ms,
                    'volume_uncertainty_ml': vol_unc,
                    'mass_uncertainty_g': mass_unc,
                    'integration_time_uncertainty_ms': time_unc,
                    'run_id': row.get('run_id', ''),
                    'timestamp': row.get('timestamp', '')
                })
    except Exception as e:
        raise MaterialBalanceError(f"Failed to parse sample tracker CSV: {e}")

    if not trials:
        raise MaterialBalanceError("No trial data found in sample tracker output.")

    return trials


def load_environment_logs() -> Dict[str, Any]:
    """
    Load environmental logs to cross-reference conditions.

    Returns:
        Dictionary of environment logs keyed by run_id.

    Raises:
        MaterialBalanceError: If the file is missing.
    """
    env_logs_path = get_processed_data_path() / "environment_logs.json"

    if not env_logs_path.exists():
        # Fallback for CI/simulation if T014 hasn't run yet, but log warning
        logger.warning(f"Environment logs not found at {env_logs_path}. "
                       "Proceeding with trial data only; environmental metadata will be missing.")
        return {}

    try:
        with open(env_logs_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list of runs and dict of runs structures
            if isinstance(data, list):
                return {run.get('run_id', 'unknown'): run for run in data}
            elif isinstance(data, dict):
                return data
            else:
                logger.warning("Unexpected format in environment_logs.json")
                return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse environment logs JSON: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Error reading environment logs: {e}")
        return {}


def calculate_material_balance(trials: List[Dict[str, Any]], env_logs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate and enrich material balance data with environmental context.

    Args:
        trials: List of trial configurations from sample tracker.
        env_logs: Dictionary of environmental logs.

    Returns:
        Enriched list of material balance records.
    """
    balance_records = []

    for trial in trials:
        run_id = trial.get('run_id', '')
        env_data = env_logs.get(run_id, {})

        # Extract environmental metrics if available
        temp = env_data.get('temperature_c', None)
        rh = env_data.get('relative_humidity_pct', None)
        pressure = env_data.get('barometric_pressure_hPa', None)

        record = {
            'solvent': trial['solvent'],
            'solvent_volume_ml': trial['solvent_volume_ml'],
            'substrate_mass_g': trial['substrate_mass_g'],
            'integration_time_ms': trial['integration_time_ms'],
            'volume_uncertainty_ml': trial['volume_uncertainty_ml'],
            'mass_uncertainty_g': trial['mass_uncertainty_g'],
            'integration_time_uncertainty_ms': trial['integration_time_uncertainty_ms'],
            'temperature_c': temp if temp is not None else '',
            'relative_humidity_pct': rh if rh is not None else '',
            'barometric_pressure_hPa': pressure if pressure is not None else '',
            'run_id': run_id,
            'timestamp': trial.get('timestamp', ''),
            'total_mass_g': trial['substrate_mass_g'], # Simplified: assuming solvent mass is separate or negligible for this report
            'notes': 'Material balance calculated from T053 and T014 outputs'
        }
        balance_records.append(record)

    return balance_records


def write_material_balance_report(records: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write the material balance report to a CSV file.

    Args:
        records: List of material balance dictionaries.
        output_path: Optional path to write to. Defaults to data/processed/material_balance_report.csv.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "material_balance_report.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'run_id', 'solvent', 'solvent_volume_ml', 'substrate_mass_g', 'integration_time_ms',
        'volume_uncertainty_ml', 'mass_uncertainty_g', 'integration_time_uncertainty_ms',
        'temperature_c', 'relative_humidity_pct', 'barometric_pressure_hPa',
        'total_mass_g', 'timestamp', 'notes'
    ]

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        logger.info(f"Material balance report written to {output_path}")
        return output_path
    except Exception as e:
        raise MaterialBalanceError(f"Failed to write material balance report: {e}")


def run_material_balance_pipeline() -> Path:
    """
    Execute the full material balance pipeline.

    Returns:
        Path to the generated report.
    """
    logger.info("Starting material balance pipeline...")

    # Load data
    trials = load_trial_configurations()
    env_logs = load_environment_logs()

    # Calculate
    records = calculate_material_balance(trials, env_logs)

    # Write
    output_path = write_material_balance_report(records)

    logger.info(f"Material balance pipeline complete. Report: {output_path}")
    return output_path


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Quantitative Material Balance Report (T061)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for the CSV report (default: data/processed/material_balance_report.csv)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )

    args = parser.parse_args()
    setup_logging(level=getattr(logging, args.log_level.upper(), logging.INFO))

    try:
        output_path = run_material_balance_pipeline()
        print(f"Report generated: {output_path}")
        return 0
    except MaterialBalanceError as e:
        logger.error(f"Material Balance Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())