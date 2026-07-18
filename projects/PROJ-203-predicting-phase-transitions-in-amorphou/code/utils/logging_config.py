"""
Logging infrastructure for the Phase Transitions pipeline.

Configures loggers to capture simulation truncations, missing data events,
and general pipeline execution flow.
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import code.config as config


# Constants for log levels
TRUNCATION_LEVEL = 25  # Between INFO and WARNING
MISSING_DATA_LEVEL = 23  # Between DEBUG and INFO

# Register custom log levels
logging.addLevelName(TRUNCATION_LEVEL, "TRUNCATION")
logging.addLevelName(MISSING_DATA_LEVEL, "MISSING_DATA")


class TruncationLoggerAdapter(logging.LoggerAdapter):
    """Adapter to log simulation truncation events with structured metadata."""
    
    def truncation(self, msg: str, composition_id: str, steps_completed: int, 
                   expected_steps: int, reason: str, extra: Optional[Dict[str, Any]] = None):
        """Log a simulation truncation event."""
        if extra is None:
            extra = {}
        extra.update({
            "event_type": "simulation_truncation",
            "composition_id": composition_id,
            "steps_completed": steps_completed,
            "expected_steps": expected_steps,
            "reason": reason
        })
        self.log(TRUNCATION_LEVEL, msg, extra=extra)


class MissingDataLoggerAdapter(logging.LoggerAdapter):
    """Adapter to log missing data events."""
    
    def missing_data(self, msg: str, entity_type: str, entity_id: str, 
                     missing_fields: list, severity: str = "WARNING", extra: Optional[Dict[str, Any]] = None):
        """Log a missing data event."""
        if extra is None:
            extra = {}
        extra.update({
            "event_type": "missing_data",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "missing_fields": missing_fields,
            "severity": severity
        })
        self.log(MISSING_DATA_LEVEL, msg, extra=extra)


def get_truncation_logger(name: str) -> TruncationLoggerAdapter:
    """Get a logger configured for truncation events."""
    logger = logging.getLogger(f"truncations.{name}")
    if not logger.handlers:
        logger.setLevel(TRUNCATION_LEVEL)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - TRUNCATION - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return TruncationLoggerAdapter(logger, {})


def get_missing_data_logger(name: str) -> MissingDataLoggerAdapter:
    """Get a logger configured for missing data events."""
    logger = logging.getLogger(f"missing_data.{name}")
    if not logger.handlers:
        logger.setLevel(MISSING_DATA_LEVEL)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - MISSING_DATA - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return MissingDataLoggerAdapter(logger, {})


def setup_pipeline_logging():
    """
    Configure the main pipeline logging infrastructure.
    
    Sets up:
    1. Console logging for general pipeline flow
    2. File logging for simulation truncations
    3. File logging for missing data events
    4. JSON log export for structured analysis
    """
    # Ensure log directory exists
    log_dir = Path(config.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    truncation_log_path = log_dir / f"truncations_{timestamp}.log"
    missing_data_log_path = log_dir / f"missing_data_{timestamp}.log"
    pipeline_log_path = log_dir / f"pipeline_{timestamp}.log"
    json_log_path = log_dir / f"events_{timestamp}.json"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler for general flow
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general pipeline
    pipeline_handler = logging.FileHandler(pipeline_log_path)
    pipeline_handler.setLevel(logging.DEBUG)
    pipeline_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    pipeline_handler.setFormatter(pipeline_formatter)
    root_logger.addHandler(pipeline_handler)
    
    # File handler for truncations
    truncation_handler = logging.FileHandler(truncation_log_path)
    truncation_handler.setLevel(TRUNCATION_LEVEL)
    truncation_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - TRUNCATION - %(message)s'
    )
    truncation_handler.setFormatter(truncation_formatter)
    
    truncation_logger = logging.getLogger("truncations")
    truncation_logger.addHandler(truncation_handler)
    truncation_logger.setLevel(TRUNCATION_LEVEL)
    
    # File handler for missing data
    missing_handler = logging.FileHandler(missing_data_log_path)
    missing_handler.setLevel(MISSING_DATA_LEVEL)
    missing_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - MISSING_DATA - %(message)s'
    )
    missing_handler.setFormatter(missing_formatter)
    
    missing_logger = logging.getLogger("missing_data")
    missing_logger.addHandler(missing_handler)
    missing_logger.setLevel(MISSING_DATA_LEVEL)
    
    # JSON event logger for structured analysis
    json_logger = logging.getLogger("json_events")
    json_logger.setLevel(logging.DEBUG)
    json_logger.handlers.clear()
    
    # Store log paths in config for later retrieval
    config.LOG_PATHS = {
        "pipeline": str(pipeline_log_path),
        "truncations": str(truncation_log_path),
        "missing_data": str(missing_data_log_path),
        "events_json": str(json_log_path)
    }
    
    # Log initialization
    root_logger.info(f"Pipeline logging initialized. Logs written to: {log_dir}")
    root_logger.info(f"Truncation log: {truncation_log_path}")
    root_logger.info(f"Missing data log: {missing_data_log_path}")
    
    return {
        "truncation_logger": get_truncation_logger("pipeline"),
        "missing_data_logger": get_missing_data_logger("pipeline"),
        "log_paths": config.LOG_PATHS
    }


def log_simulation_truncation(composition_id: str, steps_completed: int, 
                              expected_steps: int, reason: str):
    """
    Log a simulation truncation event.
    
    Args:
        composition_id: The ID of the composition being simulated
        steps_completed: Number of steps actually completed
        expected_steps: Number of steps that were intended
        reason: Reason for truncation (e.g., "time_limit_exceeded", "convergence_failed")
    """
    logger = get_truncation_logger("pipeline")
    logger.truncation(
        f"Simulation truncated for {composition_id}: {steps_completed}/{expected_steps} steps completed. Reason: {reason}",
        composition_id=composition_id,
        steps_completed=steps_completed,
        expected_steps=expected_steps,
        reason=reason
    )


def log_missing_data(entity_type: str, entity_id: str, missing_fields: list, 
                    severity: str = "WARNING"):
    """
    Log a missing data event.
    
    Args:
        entity_type: Type of entity (e.g., "composition", "descriptor", "property")
        entity_id: ID of the specific entity
        missing_fields: List of missing field names
        severity: Severity level ("WARNING", "ERROR", "CRITICAL")
    """
    logger = get_missing_data_logger("pipeline")
    logger.missing_data(
        f"Missing data detected in {entity_type} '{entity_id}': {', '.join(missing_fields)}",
        entity_type=entity_type,
        entity_id=entity_id,
        missing_fields=missing_fields,
        severity=severity
    )


def export_events_to_json(events: list, output_path: Optional[str] = None):
    """
    Export a list of events to a JSON file.
    
    Args:
        events: List of event dictionaries
        output_path: Path for the output JSON file (uses config if not provided)
    """
    if output_path is None:
        output_path = config.LOG_PATHS.get("events_json", "data/logs/events.json")
    
    with open(output_path, 'w') as f:
        json.dump(events, f, indent=2, default=str)
    
    logging.info(f"Exported {len(events)} events to {output_path}")