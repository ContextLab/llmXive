"""
llmXive BES Pipeline Package.

This package contains the modules for the Bidirectional Evolutionary Search
pipeline for self-improving language models.
"""
import logging
import sys
from pathlib import Path
import json
from datetime import datetime

# Ensure logging is configured
def setup_package_logging(log_file: str = "data/processed/experiment.log"):
    """
    Configure logging for the package to write JSON entries to a file.
    
    Args:
        log_file: Path to the log file.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a custom JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            # Add extra fields if present
            if hasattr(record, 'cpu_percent'):
                log_entry["cpu_percent"] = record.cpu_percent
            if hasattr(record, 'wall_clock_time'):
                log_entry["wall_clock_time"] = record.wall_clock_time
            
            return json.dumps(log_entry)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)

# Initialize logging on package import
setup_package_logging()

__version__ = "0.1.0"
__author__ = "llmXive Team"
