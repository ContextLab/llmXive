"""
Structured logging utilities for the llmXive research pipeline.

Provides a consistent logging configuration and helper functions
for structured JSON logging and standard console logging.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
) -> logging.Logger:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to write logs to a file
        json_format: If True, use JSON formatting; otherwise use standard formatting
            
    Returns:
        Configured root logger instance
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter() if json_format else 
                                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Logger name (typically __name__ or module path)
            
    Returns:
        Logger instance configured with project defaults
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: str = "INFO",
    **extra_data,
) -> None:
    """
    Log an event with structured extra data.
    
    Args:
        logger: Logger instance to use
        event_type: Type/category of the event
        message: Human-readable message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **extra_data: Additional key-value pairs to include in the log
    """
    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper(), logging.INFO),
        "",
        0,
        message,
        (),
        None,
    )
    log_record.extra_data = {"event_type": event_type, **extra_data}
    logger.handle(log_record)


def log_sensitivity_results(
    logger: logging.Logger,
    solvent: str,
    timescale: str,
    start_times: list,
    diffusion_coeffs: list,
    variance: float,
    variance_threshold: float = 0.05,
    status: str = "PASS",
) -> None:
    """
    Log structured results from a sensitivity analysis sweep.
    
    This function formats the sensitivity sweep results (start times, calculated
    diffusion coefficients, and variance) into a structured log entry. It also
    flags the result as PASS or FAIL based on the variance threshold.
    
    Args:
        logger: Logger instance to use
        solvent: Name of the solvent analyzed (e.g., 'water', 'ethanol')
        timescale: Simulation duration (e.g., '1ns', '10ns')
        start_times: List of regression start times used in the sweep
        diffusion_coeffs: List of diffusion coefficients calculated for each start time
        variance: Calculated variance of the diffusion coefficients
        variance_threshold: Threshold for variance (default 5% or 0.05)
        status: 'PASS' if variance <= threshold, 'FAIL' otherwise
    """
    log_level = "INFO" if status == "PASS" else "WARNING"
    
    extra_payload = {
        "component": "sensitivity_analysis",
        "solvent": solvent,
        "timescale": timescale,
        "start_times": start_times,
        "diffusion_coeffs": diffusion_coeffs,
        "variance": variance,
        "variance_threshold": variance_threshold,
        "status": status,
    }
    
    log_event(
        logger,
        event_type="sensitivity_sweep_complete",
        message=f"Sensitivity analysis for {solvent} at {timescale}: Variance={variance:.4f} ({status})",
        level=log_level,
        **extra_payload,
    )