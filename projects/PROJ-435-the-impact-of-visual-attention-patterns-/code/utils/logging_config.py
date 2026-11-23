import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assumes code/ is at root or one level down
    current = Path(__file__).resolve()
    if current.name == 'logging_config.py':
        return current.parent.parent
    return current.parent.parent.parent

def setup_logging() -> None:
    """
    Configure the root logger and create specialized handlers for:
    - General pipeline progress
    - Data quality warnings
    - Exclusion counts
    
    This function reads configuration from `code/config.yaml` if present,
    otherwise uses sensible defaults.
    """
    root = get_project_root()
    config_path = root / 'code' / 'config.yaml'
    
    log_dir = root / 'output'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Default configuration
    log_config = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'pipeline': {
                'file': str(log_dir / 'pipeline.log'),
                'level': logging.INFO
            },
            'quality': {
                'file': str(log_dir / 'data_quality.log'),
                'level': logging.WARNING
            },
            'exclusion': {
                'file': str(log_dir / 'exclusions.log'),
                'level': logging.INFO
            }
        }
    }
    
    # Try to load custom config
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            if user_config and 'logging' in user_config:
                # Merge user config with defaults
                log_config.update(user_config['logging'])
        except Exception as e:
            print(f"Warning: Could not load logging config from {config_path}: {e}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config.get('level', logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Create and configure handlers
    handlers = log_config.get('handlers', {})
    
    if 'pipeline' in handlers:
        p_handler = logging.FileHandler(handlers['pipeline']['file'])
        p_handler.setLevel(handlers['pipeline'].get('level', logging.INFO))
        p_handler.setFormatter(formatter)
        root_logger.addHandler(p_handler)
        
        # Also add to stdout for visibility
        p_stdout = logging.StreamHandler(sys.stdout)
        p_stdout.setLevel(handlers['pipeline'].get('level', logging.INFO))
        p_stdout.setFormatter(formatter)
        root_logger.addHandler(p_stdout)
    
    if 'quality' in handlers:
        q_handler = logging.FileHandler(handlers['quality']['file'])
        q_handler.setLevel(handlers['quality'].get('level', logging.WARNING))
        q_handler.setFormatter(formatter)
        root_logger.addHandler(q_handler)
    
    if 'exclusion' in handlers:
        e_handler = logging.FileHandler(handlers['exclusion']['file'])
        e_handler.setLevel(handlers['exclusion'].get('level', logging.INFO))
        e_handler.setFormatter(formatter)
        root_logger.addHandler(e_handler)

def get_pipeline_logger() -> logging.Logger:
    """Get the logger for general pipeline progress."""
    logger = logging.getLogger('pipeline')
    if not logger.handlers:
        # Ensure logging is set up
        setup_logging()
    return logger

def get_quality_logger() -> logging.Logger:
    """Get the logger for data quality warnings."""
    logger = logging.getLogger('quality')
    if not logger.handlers:
        setup_logging()
    return logger

def get_exclusion_logger() -> logging.Logger:
    """Get the logger for exclusion events and counts."""
    logger = logging.getLogger('exclusion')
    if not logger.handlers:
        setup_logging()
    return logger

def log_data_quality_warning(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a data quality warning.
    
    Args:
        message: The warning message
        details: Optional dictionary with additional context (e.g., participant_id, reason)
    """
    logger = get_quality_logger()
    if details:
        logger.warning(f"{message} | Details: {json.dumps(details)}")
    else:
        logger.warning(message)

def log_exclusion(participant_id: Optional[str] = None, 
                 headline_id: Optional[str] = None, 
                 reason: str = "", 
                 data_loss_percent: Optional[float] = None) -> None:
    """
    Log an exclusion event with structured details.
    
    Args:
        participant_id: ID of the excluded participant
        headline_id: ID of the excluded headline (if applicable)
        reason: Reason for exclusion
        data_loss_percent: Percentage of data lost (if applicable)
    """
    logger = get_exclusion_logger()
    exclusion_data = {
        'participant_id': participant_id,
        'headline_id': headline_id,
        'reason': reason,
        'data_loss_percent': data_loss_percent
    }
    # Filter out None values
    exclusion_data = {k: v for k, v in exclusion_data.items() if v is not None}
    logger.info(f"EXCLUSION: {json.dumps(exclusion_data)}")

def log_pipeline_progress(step: str, status: str, details: Optional[str] = None) -> None:
    """
    Log pipeline execution progress.
    
    Args:
        step: The current step name
        status: Status (e.g., 'STARTED', 'COMPLETED', 'FAILED')
        details: Optional additional details
    """
    logger = get_pipeline_logger()
    msg = f"PIPELINE: {step} - {status}"
    if details:
        msg += f" | {details}"
    logger.info(msg)

def load_logging_config() -> Dict[str, Any]:
    """Load and return the current logging configuration."""
    root = get_project_root()
    config_path = root / 'code' / 'config.yaml'
    
    default_config = {
        'level': 'INFO',
        'handlers': ['pipeline', 'quality', 'exclusion']
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if config and 'logging' in config:
                return config['logging']
        except Exception:
            pass
    
    return default_config

def main():
    """Demonstrate logging setup and functionality."""
    setup_logging()
    
    # Test pipeline logger
    pipeline_logger = get_pipeline_logger()
    pipeline_logger.info("Pipeline initialization started")
    log_pipeline_progress("Data Loading", "STARTED")
    log_pipeline_progress("Data Loading", "COMPLETED", "Loaded 1000 records")
    
    # Test quality logger
    quality_logger = get_quality_logger()
    log_data_quality_warning("Missing values detected in fixation_duration", 
                           {'count': 5, 'column': 'fixation_duration'})
    
    # Test exclusion logger
    exclusion_logger = get_exclusion_logger()
    log_exclusion(participant_id="P001", reason="High data loss", data_loss_percent=25.5)
    log_exclusion(participant_id="P002", reason="Missing ROI data")
    
    print("Logging configuration test completed. Check output/ directory for log files.")

if __name__ == "__main__":
    main()
