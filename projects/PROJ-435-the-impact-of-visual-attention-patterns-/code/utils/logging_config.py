import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
from datetime import datetime

# Constants for log paths relative to project root
LOG_DIR = Path("state/logs")
EXCLUSION_LOG_FILE = "state/exclusion_counts.json"
QUALITY_WARNING_LOG_FILE = "state/quality_warnings.json"
PIPELINE_PROGRESS_LOG_FILE = "state/pipeline_progress.json"

# Ensure log directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global loggers registry
_loggers: Dict[str, logging.Logger] = {}

def setup_logging(
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    config_path: Optional[Path] = None,
) -> None:
    """
    Configure the root logging infrastructure.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Custom format string for log messages.
        date_format: Custom date format string.
        config_path: Optional path to a YAML logging configuration file.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)

    # File handler for general pipeline logs
    pipeline_log_path = LOG_DIR / "pipeline.log"
    file_handler = logging.FileHandler(pipeline_log_path)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    # Load additional config if provided
    if config_path and config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)

def get_quality_logger() -> logging.Logger:
    """
    Get the logger specifically for data quality warnings.

    Returns:
        logging.Logger: Configured logger for quality warnings.
    """
    logger_name = "quality"
    if logger_name not in _loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        if not logger.handlers:
            # File handler for quality warnings
            warning_log_path = LOG_DIR / "quality_warnings.log"
            handler = logging.FileHandler(warning_log_path)
            handler.setLevel(logging.WARNING)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        _loggers[logger_name] = logger
    return _loggers[logger_name]

def get_exclusion_logger() -> logging.Logger:
    """
    Get the logger specifically for exclusion events and counts.

    Returns:
        logging.Logger: Configured logger for exclusions.
    """
    logger_name = "exclusion"
    if logger_name not in _loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            # File handler for exclusions
            exclusion_log_path = LOG_DIR / "exclusions.log"
            handler = logging.FileHandler(exclusion_log_path)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        _loggers[logger_name] = logger
    return _loggers[logger_name]

def get_pipeline_logger() -> logging.Logger:
    """
    Get the general pipeline progress logger.

    Returns:
        logging.Logger: Configured logger for pipeline progress.
    """
    logger_name = "pipeline"
    if logger_name not in _loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            # File handler for pipeline progress
            progress_log_path = LOG_DIR / "pipeline_progress.log"
            handler = logging.FileHandler(progress_log_path)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        _loggers[logger_name] = logger
    return _loggers[logger_name]

def log_data_quality_warning(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "WARNING",
) -> None:
    """
    Log a data quality warning and persist it to a JSON state file.

    Args:
        message: The warning message.
        context: Optional dictionary of additional context (e.g., file, row, value).
        severity: Severity level (WARNING, ERROR, CRITICAL).
    """
    logger = get_quality_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "message": message,
        "context": context or {},
    }

    # Log to file
    if severity == "ERROR":
        logger.error(f"{message} | Context: {context}")
    elif severity == "CRITICAL":
        logger.critical(f"{message} | Context: {context}")
    else:
        logger.warning(f"{message} | Context: {context}")

    # Persist to JSON state file
    _append_to_json_state(QUALITY_WARNING_LOG_FILE, log_entry)

def log_exclusion(
    reason: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exclusion event and update exclusion counts in a JSON state file.

    Args:
        reason: The reason for exclusion (e.g., "data_loss > 20%", "missing_roi").
        entity_type: Type of entity excluded (e.g., "participant", "trial", "headline").
        entity_id: Optional ID of the excluded entity.
        details: Optional additional details about the exclusion.
    """
    logger = get_exclusion_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
    }

    logger.info(f"Excluded {entity_type}: {entity_id or 'N/A'} | Reason: {reason} | Details: {details}")

    # Persist to JSON state file
    _append_to_json_state(EXCLUSION_LOG_FILE, log_entry)

    # Update counts
    _update_exclusion_counts(reason, entity_type)

def log_pipeline_progress(
    stage: str,
    status: str,
    message: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log pipeline progress and update a JSON state file with metrics.

    Args:
        stage: The pipeline stage (e.g., "ingestion", "preprocessing", "regression").
        status: Status of the stage (e.g., "started", "completed", "failed").
        message: Optional descriptive message.
        metrics: Optional dictionary of metrics (e.g., rows processed, time elapsed).
    """
    logger = get_pipeline_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,
        "status": status,
        "message": message,
        "metrics": metrics or {},
    }

    if status == "failed":
        logger.error(f"Stage '{stage}' failed: {message}")
    elif status == "completed":
        logger.info(f"Stage '{stage}' completed: {message} | Metrics: {metrics}")
    else:
        logger.info(f"Stage '{stage}' {status}: {message}")

    # Persist to JSON state file
    _append_to_json_state(PIPELINE_PROGRESS_LOG_FILE, log_entry)

def _append_to_json_state(file_path: str, entry: Dict[str, Any]) -> None:
    """
    Append a log entry to a JSON state file.

    Args:
        file_path: Path to the JSON state file (relative to project root).
        entry: Dictionary entry to append.
    """
    full_path = Path(file_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if full_path.exists():
        with open(full_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(entry)

    with open(full_path, "w") as f:
        json.dump(data, f, indent=2)

def _update_exclusion_counts(reason: str, entity_type: str) -> None:
    """
    Update exclusion counts in a dedicated JSON file.

    Args:
        reason: The reason for exclusion.
        entity_type: Type of entity excluded.
    """
    counts_file = Path("state/exclusion_counts_summary.json")
    counts_file.parent.mkdir(parents=True, exist_ok=True)

    if counts_file.exists():
        with open(counts_file, "r") as f:
            try:
                counts = json.load(f)
            except json.JSONDecodeError:
                counts = {"counts": {}}
    else:
        counts = {"counts": {}}

    key = f"{entity_type}_{reason}"
    counts["counts"][key] = counts["counts"].get(key, 0) + 1

    with open(counts_file, "w") as f:
        json.dump(counts, f, indent=2)

def load_logging_config(config_path: Path) -> Dict[str, Any]:
    """
    Load a logging configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the parsed configuration.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Logging config file not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main() -> None:
    """
    Demonstrate the logging infrastructure setup and usage.
    """
    setup_logging()

    # Example: Log data quality warnings
    log_data_quality_warning(
        "Missing value detected in column 'fixation_duration'",
        context={"row": 123, "file": "raw_data.csv"},
        severity="WARNING",
    )
    log_data_quality_warning(
        "Invalid coordinate values (negative x)",
        context={"row": 456, "file": "raw_data.csv", "value": -5.2},
        severity="ERROR",
    )

    # Example: Log exclusions
    log_exclusion(
        reason="data_loss_percent > 20",
        entity_type="participant",
        entity_id="P001",
        details={"data_loss_percent": 25.5},
    )
    log_exclusion(
        reason="missing_roi_coordinates",
        entity_type="trial",
        entity_id="T042",
        details={"missing_fields": ["roi_x", "roi_y"]},
    )

    # Example: Log pipeline progress
    log_pipeline_progress(
        stage="preprocessing",
        status="started",
        message="Starting I-VT fixation detection",
    )
    log_pipeline_progress(
        stage="preprocessing",
        status="completed",
        message="Fixation detection finished",
        metrics={"total_fixations": 15000, "processing_time_sec": 45.2},
    )
    log_pipeline_progress(
        stage="regression",
        status="failed",
        message="Model convergence failed",
        metrics={"iterations": 100},
    )

    print("Logging infrastructure demo completed. Check state/logs/ and state/*.json for outputs.")

if __name__ == "__main__":
    main()
