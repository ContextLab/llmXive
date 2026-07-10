"""
Structured logging for data gaps and fetch errors.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Define custom log levels for specific research events
DATA_GAP = 25
FETCH_ERROR = 25
DATA_VALIDATION = 25

logging.addLevelName(DATA_GAP, "DATA_GAP")
logging.addLevelName(FETCH_ERROR, "FETCH_ERROR")
logging.addLevelName(DATA_VALIDATION, "DATA_VALIDATION")

def _log_gap(self, message, *args, **kwargs):
    if self.isEnabledFor(DATA_GAP):
        self._log(DATA_GAP, message, args, **kwargs)

def _log_fetch_error(self, message, *args, **kwargs):
    if self.isEnabledFor(FETCH_ERROR):
        self._log(FETCH_ERROR, message, args, **kwargs)

def _log_validation(self, message, *args, **kwargs):
    if self.isEnabledFor(DATA_VALIDATION):
        self._log(DATA_VALIDATION, message, args, **kwargs)

logging.Logger.data_gap = _log_gap
logging.Logger.fetch_error = _log_fetch_error
logging.Logger.validation = _log_validation

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file handler.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if specified)
    if log_file:
        dir_name = os.path.dirname(log_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def log_data_gap(logger: logging.Logger, source: str, start_date: str, end_date: str, duration_days: int, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a data gap event with structured information.
    
    Args:
        logger: Logger instance
        source: Data source name (e.g., 'AMS-02', 'NOAA')
        start_date: Start date of the gap (YYYY-MM-DD)
        end_date: End date of the gap (YYYY-MM-DD)
        duration_days: Duration of the gap in days
        details: Optional dictionary with additional context
    """
    msg = f"DATA_GAP: Source={source}, Range=[{start_date}, {end_date}], Duration={duration_days} days"
    if details:
        msg += f" | Details={json.dumps(details)}"
    logger.data_gap(msg)

def log_fetch_error(logger: logging.Logger, source: str, url: str, status_code: Optional[int] = None, error_msg: str = "", retry_count: int = 0) -> None:
    """
    Logs a data fetch error with structured information.
    
    Args:
        logger: Logger instance
        source: Data source name
        url: URL that failed
        status_code: HTTP status code if applicable
        error_msg: Error message
        retry_count: Number of retry attempts
    """
    msg = f"FETCH_ERROR: Source={source}, URL={url}"
    if status_code:
        msg += f", Status={status_code}"
    msg += f", Error={error_msg}"
    if retry_count > 0:
        msg += f", Retries={retry_count}"
    logger.fetch_error(msg)

def log_missing_flux(logger: logging.Logger, species: str, rigidity: float, date: str, reason: str) -> None:
    """
    Logs a missing flux measurement event.
    
    Args:
        logger: Logger instance
        species: Particle species (e.g., 'proton', 'helium')
        rigidity: Rigidity value in GV
        date: Date of missing measurement (YYYY-MM-DD)
        reason: Reason for missing data (e.g., 'Below Detection Limit')
    """
    msg = f"DATA_VALIDATION: Species={species}, Rigidity={rigidity} GV, Date={date}, Reason={reason}"
    logger.validation(msg)

# Initialize default logger for the package
logger = setup_logger("cosmic_ray_analysis")