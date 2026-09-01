"""
Environment Logging Module for Photo-Fries Rearrangement Study.

This module handles the logging of environmental conditions and experimental
parameters required for reproducibility and compliance with FR-007 and SC-004.

It logs:
- Temperature (°C)
- Humidity (% RH)
- Barometric Pressure (hPa)
- Substrate Mass (g)
- Integration Time (ms)

Output: data/processed/environment_logs.json
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Ensure config is imported to resolve paths
# We import the public names from the existing API surface
try:
    from config import get_processed_data_path, ensure_directories
except ImportError:
    # Fallback for standalone execution if config isn't fully set up yet
    # This block ensures the script can at least be imported without error
    # during the implementation phase if dependencies aren't fully ready.
    def get_processed_data_path():
        return Path("data/processed")
    
    def ensure_directories():
        pass

# Setup logging using the project's utility if available
try:
    from utils.logging import setup_logging, log_environmental_params
    logger = setup_logging("environment")
except ImportError:
    # Fallback standard logging if utils.logging is not ready
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("environment")

# Constants for tolerances (defined here for local validation, 
# though validation logic primarily lives in validation.py)
TEMP_TOLERANCE = 0.5  # °C
HUMIDITY_TOLERANCE = 2.0  # % RH

ENV_LOG_PATH = Path("data/processed/environment_logs.json")


def validate_environmental_conditions(
    temperature: float,
    humidity: float,
    target_temperature: float = 25.0
) -> Tuple[bool, List[str]]:
    """
    Validate that logged environmental conditions are within acceptable tolerances.

    Args:
        temperature: Measured temperature in °C.
        humidity: Measured humidity in % RH.
        target_temperature: Target temperature (default 25.0°C).

    Returns:
        Tuple of (is_valid, list_of_warnings).
    """
    warnings = []
    is_valid = True

    if abs(temperature - target_temperature) > TEMP_TOLERANCE:
        warnings.append(
            f"Temperature {temperature}°C deviates from target {target_temperature}°C "
            f"by {abs(temperature - target_temperature):.2f}°C (tolerance: ±{TEMP_TOLERANCE}°C)."
        )
        is_valid = False

    if abs(humidity) > 100:
        warnings.append(f"Humidity {humidity}% RH is physically impossible.")
        is_valid = False
    
    # Note: Specific humidity tolerance checks are often handled in the 
    # hydration control module, but we flag extreme deviations here.
    if humidity > 95 or humidity < 10:
        warnings.append(f"Extreme humidity {humidity}% RH detected.")

    return is_valid, warnings


def record_run_environment(
    temperature: float,
    humidity: float,
    pressure: float,
    substrate_mass: float,
    integration_time_ms: float,
    solvent_name: Optional[str] = None,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a single run's environmental and experimental parameters.

    Args:
        temperature: Temperature in °C.
        humidity: Relative Humidity in %.
        pressure: Barometric pressure in hPa.
        substrate_mass: Mass of substrate in grams.
        integration_time_ms: Integration time in milliseconds.
        solvent_name: Name of the solvent used.
        run_id: Unique identifier for the run.

    Returns:
        Dictionary containing the recorded log entry.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    if run_id is None:
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    entry = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "environmental": {
            "temperature_celsius": temperature,
            "humidity_percent": humidity,
            "pressure_hpa": pressure
        },
        "experimental": {
            "substrate_mass_g": substrate_mass,
            "integration_time_ms": integration_time_ms,
            "solvent_name": solvent_name or "Unknown"
        },
        "status": "recorded"
    }

    # Validate and attach warnings
    is_valid, warnings = validate_environmental_conditions(
        temperature, humidity
    )
    entry["validation"] = {
        "is_within_tolerance": is_valid,
        "warnings": warnings
    }

    return entry


def get_environment_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for a list of environment logs.

    Args:
        logs: List of environment log entries.

    Returns:
        Dictionary with mean, min, max for key metrics.
    """
    if not logs:
        return {}

    temps = [l["environmental"]["temperature_celsius"] for l in logs]
    humids = [l["environmental"]["humidity_percent"] for l in logs]
    pressures = [l["environmental"]["pressure_hpa"] for l in logs]

    return {
        "total_runs": len(logs),
        "temperature": {
            "mean": sum(temps) / len(temps),
            "min": min(temps),
            "max": max(temps)
        },
        "humidity": {
            "mean": sum(humids) / len(humids),
            "min": min(humids),
            "max": max(humids)
        },
        "pressure": {
            "mean": sum(pressures) / len(pressures),
            "min": min(pressures),
            "max": max(pressures)
        }
    }


def write_environment_logs(
    logs: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the list of environment logs to a JSON file.

    Args:
        logs: List of log entries.
        output_path: Optional path to write to. Defaults to ENV_LOG_PATH.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = ENV_LOG_PATH

    # Ensure directory exists
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)

    logger.info(f"Environment logs written to {output_path}")
    return output_path


def main():
    """
    Main entry point for testing or standalone execution of environment logging.
    This function simulates a run series to demonstrate the logging capability
    and ensure the output file is generated as per T014 requirements.
    """
    logger.info("Starting Environment Logging Module (T014)")

    # Simulate a series of runs for different solvents
    # In a real pipeline, these values would come from sensors or a config file
    mock_runs = [
        {
            "solvent_name": "cyclohexane",
            "temperature": 24.9,
            "humidity": 45.2,
            "pressure": 1013.25,
            "substrate_mass": 0.050,
            "integration_time_ms": 100.0
        },
        {
            "solvent_name": "toluene",
            "temperature": 25.1,
            "humidity": 44.8,
            "pressure": 1013.10,
            "substrate_mass": 0.052,
            "integration_time_ms": 100.0
        },
        {
            "solvent_name": "acetonitrile",
            "temperature": 25.0,
            "humidity": 46.0,
            "pressure": 1012.90,
            "substrate_mass": 0.048,
            "integration_time_ms": 100.0
        },
        {
            "solvent_name": "methanol",
            "temperature": 24.8,
            "humidity": 45.5,
            "pressure": 1013.05,
            "substrate_mass": 0.051,
            "integration_time_ms": 100.0
        },
        {
            "solvent_name": "water",
            "temperature": 25.2,
            "humidity": 44.9,
            "pressure": 1013.20,
            "substrate_mass": 0.049,
            "integration_time_ms": 100.0
        }
    ]

    logs = []
    for i, run_data in enumerate(mock_runs):
        log_entry = record_run_environment(
            temperature=run_data["temperature"],
            humidity=run_data["humidity"],
            pressure=run_data["pressure"],
            substrate_mass=run_data["substrate_mass"],
            integration_time_ms=run_data["integration_time_ms"],
            solvent_name=run_data["solvent_name"],
            run_id=f"T014_RUN_{i+1:03d}"
        )
        logs.append(log_entry)
        logger.info(f"Recorded run {log_entry['run_id']} for {run_data['solvent_name']}")

    # Write to the required output path
    output_file = write_environment_logs(logs)
    
    # Print summary
    summary = get_environment_summary(logs)
    logger.info(f"Summary: {summary}")
    logger.info(f"Task T014 complete. Output written to: {output_file}")

    return output_file


if __name__ == "__main__":
    main()