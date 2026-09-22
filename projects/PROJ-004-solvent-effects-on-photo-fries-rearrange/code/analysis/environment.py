"""
Environmental Logging Module.
Implements T014: Implement code/analysis/environment.py to log temperature, humidity,
barometric pressure, substrate_mass, and integration_time_ms.

Constraint: Must output to data/processed/environment_logs.json.
Constraint: Must raise ConfigurationError if barometric_pressure is missing.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from config import get_processed_data_path
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

def get_environment_value(key: str, default: Optional[Any] = None) -> Any:
    """
    Retrieve an environment variable or config value.
    In a real system, this might read from a sensor or config file.
    For this implementation, we read from environment variables or a local config dict.
    """
    # Fallback to environment variables
    val = os.environ.get(key.upper())
    if val is not None:
        try:
            return float(val)
        except ValueError:
            return val
    return default

def validate_environmental_conditions(conditions: Dict[str, Any]) -> List[str]:
    """
    Validate that logged conditions are within expected ranges.
    """
    issues = []
    # Example validation logic
    if 'temperature_c' in conditions:
        if not (0 <= conditions['temperature_c'] <= 50):
            issues.append("Temperature out of expected range (0-50°C).")
    return issues

def record_run_environment(
    solvent_name: str,
    temperature_c: float,
    relative_humidity_pct: float,
    barometric_pressure_hPa: float,
    substrate_mass_mg: float,
    integration_time_ms: float,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a single run's environmental parameters.
    
    Raises:
        ConfigurationError: If barometric_pressure is missing or invalid.
    """
    if barometric_pressure_hPa is None:
        raise ConfigurationError(
            "barometric_pressure_hPa is missing. "
            "This field is required by FR-007 and SC-004."
        )
    
    if run_id is None:
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "solvent_name": solvent_name,
        "temperature_c": temperature_c,
        "relative_humidity_pct": relative_humidity_pct,
        "barometric_pressure_hPa": barometric_pressure_hPa,
        "substrate_mass_mg": substrate_mass_mg,
        "integration_time_ms": integration_time_ms
    }

def get_environment_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for the environment logs.
    """
    if not logs:
        return {}
    
    temps = [l['temperature_c'] for l in logs if 'temperature_c' in l]
    humids = [l['relative_humidity_pct'] for l in logs if 'relative_humidity_pct' in l]
    
    return {
        "total_runs": len(logs),
        "avg_temperature_c": sum(temps)/len(temps) if temps else None,
        "avg_humidity_pct": sum(humids)/len(humids) if humids else None
    }

def write_environment_logs(logs: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write the list of environment logs to data/processed/environment_logs.json.
    
    Args:
        logs: List of run dictionaries.
        output_path: Output path. Defaults to processed/environment_logs.json.
    
    Returns:
        Path to the written file.
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "environment_logs.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": get_environment_summary(logs),
        "runs": logs
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Environment logs written to {output_path}")
    return output_path

def main():
    """
    Entry point to generate sample environment logs.
    This script simulates the logging of a series of runs for testing T014.
    In a real pipeline, this would be called by the experiment runner.
    """
    setup_logging()
    logger.info("Starting Environment Logging (T014)...")
    
    # Simulate a series of runs (as if T013 configured a series)
    # We use fixed values to ensure determinism for the test, 
    # but in a real run these would come from sensors.
    # Note: barometric_pressure is explicitly set to satisfy the constraint.
    
    sample_runs = [
        record_run_environment(
            solvent_name="cyclohexane",
            temperature_c=25.1,
            relative_humidity_pct=49.5,
            barometric_pressure_hPa=1013.25,
            substrate_mass_mg=10.5,
            integration_time_ms=100.0,
            run_id="run_001"
        ),
        record_run_environment(
            solvent_name="toluene",
            temperature_c=24.8,
            relative_humidity_pct=50.2,
            barometric_pressure_hPa=1013.20,
            substrate_mass_mg=10.5,
            integration_time_ms=100.0,
            run_id="run_002"
        ),
        record_run_environment(
            solvent_name="dichloromethane",
            temperature_c=25.0,
            relative_humidity_pct=49.8,
            barometric_pressure_hPa=1013.25,
            substrate_mass_mg=10.5,
            integration_time_ms=100.0,
            run_id="run_003"
        ),
        record_run_environment(
            solvent_name="ethanol",
            temperature_c=25.2,
            relative_humidity_pct=50.1,
            barometric_pressure_hPa=1013.25,
            substrate_mass_mg=10.5,
            integration_time_ms=100.0,
            run_id="run_004"
        ),
        record_run_environment(
            solvent_name="acetonitrile",
            temperature_c=24.9,
            relative_humidity_pct=49.9,
            barometric_pressure_hPa=1013.25,
            substrate_mass_mg=10.5,
            integration_time_ms=100.0,
            run_id="run_005"
        )
    ]
    
    try:
        output_file = write_environment_logs(sample_runs)
        logger.info(f"Environment logging complete. Output: {output_file}")
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
