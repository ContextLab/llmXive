"""
llmXive project code package.
Initializes logging infrastructure for the microglial morphology analysis pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Import project root configuration to determine log file paths
from .config import get_project_root

# Define the package logger name
_LOGGER_NAME = "llmXive_microglia"
_LOGGER: Optional[logging.Logger] = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a logger for the project.
    
    Args:
        name: Optional sub-name for the logger (e.g., 'data_ingestion'). 
              If None, returns the root project logger.
              
    Returns:
        A configured logging.Logger instance.
    """
    global _LOGGER
    
    if _LOGGER is None:
        _LOGGER = logging.getLogger(_LOGGER_NAME)
        if _LOGGER.handlers:
            return _LOGGER
        
        _LOGGER.setLevel(logging.INFO)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        _LOGGER.addHandler(console_handler)
        
        # File handler for persistent logs in reports/
        project_root = get_project_root()
        log_file_path = project_root / "reports" / "pipeline.log"
        
        # Ensure reports directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        _LOGGER.addHandler(file_handler)
    
    if name:
        return _LOGGER.getChild(name)
    return _LOGGER

def warn_missing_metadata(field_name: str, record_id: str, logger_name: Optional[str] = None) -> None:
    """
    Log a warning for missing metadata fields as required by FR-001 and FR-008.
    
    This function ensures consistent warning formatting across the pipeline
    when subjects or images are excluded due to missing data.
    
    Args:
        field_name: The name of the missing metadata field (e.g., 'brain_region', 'cognitive_score').
        record_id: The identifier of the record missing the field.
        logger_name: Optional specific logger name. Defaults to the root project logger.
    """
    logger = get_logger(logger_name)
    logger.warning(
        f"Missing metadata '{field_name}' for record '{record_id}'. "
        f"Excluding from analysis per FR-001/FR-008."
    )

def setup_file_logging(log_path: Optional[Path] = None, level: int = logging.DEBUG) -> None:
    """
    Explicitly set up file logging if the default initialization needs customization.
    
    Args:
        log_path: Path to the log file. If None, defaults to reports/pipeline.log.
        level: Logging level for the file handler.
    """
    global _LOGGER
    if _LOGGER is None:
        get_logger() # Initialize defaults first
    
    if log_path is None:
        project_root = get_project_root()
        log_path = project_root / "reports" / "pipeline.log"
    
    # Check if handler already exists for this specific file to avoid duplicates
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_path) for h in _LOGGER.handlers):
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        _LOGGER.addHandler(file_handler)

# Export public API
__all__ = [
    "get_logger",
    "warn_missing_metadata",
    "setup_file_logging",
    "logging"
]