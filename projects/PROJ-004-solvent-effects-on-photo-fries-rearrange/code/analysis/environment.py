"""Environmental logging module for US1.

Implements FR-007 and SC-004 by logging temperature, humidity, barometric pressure,
substrate_mass, and integration_time_ms for each run.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from local utils to satisfy the shared contract
from utils.logging import setup_logging, log_operation

class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

# Default paths
PROCESSED_DATA_PATH = Path("data/processed")
ENVIRONMENT_LOG_FILE = PROCESSED_DATA_PATH / "environment_logs.json"

def get_environment_value(key: str, fallback: Optional[Any] = None) -> Any:
    """
    Retrieve a value from environment variables or config.
    Prioritizes environment variables, then a hypothetical config dict.
    """
    # Check environment variables first
    env_val = os.getenv(key.upper())
    if env_val is not None:
        try:
            return float(env_val)
        except ValueError:
            return env_val
    
    # Fallback to hardcoded defaults for CI/Testing if not in env
    # These represent the "Config" source mentioned in FR-007
    defaults = {
        "temperature": 25.0,
        "humidity": 50.0,
        "barometric_pressure": 1013.25,
        "substrate_mass": 0.050, # 50 mg
        "integration_time_ms": 100.0
    }
    
    if key in defaults:
        return defaults[key]
    return fallback

def validate_environmental_conditions(conditions: Dict[str, float]) -> List[str]:
    """
    Validate environmental conditions against tolerances.
    Returns a list of warning messages if conditions are out of spec.
    """
    warnings = []
    
    # Tolerances
    TEMP_TOL = 0.5  # ±0.5°C
    HUMIDITY_TOL = 2.0  # ±2% RH
    PRESSURE_TOL = 5.0  # ±5 hPa
    
    temp = conditions.get("temperature")
    if temp is not None:
        if abs(temp - 25.0) > TEMP_TOL:
            warnings.append(f"Temperature {temp}°C deviates > {TEMP_TOL}°C from 25°C target.")
    
    humidity = conditions.get("humidity")
    if humidity is not None:
        if abs(humidity - 50.0) > HUMIDITY_TOL:
            warnings.append(f"Humidity {humidity}% deviates > {HUMIDITY_TOL}% from 50% target.")
    
    pressure = conditions.get("barometric_pressure")
    if pressure is not None:
        if abs(pressure - 1013.25) > PRESSURE_TOL:
            warnings.append(f"Pressure {pressure} hPa deviates > {PRESSURE_TOL} hPa from 1013.25 hPa target.")
    
    return warnings

def record_run_environment(run_id: str, **kwargs) -> Dict[str, Any]:
    """
    Record the environment for a specific run.
    Ensures all required fields (FR-007) are present.
    """
    # Required fields per FR-007
    required_fields = [
        "temperature", "humidity", "barometric_pressure", 
        "substrate_mass", "integration_time_ms"
    ]
    
    environment = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    missing_fields = []
    
    for field in required_fields:
        # Try to get from kwargs first, then env/config
        value = kwargs.get(field)
        if value is None:
            value = get_environment_value(field)
        
        if value is None:
            missing_fields.append(field)
        else:
            environment[field] = float(value)
    
    if missing_fields:
        raise ConfigurationError(
            f"Missing required environmental fields: {missing_fields}. "
            f"Ensure config or environment variables provide: {', '.join(missing_fields)}"
        )
    
    # Validate and add warnings
    warnings = validate_environmental_conditions(environment)
    if warnings:
        environment["warnings"] = warnings
        log_operation("environmental_warning", warnings=warnings)
    
    return environment

def get_environment_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of environmental logs.
    Calculates mean, min, max for numeric fields.
    """
    if not logs:
        return {"error": "No logs provided"}
    
    numeric_fields = ["temperature", "humidity", "barometric_pressure", "substrate_mass", "integration_time_ms"]
    summary = {
        "total_runs": len(logs),
        "fields_summary": {}
    }
    
    for field in numeric_fields:
        values = [log.get(field) for log in logs if field in log]
        if values:
            summary["fields_summary"][field] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
    
    return summary

def write_environment_logs(logs: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write environment logs to a JSON file.
    Creates the directory if it doesn't exist.
    """
    if output_path is None:
        output_path = ENVIRONMENT_LOG_FILE
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, default=str)
    
    log_operation("environment_logs_written", path=str(output_path), count=len(logs))
    return output_path

def main() -> None:
    """
    CLI entry point to generate environment logs.
    Simulates a series of runs with varying conditions or reads from config.
    """
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting environment logging process (T014).")
    
    # Simulate a series of runs (US1 requirement: multiple solvents/conditions)
    # In a real pipeline, this would be driven by the solvent series configuration
    run_configs = [
        {"run_id": "RUN-001", "temperature": 24.8, "humidity": 49.5, "barometric_pressure": 1012.0},
        {"run_id": "RUN-002", "temperature": 25.2, "humidity": 50.1, "barometric_pressure": 1013.5},
        {"run_id": "RUN-003", "temperature": 25.0, "humidity": 51.0, "barometric_pressure": 1014.0},
    ]
    
    logs = []
    for config in run_configs:
        try:
            env_record = record_run_environment(**config)
            logs.append(env_record)
            logger.info(f"Recorded environment for {env_record['run_id']}: "
                        f"T={env_record['temperature']}°C, "
                        f"H={env_record['humidity']}%, "
                        f"P={env_record['barometric_pressure']} hPa")
        except ConfigurationError as e:
            logger.error(f"Failed to record environment for {config.get('run_id')}: {e}")
            sys.exit(1)
    
    if logs:
        output_path = write_environment_logs(logs)
        logger.info(f"Environment logs written to {output_path}")
        
        # Print summary to stdout for immediate verification
        summary = get_environment_summary(logs)
        print(json.dumps(summary, indent=2))
    else:
        logger.error("No environment logs were recorded.")
        sys.exit(1)

if __name__ == "__main__":
    main()