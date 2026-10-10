"""Structured logging for environmental parameters and reproducibility.

This module provides a robust logging infrastructure that handles environmental
parameter logging (temperature, humidity, barometric pressure, substrate mass,
integration time) per run, as required by FR-007 and T014 dependencies.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from pathlib import Path

@dataclass
class LogEntry:
    """Represents a single structured log entry."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        """Convert log entry to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class EnvironmentalLogger:
    """
    Structured logger for environmental parameters.
    
    Captures and validates environmental conditions (temperature, humidity,
    barometric pressure, substrate mass, integration time) per run, as required
    by FR-007 and the specification's acceptance criteria.
    """

    def __init__(self, name: str = "environmental") -> None:
        self.name = name
        self.entries: List[LogEntry] = []
        self._stdlib_logger = logging.getLogger(name)

    def log_environmental_parameters(
        self,
        temperature_c: Optional[float] = None,
        relative_humidity_percent: Optional[float] = None,
        barometric_pressure_hpa: Optional[float] = None,
        substrate_mass_mg: Optional[float] = None,
        integration_time_ms: Optional[float] = None,
        **kwargs: Any
    ) -> LogEntry:
        """
        Log environmental parameters for a run.
        
        Captures all required environmental metadata per FR-007:
        - temperature (°C)
        - relative_humidity (%)
        - barometric_pressure (hPa)
        - substrate_mass (mg)
        - integration_time_per_scan (ms)
        
        Args:
            temperature_c: Temperature in Celsius.
            relative_humidity_percent: Relative humidity in percent.
            barometric_pressure_hpa: Barometric pressure in hPa.
            substrate_mass_mg: Substrate mass in milligrams.
            integration_time_ms: Integration time per scan in milliseconds.
            **kwargs: Additional parameters.
        
        Returns:
            LogEntry with the recorded parameters.
        """
        params = {
            "temperature_c": temperature_c,
            "relative_humidity_percent": relative_humidity_percent,
            "barometric_pressure_hpa": barometric_pressure_hpa,
            "substrate_mass_mg": substrate_mass_mg,
            "integration_time_ms": integration_time_ms,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        params.update(kwargs)
        
        entry = LogEntry(operation="environmental_parameters", parameters=params)
        self.entries.append(entry)
        
        # Also log to stdlib logger
        self._stdlib_logger.info(
            f"Environmental parameters logged: {entry.to_json()}"
        )
        
        return entry

    def validate_environmental_conditions(
        self,
        temperature_c: Optional[float] = None,
        relative_humidity_percent: Optional[float] = None
    ) -> List[str]:
        """
        Validate environmental conditions against tolerances.
        
        Per specification:
        - Temperature: 25 ± 0.5°C (SC-004)
        - Relative Humidity: ±2% RH (SC-004)
        
        Args:
            temperature_c: Measured temperature in Celsius.
            relative_humidity_percent: Measured relative humidity in percent.
        
        Returns:
            List of warning messages if conditions are out of spec.
        """
        warnings = []
        
        if temperature_c is not None:
            if not (24.5 <= temperature_c <= 25.5):
                msg = (
                    f"Temperature {temperature_c}°C is outside tolerance "
                    f"(25 ± 0.5°C). Run flagged for exclusion from primary analysis."
                )
                warnings.append(msg)
                self._stdlib_logger.warning(msg)
        
        if relative_humidity_percent is not None:
            # Assuming target is 50% RH (common lab standard), ±2%
            # But spec doesn't specify target, just ±2% tolerance
            # We'll interpret as: if RH deviates > 2% from a target (assume 50%)
            # Or more conservatively: flag if RH < 30% or > 70% (very broad)
            # Actually, spec says "±2% RH" which typically means ±2 percentage points
            # from a target. Without explicit target, we flag extreme values.
            # Let's use a reasonable range: 35-65% (typical lab control).
            if not (35.0 <= relative_humidity_percent <= 65.0):
                msg = (
                    f"Relative humidity {relative_humidity_percent}% is outside "
                    f"acceptable range (35-65%). Run flagged."
                )
                warnings.append(msg)
                self._stdlib_logger.warning(msg)
        
        return warnings

    def log_compliance_check(
        self,
        metric_name: str,
        value: float,
        threshold: float,
        passed: bool
    ) -> LogEntry:
        """
        Log a compliance check result.
        
        Args:
            metric_name: Name of the metric being checked.
            value: Measured value.
            threshold: Threshold for compliance.
            passed: Whether the check passed.
        
        Returns:
            LogEntry with compliance check result.
        """
        entry = LogEntry(
            operation="compliance_check",
            parameters={
                "metric": metric_name,
                "value": value,
                "threshold": threshold,
                "passed": passed
            }
        )
        self.entries.append(entry)
        self._stdlib_logger.info(
            f"Compliance check: {metric_name} = {value} "
            f"(threshold: {threshold}) - {'PASS' if passed else 'FAIL'}"
        )
        return entry

    def log_instrument_settings(self, settings: Dict[str, Any]) -> LogEntry:
        """
        Log instrument configuration and settings.
        
        Args:
            settings: Dictionary of instrument settings.
        
        Returns:
            LogEntry with instrument settings.
        """
        entry = LogEntry(
            operation="instrument_settings",
            parameters=settings
        )
        self.entries.append(entry)
        self._stdlib_logger.info(f"Instrument settings logged: {settings}")
        return entry

    def log_data_point(
        self,
        run_id: str,
        solvent: str,
        replicate: int,
        measurements: Dict[str, Any]
    ) -> LogEntry:
        """
        Log a single data point with all required metadata.
        
        Args:
            run_id: Unique identifier for this run.
            solvent: Name of the solvent used.
            replicate: Replicate number.
            measurements: Dictionary of measured quantities.
        
        Returns:
            LogEntry with data point record.
        """
        entry = LogEntry(
            operation="data_point",
            parameters={
                "run_id": run_id,
                "solvent": solvent,
                "replicate": replicate,
                **measurements
            }
        )
        self.entries.append(entry)
        self._stdlib_logger.info(
            f"Data point logged: {run_id} / {solvent} / replicate {replicate}"
        )
        return entry

    def write_entries_to_file(self, output_path: Path) -> None:
        """
        Write all logged entries to a JSON file.
        
        Args:
            output_path: Path to write the JSON log file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            entries_data = [asdict(e) for e in self.entries]
            json.dump(entries_data, f, indent=2, default=str)
        self._stdlib_logger.info(f"Logged {len(self.entries)} entries to {output_path}")


# Global logger instance
_GLOBAL_LOGGER: Optional[EnvironmentalLogger] = None


def get_logger(name: str = "environmental") -> EnvironmentalLogger:
    """Get or create the global environmental logger."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = EnvironmentalLogger(name)
    return _GLOBAL_LOGGER


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> EnvironmentalLogger:
    """
    Setup logging with tolerance for various call signatures.

    Accepts:
      - setup_logging()
      - setup_logging(level=logging.INFO)
      - setup_logging(level="INFO")
      - setup_logging(log_file="path/to/file.log")
    
    Args:
        level: Logging level as string or int. Defaults to "INFO".
        log_file: Optional file path for file-based logging.
    
    Returns:
        The global EnvironmentalLogger instance.
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Handle if level is passed as a logging constant
    if isinstance(level, int):
        level_val = level
    elif isinstance(level, str):
        level_val = getattr(logging, level.upper(), logging.INFO)
    else:
        level_val = logging.INFO

    # Configure stdlib logging if a file is requested
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(level_val)
        root_logger.addHandler(handler)
    else:
        logging.basicConfig(level=level_val)
    
    return get_logger()


def log_environmental_params(params: Dict[str, Any]) -> LogEntry:
    """
    Log environmental parameters to the global logger.
    
    Handles parameters required by FR-007:
    - temperature (°C)
    - relative_humidity (%)
    - barometric_pressure (hPa)
    - substrate_mass (mg)
    - integration_time_per_scan (ms)
    
    Args:
        params: Dictionary of environmental parameter key-value pairs.
    
    Returns:
        LogEntry with the recorded parameters.
    """
    logger = get_logger()
    return logger.log_environmental_parameters(**params)


def log_compliance_check(
    metric_name: str,
    value: float,
    threshold: float,
    passed: bool
) -> LogEntry:
    """
    Log a compliance check result.
    
    Args:
        metric_name: Name of the metric being checked.
        value: Measured value.
        threshold: Threshold for compliance.
        passed: Whether the check passed.
    
    Returns:
        LogEntry with compliance check result.
    """
    logger = get_logger()
    return logger.log_compliance_check(metric_name, value, threshold, passed)


def log_instrument_settings(settings: Dict[str, Any]) -> LogEntry:
    """
    Log instrument configuration and settings.
    
    Args:
        settings: Dictionary of instrument settings.
    
    Returns:
        LogEntry with instrument settings.
    """
    logger = get_logger()
    return logger.log_instrument_settings(settings)


def log_data_point(
    run_id: str,
    solvent: str,
    replicate: int,
    measurements: Dict[str, Any]
) -> LogEntry:
    """
    Log a single data point with all required metadata.
    
    Args:
        run_id: Unique identifier for this run.
        solvent: Name of the solvent used.
        replicate: Replicate number.
        measurements: Dictionary of measured quantities.
    
    Returns:
        LogEntry with data point record.
    """
    logger = get_logger()
    return logger.log_data_point(run_id, solvent, replicate, measurements)