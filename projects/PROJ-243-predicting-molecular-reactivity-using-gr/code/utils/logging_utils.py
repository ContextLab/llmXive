import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config, ensure_directories

# Global metrics storage for the session
_metrics_buffer: Dict[str, Any] = {}
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the root logger and project-specific logger.
    Sets up file handlers for structured logs and console handlers.
    """
    config = get_config()
    ensure_directories()

    log_dir = os.path.join("artifacts", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = datetime.now().strftime("run_%Y%m%d_%H%M%S.log")
    log_path = os.path.join(log_dir, log_filename)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates in interactive environments
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for structured logs
    file_handler = logging.FileHandler(log_path)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Create project logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a logger. Initializes if not already set up.
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger

def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """
    Record a metric to the in-memory buffer and append to metrics.json.
    Handles JSON serialization safely.
    """
    global _metrics_buffer
    config = get_config()
    ensure_directories()

    metrics_path = os.path.join("artifacts", "metrics.json")
    
    # Load existing metrics if file exists
    existing_metrics = []
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    existing_metrics = json.loads(content)
                else:
                    existing_metrics = []
        except (json.JSONDecodeError, IOError):
            existing_metrics = []

    # Prepare new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "key": key,
        "value": value,
        "step": step
    }
    
    # Convert numpy types or other non-serializable types
    def convert_value(v):
        if isinstance(v, (int, float, str, bool, type(None))):
            return v
        if hasattr(v, 'item'): # numpy scalar
            return v.item()
        return str(v)

    entry["value"] = convert_value(entry["value"])

    existing_metrics.append(entry)
    _metrics_buffer[key] = value

    # Write back to file (append mode for robustness, but overwrite to keep clean JSON list)
    # Using 'w' mode to ensure valid JSON structure at all times if the process crashes
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(existing_metrics, f, indent=2)

def flush_metrics() -> None:
    """
    Finalize metrics log (no-op in this implementation as writes are immediate,
    but kept for API compatibility).
    """
    pass

def get_metrics() -> Dict[str, Any]:
    """
    Return the current in-memory metrics buffer.
    """
    return _metrics_buffer.copy()

def log_execution_summary(summary: Dict[str, Any]) -> None:
    """
    Log a structured summary of the execution (e.g., success/failure, counts).
    """
    logger = get_logger()
    logger.info("Execution Summary: %s", json.dumps(summary))
    for key, value in summary.items():
        log_metric(f"summary.{key}", value)

def main() -> None:
    """
    Entry point for testing the logging utility.
    """
    logger = setup_logging()
    logger.info("Logging infrastructure initialized successfully.")
    
    # Test metric logging
    log_metric("test_metric", 42.0, step=1)
    log_metric("test_string", "hello", step=2)
    
    # Test summary
    log_execution_summary({"status": "success", "items_processed": 100})
    
    logger.info("Logging test complete. Check artifacts/logs/ and artifacts/metrics.json")

if __name__ == "__main__":
    main()