"""
Logging utilities for the cosmic ray analysis pipeline.

This module provides structured logging functions for:
- Setting up loggers
- Logging data gaps
- Logging fetch errors
- Logging missing flux data
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Parameters:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger

def log_data_gap(logger: logging.Logger, start_date: str, end_date: str, 
                 duration_days: int, table: str = "unified_timeseries") -> None:
    """
    Log a data gap with structured information.
    
    Parameters:
        logger: Logger instance
        start_date: Start date of the gap
        end_date: End date of the gap
        duration_days: Duration of the gap in days
        table: Name of the affected table
    """
    gap_info = {
        "event": "data_gap",
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration_days,
        "table": table,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.warning(f"Data gap detected: {json.dumps(gap_info)}")

def log_fetch_error(logger: logging.Logger, source: str, error_message: str, 
                   retry_count: int = 0) -> None:
    """
    Log a data fetch error with structured information.
    
    Parameters:
        logger: Logger instance
        source: Data source URL or name
        error_message: Error message
        retry_count: Number of retry attempts
    """
    error_info = {
        "event": "fetch_error",
        "source": source,
        "error": error_message,
        "retry_count": retry_count,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.error(f"Fetch error: {json.dumps(error_info)}")

def log_missing_flux(logger: logging.Logger, date: str, species: str, 
                     rigidity_bin: float, table: str = "unified_timeseries") -> None:
    """
    Log missing flux data with structured information.
    
    Parameters:
        logger: Logger instance
        date: Date of missing data
        species: Species name (proton, helium, etc.)
        rigidity_bin: Rigidity bin value
        table: Name of the affected table
    """
    missing_info = {
        "event": "missing_flux",
        "date": date,
        "species": species,
        "rigidity_bin": rigidity_bin,
        "table": table,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.warning(f"Missing flux data: {json.dumps(missing_info)}")

def log_below_detection_limit(logger: logging.Logger, date: str, species: str,
                              ratio_type: str = "He/p") -> None:
    """
    Log a below detection limit event.
    
    Parameters:
        logger: Logger instance
        date: Date of the event
        species: Species name
        ratio_type: Type of ratio (e.g., "He/p", "Fe/p")
    """
    bdl_info = {
        "event": "below_detection_limit",
        "date": date,
        "species": species,
        "ratio_type": ratio_type,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.warning(f"Below detection limit: {json.dumps(bdl_info)}")

def log_correlation_result(logger: logging.Logger, lag_months: int, 
                           correlation: float, p_value: float, 
                           rigidity_bin: float, method: str) -> None:
    """
    Log a correlation result with structured information.
    
    Parameters:
        logger: Logger instance
        lag_months: Lag in months
        correlation: Correlation coefficient
        p_value: P-value
        rigidity_bin: Rigidity bin value
        method: Correlation method (pearson, spearman)
    """
    corr_info = {
        "event": "correlation_result",
        "lag_months": lag_months,
        "correlation": correlation,
        "p_value": p_value,
        "rigidity_bin": rigidity_bin,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Correlation result: {json.dumps(corr_info)}")

def log_model_fit(logger: logging.Logger, rigidity_bin: float, 
                  amplitude: float, r_squared: float, 
                  method: str = "sinusoidal_fit") -> None:
    """
    Log a model fitting result.
    
    Parameters:
        logger: Logger instance
        rigidity_bin: Rigidity bin value
        amplitude: Modulation amplitude
        r_squared: R-squared value
        method: Fitting method
    """
    fit_info = {
        "event": "model_fit",
        "rigidity_bin": rigidity_bin,
        "amplitude": amplitude,
        "r_squared": r_squared,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Model fit result: {json.dumps(fit_info)}")

def log_bootstrap_result(logger: logging.Logger, rigidity_bin: float,
                         ci_lower: float, ci_upper: float,
                         iterations: int = 1000) -> None:
    """
    Log bootstrap resampling result.
    
    Parameters:
        logger: Logger instance
        rigidity_bin: Rigidity bin value
        ci_lower: Lower bound of 95% CI
        ci_upper: Upper bound of 95% CI
        iterations: Number of bootstrap iterations
    """
    bootstrap_info = {
        "event": "bootstrap_result",
        "rigidity_bin": rigidity_bin,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "iterations": iterations,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Bootstrap result: {json.dumps(bootstrap_info)}")
