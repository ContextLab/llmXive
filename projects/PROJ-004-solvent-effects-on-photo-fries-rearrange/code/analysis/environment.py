"""
Environmental logging module for the Photo-Fries Rearrangement study.

This module captures and logs critical environmental parameters required for
reproducibility and compliance with FR-007 and SC-004.

Required fields per FR-007:
- temperature (°C)
- relative_humidity (%)
- barometric_pressure (hPa)
- substrate_mass (g)
- integration_time_ms (ms)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import config paths
from config import get_processed_data_path, ensure_directories

# Setup logger
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when required configuration or environmental data is missing."""
    pass

def validate_environmental_conditions(
    temperature: float,
    humidity: float,
    pressure: float,
    substrate_mass: float,
    integration_time_ms: float
) -> Tuple[bool, List[str]]:
    """
    Validate that environmental parameters are within expected physical ranges.

    Args:
        temperature: Temperature in Celsius.
        humidity: Relative humidity in %.
        pressure: Barometric pressure in hPa.
        substrate_mass: Mass of substrate in grams.
        integration_time_ms: Integration time in milliseconds.

    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []

    # Temperature: typical lab range 15-35°C
    if not (15.0 <= temperature <= 35.0):
        warnings.append(f"Temperature {temperature}°C outside typical lab range (15-35°C)")

    # Humidity: typical lab range 30-70%
    if not (30.0 <= humidity <= 70.0):
        warnings.append(f"Humidity {humidity}% outside typical lab range (30-70%)")

    # Pressure: typical sea level range 950-1050 hPa
    if not (950.0 <= pressure <= 1050.0):
        warnings.append(f"Pressure {pressure} hPa outside typical range (950-1050 hPa)")

    # Substrate mass: must be positive
    if substrate_mass <= 0:
        raise ConfigurationError(f"Substrate mass must be positive, got {substrate_mass}")

    # Integration time: must be positive
    if integration_time_ms <= 0:
        raise ConfigurationError(f"Integration time must be positive, got {integration_time_ms}")

    return len(warnings) == 0, warnings

def get_environment_value(key: str, env_var: Optional[str] = None, default: Optional[float] = None) -> float:
    """
    Retrieve an environmental value from config, environment variable, or raise error.

    Args:
        key: The name of the parameter (for logging).
        env_var: The environment variable name to check.
        default: A default value if not found (if None, raises error).

    Returns:
        The float value.

    Raises:
        ConfigurationError: If value is missing and no default provided.
    """
    value = None

    # Try environment variable first
    if env_var:
        env_val = os.getenv(env_var)
        if env_val:
            try:
                value = float(env_val)
            except ValueError:
                logger.warning(f"Could not parse {env_var}='{env_val}' as float")

    # Try config file (project_root/config/environment.yaml)
    if value is None:
        config_path = Path("config/environment.yaml")
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                if config and key in config:
                    value = float(config[key])
            except ImportError:
                logger.warning("PyYAML not installed, skipping config file read")
            except Exception as e:
                logger.warning(f"Could not read config file: {e}")

    # Try default
    if value is None and default is not None:
        value = default

    if value is None:
        raise ConfigurationError(
            f"Missing required environmental parameter: {key}. "
            f"Set via env var {env_var}, config file, or provide default."
        )

    return value

def record_run_environment(
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    barometric_pressure: Optional[float] = None,
    substrate_mass: Optional[float] = None,
    integration_time_ms: Optional[float] = None
) -> Dict[str, Any]:
    """
    Record the environmental conditions for a single run.

    Args:
        temperature: Temperature in °C. If None, attempts to read from env/config.
        humidity: Relative humidity in %. If None, attempts to read from env/config.
        barometric_pressure: Pressure in hPa. If None, attempts to read from env/config.
        substrate_mass: Mass in grams. If None, attempts to read from env/config.
        integration_time_ms: Time in ms. If None, attempts to read from env/config.

    Returns:
        Dictionary containing the recorded environment data.

    Raises:
        ConfigurationError: If any required field is missing and cannot be resolved.
    """
    # Resolve values
    # Barometric pressure is explicitly mandated by T014
    if barometric_pressure is None:
        barometric_pressure = get_environment_value(
            "barometric_pressure",
            env_var="BAROMETRIC_PRESSURE_HPA",
            default=None  # Must be provided if not in env/config
        )

    if temperature is None:
        temperature = get_environment_value(
            "temperature",
            env_var="LAB_TEMPERATURE_C",
            default=25.0  # Standard lab temp fallback
        )

    if humidity is None:
        humidity = get_environment_value(
            "humidity",
            env_var="LAB_HUMIDITY_RH",
            default=50.0  # Standard lab humidity fallback
        )

    if substrate_mass is None:
        substrate_mass = get_environment_value(
            "substrate_mass",
            env_var="SUBSTRATE_MASS_G",
            default=None  # Must be provided if not in env/config
        )

    if integration_time_ms is None:
        integration_time_ms = get_environment_value(
            "integration_time_ms",
            env_var="INTEGRATION_TIME_MS",
            default=1000.0  # Default 1s if not specified
        )

    # Validate
    is_valid, warnings = validate_environmental_conditions(
        temperature, humidity, barometric_pressure, substrate_mass, integration_time_ms
    )

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature_c": temperature,
        "relative_humidity_pct": humidity,
        "barometric_pressure_hPa": barometric_pressure,
        "substrate_mass_g": substrate_mass,
        "integration_time_ms": integration_time_ms,
        "warnings": warnings,
        "is_valid": is_valid
    }

    if warnings:
        for w in warnings:
            logger.warning(f"Environmental warning: {w}")

    if not is_valid:
        logger.error("Environmental conditions validation failed.")

    return record

def get_environment_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of multiple environment logs.

    Args:
        logs: List of environment log dictionaries.

    Returns:
        Summary dictionary with min, max, mean for numeric fields.
    """
    if not logs:
        return {}

    summary = {
        "total_runs": len(logs),
        "valid_runs": sum(1 for l in logs if l.get("is_valid", False)),
        "fields": {}
    }

    numeric_fields = ["temperature_c", "relative_humidity_pct", "barometric_pressure_hPa", "substrate_mass_g", "integration_time_ms"]

    for field in numeric_fields:
        values = [l[field] for l in logs if field in l]
        if values:
            summary["fields"][field] = {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "count": len(values)
            }

    return summary

def write_environment_logs(logs: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Write environment logs to a JSON file.

    Args:
        logs: List of environment log dictionaries.
        output_path: Path to output file. Defaults to data/processed/environment_logs.json.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = str(get_processed_data_path() / "environment_logs.json")

    # Ensure directory exists
    ensure_directories()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(logs, f, indent=2)

    logger.info(f"Environment logs written to {output_path}")
    return output_path

def main():
    """
    CLI entry point to record and log environmental conditions.

    Usage:
        python -m code.analysis.environment --temp 25.0 --hum 50.0 --press 1013.0 --mass 0.5 --time 1000
    """
    import argparse

    parser = argparse.ArgumentParser(description="Record environmental conditions for a run.")
    parser.add_argument("--temp", type=float, help="Temperature in Celsius")
    parser.add_argument("--hum", type=float, help="Relative humidity in %")
    parser.add_argument("--press", type=float, help="Barometric pressure in hPa")
    parser.add_argument("--mass", type=float, help="Substrate mass in grams")
    parser.add_argument("--time", type=float, help="Integration time in ms")
    parser.add_argument("--output", type=str, help="Output JSON path")
    parser.add_argument("--append", action="store_true", help="Append to existing log file")

    args = parser.parse_args()

    # Record environment
    try:
        log_entry = record_run_environment(
            temperature=args.temp,
            humidity=args.hum,
            barometric_pressure=args.press,
            substrate_mass=args.mass,
            integration_time_ms=args.time
        )
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)

    # Load existing logs if appending
    logs = [log_entry]
    if args.append:
        output_path = args.output or str(get_processed_data_path() / "environment_logs.json")
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    existing = json.load(f)
                    if isinstance(existing, list):
                        logs = existing + [log_entry]
                    else:
                        logs = [existing, log_entry]
            except json.JSONDecodeError:
                logger.warning("Existing log file is not valid JSON, overwriting.")

    # Write logs
    output_path = write_environment_logs(logs, args.output)
    print(f"Logged environment to {output_path}")

if __name__ == "__main__":
    import sys
    main()
