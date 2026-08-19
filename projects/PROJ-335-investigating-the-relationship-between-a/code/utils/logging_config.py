import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure the data/results directory exists for log file output
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines for structured logging.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Include any extra fields passed to the log call
        if hasattr(record, 'extra_data'):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)

def setup_logging(console_level: int = logging.INFO, 
                  file_level: int = logging.DEBUG,
                  log_filename: Optional[str] = None) -> None:
    """
    Configure the root logger to output structured logs to both console and file.
    
    Args:
        console_level: Logging level for console output (default: INFO)
        file_level: Logging level for file output (default: DEBUG)
        log_filename: Optional filename for the log file. If None, uses timestamped name.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Capture all, filters applied by handlers

    # Clear existing handlers to avoid duplicates on re-runs
    root_logger.handlers.clear()

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # 2. File Handler (Structured JSON)
    if log_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"pipeline_{timestamp}.log"
    
    log_path = RESULTS_DIR / log_filename
    
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # Log startup confirmation
    logging.info(f"Logging infrastructure initialized. Output to: {log_path}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Name for the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_metric(logger: logging.Logger, metric_name: str, value: float, 
               subject_id: Optional[str] = None, **kwargs) -> None:
    """
    Helper function to log a metric with structured extra data.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Value of the metric
        subject_id: Optional subject ID
        **kwargs: Additional key-value pairs to include in the log data
    """
    extra_data = {
        "metric": metric_name,
        "value": value
    }
    if subject_id:
        extra_data["subject_id"] = subject_id
    extra_data.update(kwargs)
    
    # Attach extra data to the log record via a custom attribute
    # We use a wrapper to inject this into the formatter
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, 
        f"Metric recorded: {metric_name} = {value}", 
        (), None
    )
    record.extra_data = extra_data
    logger.handle(record)

def main():
    """
    Test function to demonstrate logging configuration.
    """
    setup_logging()
    logger = get_logger("T008_Test")
    
    logger.info("Logging system initialized successfully.")
    logger.warning("This is a test warning.")
    logger.error("This is a test error.")
    
    # Test structured metric logging
    log_metric(logger, "alpha_power", 0.85, subject_id="001", channel="Fz")
    
    logger.info("Test completed. Check data/results/ for log files.")

if __name__ == "__main__":
    main()