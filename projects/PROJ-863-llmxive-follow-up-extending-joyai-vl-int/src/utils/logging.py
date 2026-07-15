"""
Execution logging utilities for the llmXive pipeline.

Implements FR-001.1: Structured execution logging to track pipeline progress,
data sources, and verify zero VLM API calls during labeling.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Constants for log file locations
LOG_DIR = Path("logs")
LOG_FILE_NAME = "execution.log"
METRICS_FILE_NAME = "metrics.jsonl"

# Global logger instance
_logger: Optional[logging.Logger] = None
_metrics_buffer: List[Dict[str, Any]] = []
_metrics_file_path: Optional[Path] = None


def _ensure_log_dir() -> Path:
    """Ensure the logs directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    metrics_file: Optional[Union[str, Path]] = None,
) -> logging.Logger:
    """
    Configure the global logger and metrics file paths.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path for the log file. Defaults to logs/execution.log.
        metrics_file: Optional path for the metrics JSONL file. Defaults to logs/metrics.jsonl.

    Returns:
        The configured logger instance.
    """
    global _logger, _metrics_file_path

    if _logger is not None:
        return _logger

    _ensure_log_dir()

    # Set up file paths
    if log_file is None:
        log_file = LOG_DIR / LOG_FILE_NAME
    else:
        log_file = Path(log_file)
        if not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)

    if metrics_file is None:
        metrics_file = LOG_DIR / METRICS_FILE_NAME
    else:
        metrics_file = Path(metrics_file)
        if not metrics_file.parent.exists():
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    _metrics_file_path = metrics_file

    # Create logger
    _logger = logging.getLogger("llmxive_pipeline")
    _logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    _logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)

    _logger.info("Logging system initialized.")
    return _logger


def get_logger() -> logging.Logger:
    """
    Get the global logger instance.

    Raises:
        RuntimeError: If logging has not been initialized.
    """
    if _logger is None:
        raise RuntimeError(
            "Logger not initialized. Call setup_logging() before using get_logger()."
        )
    return _logger


def log_execution_start(stage: str, parameters: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline execution stage.

    Args:
        stage: The name of the stage (e.g., "data_generation", "feature_extraction").
        parameters: Optional dictionary of parameters for this run.
    """
    logger = get_logger()
    logger.info(f"--- EXECUTION START: {stage} ---")
    if parameters:
        logger.info(f"Parameters: {json.dumps(parameters, indent=2)}")


def log_execution_end(stage: str, success: bool = True, duration_seconds: Optional[float] = None) -> None:
    """
    Log the end of a pipeline execution stage.

    Args:
        stage: The name of the stage.
        success: Whether the stage completed successfully.
        duration_seconds: Optional duration of the stage in seconds.
    """
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"
    msg = f"--- EXECUTION END: {stage} [{status}] ---"
    if duration_seconds is not None:
        msg += f" Duration: {duration_seconds:.2f}s"
    logger.info(msg)


def log_data_source(source_type: str, source_path: str, record_count: Optional[int] = None) -> None:
    """
    Log information about a data source used in the pipeline.

    Args:
        source_type: Type of data source (e.g., "video", "labels", "features").
        source_path: Path to the data source.
        record_count: Optional number of records processed.
    """
    logger = get_logger()
    msg = f"Data Source: {source_type} -> {source_path}"
    if record_count is not None:
        msg += f" (Records: {record_count})"
    logger.info(msg)


def log_vlm_api_call(model_name: str, input_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a VLM API call.

    This function is critical for FR-001.1 to verify zero VLM calls during labeling.
    If called during labeling, it should trigger a warning or error.

    Args:
        model_name: Name of the VLM model used.
        input_data: Optional input data sent to the model.
    """
    logger = get_logger()
    warning_msg = f"⚠️ VLM API CALL DETECTED: {model_name}"
    logger.warning(warning_msg)
    if input_data:
        logger.warning(f"Input: {json.dumps(input_data, indent=2)}")


def log_metric(name: str, value: float, stage: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a metric value to the metrics JSONL file.

    Args:
        name: Name of the metric (e.g., "f1_score", "inference_latency").
        value: The metric value.
        stage: Optional stage name where the metric was computed.
        metadata: Optional additional metadata.
    """
    if _metrics_file_path is None:
        setup_logging()  # Initialize if not already done

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "metric_name": name,
        "value": value,
        "stage": stage,
        "metadata": metadata or {},
    }

    # Append to buffer and write to file
    with open(_metrics_file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def log_event(event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a custom event with structured details.

    Args:
        event_type: Type of event (e.g., "error", "warning", "info").
        details: Optional dictionary of event details.
    """
    logger = get_logger()
    if details:
        logger.info(f"Event: {event_type} - {json.dumps(details)}")
    else:
        logger.info(f"Event: {event_type}")


def verify_zero_vlm_calls(log_file: Optional[Union[str, Path]] = None) -> bool:
    """
    Verify that the execution log contains zero VLM API calls.

    This is a critical check for FR-001.1 during the data labeling phase.

    Args:
        log_file: Optional path to the log file. Defaults to logs/execution.log.

    Returns:
        True if zero VLM calls are found, False otherwise.
    """
    if log_file is None:
        log_file = LOG_DIR / LOG_FILE_NAME
    else:
        log_file = Path(log_file)

    if not log_file.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")

    vlm_call_count = 0
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if "VLM API CALL DETECTED" in line:
                vlm_call_count += 1

    return vlm_call_count == 0


def get_log_summary() -> Dict[str, Any]:
    """
    Get a summary of the execution log.

    Returns:
        Dictionary containing log statistics.
    """
    log_file = LOG_DIR / LOG_FILE_NAME
    if not log_file.exists():
        return {"error": "Log file not found"}

    summary = {
        "total_lines": 0,
        "info_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "vlm_call_count": 0,
        "stages": set(),
    }

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            summary["total_lines"] += 1
            if "INFO" in line:
                summary["info_count"] += 1
            elif "WARNING" in line:
                summary["warning_count"] += 1
            elif "ERROR" in line:
                summary["error_count"] += 1
            if "VLM API CALL DETECTED" in line:
                summary["vlm_call_count"] += 1
            if "EXECUTION START:" in line:
                stage = line.split("EXECUTION START:")[1].split(" ---")[0].strip()
                summary["stages"].add(stage)

    summary["stages"] = list(summary["stages"])
    return summary