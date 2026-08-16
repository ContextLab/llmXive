import logging
import sys
import json
from typing import Optional
from pathlib import Path
from datetime import datetime
import os

# Ensure data directory exists before logging
DATA_DIR = Path("data")
AUDIT_LOG_PATH = DATA_DIR / "audit_log.json"

# Ensure data directory structure exists
def _ensure_data_dirs():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Create subdirectories if they don't exist
    (DATA_DIR / "raw").mkdir(exist_ok=True)
    (DATA_DIR / "processed").mkdir(exist_ok=True)
    (DATA_DIR / "contracts").mkdir(exist_ok=True)

# Initialize logger
def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a logger that outputs to both console and the audit log file.
    """
    _ensure_data_dirs()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler for audit log
        file_handler = logging.FileHandler(AUDIT_LOG_PATH)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger

logger = get_logger()

class DataAvailabilityError(Exception):
    """Raised when required data is missing or incomplete."""
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"DataAvailabilityError: {message}")

class VoronoiFailure(Exception):
    """Raised when Voronoi tessellation fails."""
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"VoronoiFailure: {message}")

def log_audit_event(event_type: str, details: dict) -> None:
    """
    Logs an audit event to both the console and the JSON audit log file.
    
    Args:
        event_type: Type of event (e.g., 'DATA_INGESTION_START', 'GRAPH_CONSTRUCTION_COMPLETE')
        details: Dictionary containing event-specific details
    """
    _ensure_data_dirs()
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "details": details
    }
    
    # Log to console via logger
    logger.info(f"AUDIT: {event_type} - {json.dumps(details)}")
    
    # Append to JSON audit log file
    try:
        if AUDIT_LOG_PATH.exists():
            with open(AUDIT_LOG_PATH, 'r') as f:
                try:
                    audit_data = json.load(f)
                except json.JSONDecodeError:
                    audit_data = []
        else:
            audit_data = []
        
        audit_data.append(log_entry)
        
        with open(AUDIT_LOG_PATH, 'w') as f:
            json.dump(audit_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        raise