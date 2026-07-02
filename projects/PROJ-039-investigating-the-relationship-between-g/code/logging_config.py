import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
import yaml

# Ensure artifacts directory exists
ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

PREPROCESS_LOG_PATH = ARTIFACTS_DIR / "preprocess.yaml"
ANALYSIS_RESULTS_PATH = ARTIFACTS_DIR / "analysis_results.json"

class YAMLLogHandler(logging.Handler):
    """Custom logging handler that accumulates structured log events into a YAML file."""
    
    def __init__(self, log_path: Path):
        super().__init__()
        self.log_path = log_path
        self.events = []
        
        # Initialize file if it doesn't exist
        if not self.log_path.exists():
            with open(self.log_path, 'w') as f:
                yaml.dump({"logs": []}, f)

    def emit(self, record: logging.LogRecord):
        try:
            event = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add extra fields if present
            if hasattr(record, 'event_data'):
                event.update(record.event_data)
            
            self.events.append(event)
            
            # Also write immediately to file for persistence
            self._write_event(event)
            
        except Exception:
            self.handleError(record)

    def _write_event(self, event: Dict[str, Any]):
        """Append a single event to the YAML file."""
        try:
            # Read existing content
            existing = {"logs": []}
            if self.log_path.exists():
                try:
                    with open(self.log_path, 'r') as f:
                        content = yaml.safe_load(f)
                        if content and 'logs' in content:
                            existing['logs'] = content['logs']
                except (yaml.YAMLError, IOError):
                    pass
            
            # Append new event
            existing['logs'].append(event)
            
            # Write back
            with open(self.log_path, 'w') as f:
                yaml.dump(existing, f, default_flow_style=False, sort_keys=False)
                
        except Exception as e:
            logging.error(f"Failed to write log event to {self.log_path}: {e}")

    def flush(self):
        """Flush any buffered events."""
        pass

class StructuredFormatter(logging.Formatter):
    """Formatter that creates structured log records with extra data support."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Standard formatting for console output
        return super().format(record)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a configured logger with both console and YAML file handlers.
    
    Args:
        name: Logger name, defaults to "llmXive"
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = StructuredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # YAML file handler for structured logs
    yaml_handler = YAMLLogHandler(PREPROCESS_LOG_PATH)
    yaml_handler.setLevel(logging.INFO)
    yaml_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(yaml_handler)
    
    return logger

def log_structured_event(
    logger: logging.Logger, 
    level: str, 
    message: str, 
    **kwargs
) -> None:
    """
    Log a structured event with additional data fields.
    
    Args:
        logger: Logger instance to use
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        **kwargs: Additional structured data to include
    """
    record = logger.makeRecord(
        logger.name, 
        getattr(logging, level.upper()), 
        "", 
        0, 
        message, 
        (), 
        None
    )
    record.event_data = kwargs
    logger.handle(record)

def flush_yaml_logs() -> None:
    """Explicitly flush all YAML log handlers."""
    for handler in logging.root.handlers:
        if isinstance(handler, YAMLLogHandler):
            handler.flush()

def save_analysis_results(results: Dict[str, Any]) -> None:
    """
    Save analysis results to the canonical JSON file.
    
    Args:
        results: Dictionary of analysis results to save
    """
    try:
        # Ensure directory exists
        ANALYSIS_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "project": "llmXive-gut-microbiome-eeg",
            "results": results
        }
        
        with open(ANALYSIS_RESULTS_PATH, 'w') as f:
            json.dump(output, f, indent=2, default=str)
            
        # Also log the save event
        logger = get_logger()
        log_structured_event(
            logger, 
            "INFO", 
            f"Analysis results saved to {ANALYSIS_RESULTS_PATH}",
            file=str(ANALYSIS_RESULTS_PATH),
            keys=list(results.keys())
        )
        
    except Exception as e:
        logger = get_logger()
        log_structured_event(
            logger, 
            "ERROR", 
            f"Failed to save analysis results: {e}",
            error=str(e)
        )
        raise

# Convenience function to get the preprocess logger
def get_preprocess_logger() -> logging.Logger:
    """Get logger configured for preprocessing tasks."""
    return get_logger("preprocess")

# Convenience function to get the analysis logger
def get_analysis_logger() -> logging.Logger:
    """Get logger configured for analysis tasks."""
    return get_logger("analysis")
