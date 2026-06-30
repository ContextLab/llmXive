"""
Utility functions for the music-personality-correlation project.

This module provides shared utilities including logging setup, configuration loading,
and error handling wrappers.

Environment Variables:
  - RANDOM_SEED: Integer seed for reproducibility. Default: 42.
    Used to ensure deterministic behavior in synthetic data generation and random splits.
  - DATA_PATH: Path to the root data directory (e.g., 'data'). Default: 'data'.
    Used as the base path for loading raw datasets and saving processed files.
  - LOG_LEVEL: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: 'INFO'.
    Controls the verbosity of the logging system.
  - HTTP_TIMEOUT: Maximum seconds to wait for network requests (e.g., dataset download). Default: 30.
    Used to prevent hanging during external data ingestion attempts.
  - RESULTS_PATH: Path to the results output directory. Default: 'results'.
    Used for storing generated figures and final analysis reports.
"""

import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Any, Optional
import requests
from requests.exceptions import Timeout, HTTPError, ConnectionError, RequestException


def setup_logging(log_file: str = "logs/app.log", level: int = None) -> logging.Logger:
    """
    Configure and return a logger with file rotation.

    The logger writes to the specified log file with rotation capabilities.
    It also logs to the console.

    Args:
        log_file: Relative path to the log file from the project root.
        level: Logging level. If None, reads from LOG_LEVEL env var or defaults to INFO.

    Returns:
        A configured logging.Logger instance named 'music_personality_logger'.
    """
    # Determine log level
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("music_personality_logger")
    logger.setLevel(level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler with rotation (max 5MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def load_config() -> dict:
    """
    Load configuration from environment variables.

    This function retrieves expected environment variables (RANDOM_SEED, DATA_PATH, LOG_LEVEL, HTTP_TIMEOUT, RESULTS_PATH).
    If a variable is missing, it assigns a sensible default and logs a warning.
    It relies on `setup_logging()` (T005a) being available to report configuration issues.

    Returns:
        A dictionary containing the configuration values:
        - 'RANDOM_SEED': int (default 42)
        - 'DATA_PATH': str (default 'data')
        - 'LOG_LEVEL': str (default 'INFO')
        - 'HTTP_TIMEOUT': int (default 30)
        - 'RESULTS_PATH': str (default 'results')
    """
    logger = setup_logging()
    config = {}

    # Define expected environment variables
    expected_vars = [
        ("RANDOM_SEED", 42, int),
        ("DATA_PATH", "data", str),
        ("LOG_LEVEL", "INFO", str),
        ("HTTP_TIMEOUT", 30, int),
        ("RESULTS_PATH", "results", str),
    ]

    for var_name, default_val, val_type in expected_vars:
        value = os.getenv(var_name)
        if value is None:
            config[var_name] = default_val
            logger.warning(f"Environment variable {var_name} not set. Using default: {default_val}")
        else:
            try:
                if val_type == int:
                    config[var_name] = int(value)
                else:
                    config[var_name] = value
                logger.info(f"Loaded environment variable: {var_name}")
            except ValueError:
                logger.error(f"Invalid {var_name} value '{value}'. Using default {default_val}.")
                config[var_name] = default_val

    return config


def safe_http_request(
    url: str,
    method: str = "GET",
    timeout: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any
) -> Optional[requests.Response]:
    """
    Execute an HTTP request with robust error handling for timeouts and 404s.

    This wrapper attempts the request and catches common network exceptions.
    It logs specific error messages based on the failure type (Timeout, 404 Not Found,
    Connection Error, or generic Request Exception) and returns None on failure.
    If successful, it returns the Response object.

    Args:
        url: The URL to request.
        method: HTTP method ('GET', 'POST', etc.). Default is 'GET'.
        timeout: Maximum seconds to wait. If None, uses HTTP_TIMEOUT from config.
        logger: Logger instance. If None, creates a default one via setup_logging().
        **kwargs: Additional arguments passed to requests.request().

    Returns:
        requests.Response object if successful, None otherwise.
    """
    if logger is None:
        logger = setup_logging()

    if timeout is None:
        # Fallback to default if env var reading fails inside load_config or similar
        config = load_config()
        timeout = config.get("HTTP_TIMEOUT", 30)

    try:
        logger.info(f"Attempting {method} request to {url} with timeout {timeout}s")
        response = requests.request(method, url, timeout=timeout, **kwargs)
        
        # Check for HTTP errors (4xx, 5xx)
        response.raise_for_status()
        return response

    except Timeout:
        logger.error(f"Request timed out after {timeout}s for URL: {url}")
        return None
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.error(f"Resource not found (404) at URL: {url}")
        else:
            status_code = e.response.status_code if e.response else "Unknown"
            logger.error(f"HTTP error {status_code} occurred for URL: {url}. Error: {e}")
        return None
    except ConnectionError:
        logger.error(f"Connection error occurred while trying to reach: {url}")
        return None
    except RequestException as e:
        logger.error(f"General request exception for URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during request to {url}: {e}")
        return None


def download_file(
    url: str,
    dest_path: str,
    timeout: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Download a file from a URL to a local path with error handling.

    This function uses `safe_http_request` to fetch the content and writes it
    to the specified destination path. It handles timeouts and 404s gracefully.

    Args:
        url: The URL of the file to download.
        dest_path: The local file path where the content will be saved.
        timeout: Maximum seconds to wait. If None, uses HTTP_TIMEOUT from config.
        logger: Logger instance. If None, creates a default one.

    Returns:
        True if download was successful, False otherwise.
    """
    if logger is None:
        logger = setup_logging()

    if timeout is None:
        config = load_config()
        timeout = config.get("HTTP_TIMEOUT", 30)

    # Ensure destination directory exists
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    response = safe_http_request(url, method="GET", timeout=timeout, logger=logger)

    if response is None:
        logger.error(f"Failed to download file from {url}. Check logs for details.")
        return False

    try:
        with open(dest, "wb") as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded {url} to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write downloaded content to {dest_path}: {e}")
        return False