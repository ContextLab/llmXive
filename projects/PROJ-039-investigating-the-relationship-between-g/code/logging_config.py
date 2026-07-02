import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import yaml
import json

# Constants for artifact paths
ARTIFACTS_DIR = "artifacts"
PREPROCESS_LOG_PATH = os.path.join(ARTIFACTS_DIR, "preprocess.yaml")
ANALYSIS_RESULTS_PATH = os.path.join(ARTIFACTS_DIR, "analysis_results.json")

# Global storage for structured logs
_preprocess_logs: list[Dict[str, Any]] = []
_analysis_results: Dict[str, Any] = {}
_log_lock = None  # For thread safety if needed later

class YAMLLogHandler(logging.Handler):
    """
    Custom logging handler that captures structured log events
    and writes them to a YAML file.
    """
    def __init__(self, log_list: list):
        super().__init__()
        self.log_list = log_list
        self.setLevel(logging.INFO)
        self.setFormatter(StructuredFormatter())

    def emit(self, record: logging.LogRecord):
        try:
            # Parse the structured message if it exists, otherwise format standard
            msg = self.format(record)
            try:
                # Try to parse as JSON if the formatter output JSON, fallback to string
                if isinstance(record.msg, dict):
                    entry = record.msg
                else:
                    entry = {"message": msg, "level": record.levelname, "timestamp": datetime.now().isoformat()}
                
                # Ensure required fields
                if "timestamp" not in entry:
                    entry["timestamp"] = datetime.now().isoformat()
                if "level" not in entry:
                    entry["level"] = record.levelname
                
                self.log_list.append(entry)
            except Exception:
                # Fallback for non-dict messages
                self.log_list.append({
                    "message": msg,
                    "level": record.levelname,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception:
            self.handleError(record)

class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs JSON-like structured strings for console
    but allows the handler to intercept the raw dict if available.
    """
    def format(self, record):
        if isinstance(record.msg, dict):
            # If the message is already a dict, we return it as a string for console
            # but the handler handles the dict directly.
            return json.dumps(record.msg)
        return super().format(record)

def get_logger(name: str, is_preprocess: bool = False) -> logging.Logger:
    """
    Factory function to get a configured logger.
    If is_preprocess is True, it uses the global preprocess log list.
    Otherwise, it uses standard logging or analysis results dict.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Determine target based on context
    if is_preprocess:
        handler = YAMLLogHandler(_preprocess_logs)
        logger.addHandler(handler)
    else:
        # For analysis, we might want to update the global results dict
        # This is a simplified approach; usually, analysis results are updated explicitly
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    return logger

def get_preprocess_logger() -> logging.Logger:
    """Returns the logger configured for preprocessing tasks."""
    return get_logger("preprocess_logger", is_preprocess=True)

def get_analysis_logger() -> logging.Logger:
    """Returns the logger configured for analysis tasks."""
    return get_logger("analysis_logger", is_preprocess=False)

def log_structured_event(logger: logging.Logger, event_name: str, details: Dict[str, Any]) -> None:
    """
    Logs a structured event to the logger.
    """
    event = {
        "event": event_name,
        "timestamp": datetime.now().isoformat(),
        **details
    }
    logger.info(event)

def flush_yaml_logs() -> None:
    """
    Writes the accumulated preprocess logs to artifacts/preprocess.yaml.
    """
    artifacts_path = Path(ARTIFACTS_DIR)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    
    output_file = artifacts_path / "preprocess.yaml"
    
    with open(output_file, "w") as f:
        yaml.dump(_preprocess_logs, f, default_flow_style=False, sort_keys=False)

def save_analysis_results(results: Dict[str, Any]) -> None:
    """
    Updates the global analysis results and writes to artifacts/analysis_results.json.
    This function is typically called by the analysis module to finalize results.
    """
    global _analysis_results
    _analysis_results.update(results)
    
    artifacts_path = Path(ARTIFACTS_DIR)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    
    output_file = artifacts_path / "analysis_results.json"
    
    with open(output_file, "w") as f:
        json.dump(_analysis_results, f, indent=2, default=str)

def get_analysis_results() -> Dict[str, Any]:
    """Returns the current state of analysis results."""
    return _analysis_results

def initialize_logging() -> None:
    """
    Initializes the logging infrastructure.
    Clears previous logs if re-running in the same session.
    """
    global _preprocess_logs, _analysis_results
    _preprocess_logs = []
    _analysis_results = {}
    
    # Ensure artifacts directory exists
    Path(ARTIFACTS_DIR).mkdir(parents=True, exist_ok=True)

# Initialize immediately on import to ensure state is clean for the task run
initialize_logging()
