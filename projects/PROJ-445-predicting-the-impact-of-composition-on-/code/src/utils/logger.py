import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "state"
LOG_FILE = LOG_DIR / "pipeline.log"
MANIFEST_FILE = PROJECT_ROOT / "state" / "manifest.json"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

class LoggerConfig:
    """Configuration for the project logger."""
    def __init__(
        self,
        name: str = "chalcogenide_pipeline",
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
        console: bool = True
    ):
        self.name = name
        self.level = level
        self.log_file = log_file or LOG_FILE
        self.console = console
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        if logger.handlers:
            return logger

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if self.console:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(self.level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        if self.log_file:
            fh = logging.FileHandler(self.log_file)
            fh.setLevel(self.level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        return logger

    def get_logger(self) -> logging.Logger:
        return self.logger


def initialize_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Initialize the global logging infrastructure.

    Args:
        log_level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Optional path to log file. Defaults to state/pipeline.log
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    level = level_map.get(log_level.upper(), logging.INFO)

    if log_file:
        log_path = Path(log_file)
    else:
        log_path = LOG_FILE

    config = LoggerConfig(
        name="chalcogenide_pipeline",
        level=level,
        log_file=log_path,
        console=console
    )
    return config.get_logger()


def log_error_to_manifest(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error to the manifest file for tracking.

    Args:
        error_type: Type of error (e.g., 'DATA_MISSING', 'TRAINING_FAILED')
        error_message: Detailed error message
        context: Optional dictionary of context information
    """
    if not MANIFEST_FILE.exists():
        # Initialize manifest if it doesn't exist
        manifest = {"artifacts": {}, "errors": []}
    else:
        try:
            with open(MANIFEST_FILE, 'r') as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError):
            manifest = {"artifacts": {}, "errors": []}

    if "errors" not in manifest:
        manifest["errors"] = []

    error_entry = {
        "timestamp": logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord(
            "", logging.INFO, "", 0, "", (), None
        )),
        "type": error_type,
        "message": error_message,
        "context": context or {}
    }
    manifest["errors"].append(error_entry)

    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)


def log_data_missing_error(column_name: str, file_path: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a specific data missing error as per SC-005.

    Args:
        column_name: Name of the missing column
        file_path: Path to the file where the column was expected
        logger: Logger instance to use
    """
    msg = f"DATA_MISSING: Required column {column_name} not found in {file_path}"
    logger = logger or initialize_logging()
    logger.error(msg)
    log_error_to_manifest("DATA_MISSING", msg, {"column": column_name, "file": file_path})


def log_variable_availability_success(predictors: list, logger: Optional[logging.Logger] = None) -> None:
    """
    Log success marker for variable availability as per SC-008.

    Args:
        predictors: List of predictor variables found
        logger: Logger instance to use
    """
    msg = f"Dataset variable availability is confirmed. Found predictors: {', '.join(predictors)}"
    logger = logger or initialize_logging()
    logger.info(msg)


def log_variable_missing_error(predictor_name: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a specific variable missing error as per SC-008.

    Args:
        predictor_name: Name of the missing predictor
        logger: Logger instance to use
    """
    msg = f"DATA_MISSING: Predictor {predictor_name} not found"
    logger = logger or initialize_logging()
    logger.error(msg)
    log_error_to_manifest("VARIABLE_MISSING", msg, {"predictor": predictor_name})


def main():
    """
    Main entry point for testing the logger module.
    """
    logger = initialize_logging(log_level="DEBUG")
    logger.info("Logger initialized successfully.")
    
    log_variable_availability_success(["mean_coordination", "electronegativity_variance"], logger)
    
    log_data_missing_error("Tg", "data/raw/sample.csv", logger)
    
    log_variable_missing_error("atomic_radius_variance", logger)
    
    logger.info("Logging infrastructure test completed.")

if __name__ == "__main__":
    main()