import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import yaml
import json

# Ensure artifacts directory exists
ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

PREPROCESS_LOG_PATH = ARTIFACTS_DIR / "preprocess.yaml"
ANALYSIS_RESULTS_PATH = ARTIFACTS_DIR / "analysis_results.json"

class YAMLLogHandler(logging.Handler):
    """Custom handler that writes structured log events to a YAML file."""
    
    def __init__(self, filepath: Path):
        super().__init__()
        self.filepath = filepath
        self.events: list[Dict[str, Any]] = []
        self.lock = None  # Simplified for single-threaded execution
        
    def emit(self, record: logging.LogRecord):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            event.update(record.extra_data)
        
        self.events.append(event)
        
        # Append to file immediately for persistence
        try:
            with open(self.filepath, 'a') as f:
                yaml.dump([event], f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            # Fallback to stderr if file write fails
            print(f"Failed to write log to {self.filepath}: {e}", file=sys.stderr)

class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON-like structured strings for console."""
    
    def format(self, record: logging.LogRecord):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        return json.dumps(log_data)

def get_logger(name: str, log_to_file: Optional[Path] = None) -> logging.Logger:
    """
    Creates and configures a logger.
    
    Args:
        name: Logger name (usually __name__)
        log_to_file: Optional Path to write structured logs. 
                     If provided, attaches YAMLLogHandler.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    # File handler if requested
    if log_to_file:
        file_handler = YAMLLogHandler(log_to_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

    return logger

def get_preprocess_logger() -> logging.Logger:
    """Returns the specific logger for preprocessing tasks."""
    return get_logger("preprocess", PREPROCESS_LOG_PATH)

def get_analysis_logger() -> logging.Logger:
    """Returns the specific logger for analysis tasks."""
    # Analysis logs to the same YAML initially, but results are saved to JSON
    return get_logger("analysis", PREPROCESS_LOG_PATH)

def log_structured_event(logger: logging.Logger, message: str, level: str = "INFO", **kwargs):
    """
    Helper to log a structured event with extra data.
    
    Args:
        logger: The logger instance.
        message: The log message.
        level: Log level string.
        **kwargs: Additional key-value pairs to include in the log event.
    """
    extra_data = kwargs if kwargs else {}
    # Attach extra data to the record
    record = logger.makeRecord(
        logger.name, 
        getattr(logging, level, logging.INFO), 
        "", 
        0, 
        message, 
        (), 
        None
    )
    record.extra_data = extra_data
    logger.handle(record)

def flush_yaml_logs():
    """
    Placeholder for flushing buffers. 
    In this implementation, YAMLLogHandler writes immediately, 
    but this function ensures any pending operations are done.
    """
    logging.shutdown()

def save_analysis_results(results: Dict[str, Any]) -> None:
    """
    Saves the final analysis results to the canonical JSON artifact.
    
    Args:
        results: Dictionary containing analysis results (correlations, 
                 permutation stats, strata counts, etc.).
    """
    try:
        with open(ANALYSIS_RESULTS_PATH, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"Analysis results saved to {ANALYSIS_RESULTS_PATH}")
    except Exception as e:
        logging.error(f"Failed to save analysis results: {e}")
        raise

def get_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Reads the analysis results from the artifact file if it exists.
    
    Returns:
        Dictionary of results or None if file doesn't exist.
    """
    if not ANALYSIS_RESULTS_PATH.exists():
        return None
    
    try:
        with open(ANALYSIS_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load analysis results: {e}")
        return None

def initialize_logging():
    """
    Initializes the global logging infrastructure.
    Creates the artifacts directory and ensures log handlers are ready.
    """
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    # Clear existing handlers to ensure clean state
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(StructuredFormatter())
    root_logger.addHandler(console)
    
    logging.info("Logging infrastructure initialized.")
    logging.info(f"Preprocess logs will be written to: {PREPROCESS_LOG_PATH}")
    logging.info(f"Analysis results will be written to: {ANALYSIS_RESULTS_PATH}")

# Initialize on module load if this is the entry point
if __name__ == "__main__":
    initialize_logging()
    logger = get_logger("test")
    log_structured_event(logger, "Test log event", extra="value", number=123)
    flush_yaml_logs()