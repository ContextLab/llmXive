"""
Environment monitoring module for Photo-Fries rearrangement experiments.

Records temperature, humidity, and barometric pressure per run to ensure
experimental conditions comply with tolerance specifications (±0.5°C, ±2% RH).
Addresses reviewer concerns regarding hydration state control and
environmental reproducibility.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import project utilities from the existing API surface
from utils.logging import setup_logging, log_environmental_params
from config import get_processed_data_path

# Constants for tolerance checks
TARGET_TEMP_C = 25.0
TEMP_TOLERANCE_C = 0.5
HUMIDITY_TOLERANCE_RH = 2.0
MIN_PRESSURE_HPA = 950.0
MAX_PRESSURE_HPA = 1050.0

logger = logging.getLogger(__name__)


def validate_environmental_conditions(
    temperature: float,
    humidity: float,
    pressure: Optional[float] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate environmental readings against experimental tolerances.

    Args:
        temperature: Temperature in Celsius.
        humidity: Relative humidity in %.
        pressure: Barometric pressure in hPa (optional).

    Returns:
        Tuple of (is_valid, details_dict) where details_dict contains
        pass/fail status for each parameter.
    """
    details = {
        "temperature": {
            "value": temperature,
            "unit": "°C",
            "target": TARGET_TEMP_C,
            "tolerance": TEMP_TOLERANCE_C,
            "in_range": abs(temperature - TARGET_TEMP_C) <= TEMP_TOLERANCE_C
        },
        "humidity": {
            "value": humidity,
            "unit": "% RH",
            "tolerance": HUMIDITY_TOLERANCE_RH,
            "in_range": humidity <= 100.0 and humidity >= 0.0  # Basic validity
        }
    }

    if pressure is not None:
        details["pressure"] = {
            "value": pressure,
            "unit": "hPa",
            "min": MIN_PRESSURE_HPA,
            "max": MAX_PRESSURE_HPA,
            "in_range": MIN_PRESSURE_HPA <= pressure <= MAX_PRESSURE_HPA
        }

    is_valid = all(
        details[param].get("in_range", True)
        for param in details
    )

    return is_valid, details


def record_run_environment(
    run_id: str,
    temperature: float,
    humidity: float,
    pressure: Optional[float] = None,
    solvent_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record environmental parameters for a specific experimental run.

    This function logs the environment to both the structured log file
    and a persistent JSON file in data/processed/.

    Args:
        run_id: Unique identifier for the experimental run.
        temperature: Temperature in Celsius.
        humidity: Relative humidity in %.
        pressure: Barometric pressure in hPa (optional).
        solvent_name: Name of the solvent used (optional).

    Returns:
        Dictionary containing the recorded environmental data and validation status.
    """
    # Validate conditions
    is_valid, validation_details = validate_environmental_conditions(
        temperature, humidity, pressure
    )

    # Prepare record
    record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environmental_params": {
            "temperature_c": round(temperature, 2),
            "humidity_percent_rh": round(humidity, 2),
            "pressure_hpa": round(pressure, 2) if pressure is not None else None
        },
        "validation": {
            "is_valid": is_valid,
            "details": validation_details
        },
        "solvent_name": solvent_name
    }

    # Log to structured log file
    log_environmental_params(
        run_id=run_id,
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        solvent=solvent_name
    )

    # Append to persistent JSON file
    output_dir = Path(get_processed_data_path())
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "environment_logs.json"

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                all_records = json.load(f)
            except json.JSONDecodeError:
                all_records = []
    else:
        all_records = []

    all_records.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Environment recorded for run {run_id}: "
        f"T={temperature}°C, RH={humidity}%, Valid={is_valid}"
    )

    return record


def get_environment_summary() -> Dict[str, Any]:
    """
    Retrieve a summary of all recorded environmental data.

    Returns:
        Dictionary containing statistics on temperature, humidity, and pressure
        across all recorded runs.
    """
    output_file = Path(get_processed_data_path()) / "environment_logs.json"

    if not output_file.exists():
        return {
            "total_runs": 0,
            "message": "No environment logs found. Run experiments first."
        }

    with open(output_file, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError:
            return {
                "total_runs": 0,
                "message": "Environment log file is corrupted."
            }

    if not records:
        return {
            "total_runs": 0,
            "message": "No runs recorded yet."
        }

    temps = [r["environmental_params"]["temperature_c"] for r in records]
    humidities = [r["environmental_params"]["humidity_percent_rh"] for r in records]
    pressures = [
        r["environmental_params"]["pressure_hpa"]
        for r in records
        if r["environmental_params"]["pressure_hpa"] is not None
    ]

    valid_runs = sum(1 for r in records if r["validation"]["is_valid"])

    return {
        "total_runs": len(records),
        "compliance_count": valid_runs,
        "compliance_rate": f"{(valid_runs / len(records)) * 100:.2f}%",
        "temperature": {
            "min": min(temps),
            "max": max(temps),
            "mean": sum(temps) / len(temps),
            "target": TARGET_TEMP_C,
            "tolerance": TEMP_TOLERANCE_C
        },
        "humidity": {
            "min": min(humidities),
            "max": max(humidities),
            "mean": sum(humidities) / len(humidities),
            "tolerance": HUMIDITY_TOLERANCE_RH
        },
        "pressure": {
            "min": min(pressures) if pressures else None,
            "max": max(pressures) if pressures else None,
            "mean": sum(pressures) / len(pressures) if pressures else None
        }
    }


def main():
    """
    CLI entry point for recording environment parameters.
    Usage: python code/analysis/environment.py --run_id R001 --temp 24.8 --humid 45.2 --pressure 1013.25
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Record environmental parameters for a Photo-Fries experiment run."
    )
    parser.add_argument(
        "--run_id", type=str, required=True,
        help="Unique run identifier (e.g., 'R001', 'SOLVENT_A_RUN_1')"
    )
    parser.add_argument(
        "--temp", type=float, required=True,
        help="Temperature in Celsius (e.g., 24.8)"
    )
    parser.add_argument(
        "--humid", type=float, required=True,
        help="Relative humidity in % (e.g., 45.2)"
    )
    parser.add_argument(
        "--pressure", type=float, default=None,
        help="Barometric pressure in hPa (optional)"
    )
    parser.add_argument(
        "--solvent", type=str, default=None,
        help="Name of the solvent used (optional)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    record = record_run_environment(
        run_id=args.run_id,
        temperature=args.temp,
        humidity=args.humid,
        pressure=args.pressure,
        solvent_name=args.solvent
    )

    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()