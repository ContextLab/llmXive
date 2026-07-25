import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Constants for log levels and formats
DEFAULT_LOG_LEVEL = logging.INFO
DATA_QUALITY_LEVEL = logging.WARNING
EXCLUSION_LEVEL = logging.INFO
PIPELINE_LEVEL = logging.INFO

# Custom log levels if needed
if not hasattr(logging, 'DATA_QUALITY'):
    logging.DATA_QUALITY = 35
    logging.addLevelName(logging.DATA_QUALITY, "DATA_QUALITY")

if not hasattr(logging, 'EXCLUSION'):
    logging.EXCLUSION = 25
    logging.addLevelName(logging.EXCLUSION, "EXCLUSION")

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_initialized = False

def _ensure_initialized(project_root: Optional[Path] = None) -> None:
    """Initialize logging infrastructure if not already done."""
    global _initialized
    if _initialized:
        return

    if project_root is None:
        project_root = Path(__file__).parent.parent.parent

    log_dir = project_root / "state" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler for general output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    _initialized = True

def setup_logging(project_root: Optional[Path] = None) -> None:
    """
    Configure the logging infrastructure for the pipeline.
    
    Args:
        project_root: Root directory of the project. Defaults to parent of this file's parent.
    """
    _ensure_initialized(project_root)

def get_quality_logger() -> logging.Logger:
    """
    Get the logger for data quality warnings.
    
    Returns:
        Logger instance configured for data quality messages.
    """
    logger_name = "data_quality"
    if logger_name in _loggers:
        return _loggers[logger_name]

    _ensure_initialized()
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / "state" / "logs"
    log_file = log_dir / "data_quality.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.WARNING)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        # Also add a console handler for immediate visibility
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)

    _loggers[logger_name] = logger
    return logger

def get_exclusion_logger() -> logging.Logger:
    """
    Get the logger for participant/trial exclusion events.
    
    Returns:
        Logger instance configured for exclusion messages.
    """
    logger_name = "exclusions"
    if logger_name in _loggers:
        return _loggers[logger_name]

    _ensure_initialized()
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / "state" / "logs"
    log_file = log_dir / "exclusions.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)

    _loggers[logger_name] = logger
    return logger

def get_pipeline_logger() -> logging.Logger:
    """
    Get the logger for general pipeline progress.
    
    Returns:
        Logger instance configured for pipeline messages.
    """
    logger_name = "pipeline"
    if logger_name in _loggers:
        return _loggers[logger_name]

    _ensure_initialized()
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / "state" / "logs"
    log_file = log_dir / "pipeline.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(file_format)
        logger.addHandler(console_handler)

    _loggers[logger_name] = logger
    return logger

def log_data_quality_warning(message: str, participant_id: Optional[str] = None, 
                             headline_id: Optional[str] = None, details: Optional[Dict] = None) -> None:
    """
    Log a data quality warning.
    
    Args:
        message: Description of the quality issue.
        participant_id: Optional ID of the affected participant.
        headline_id: Optional ID of the affected headline.
        details: Optional dictionary of additional context.
    """
    logger = get_quality_logger()
    if participant_id or headline_id:
        context = f" [participant={participant_id}, headline={headline_id}]"
        if details:
            context += f" | {details}"
        logger.warning(f"{message}{context}")
    else:
        logger.warning(message)

def log_exclusion(reason: str, participant_id: Optional[str] = None, 
                  trial_id: Optional[str] = None, count: int = 1) -> None:
    """
    Log an exclusion event.
    
    Args:
        reason: Reason for exclusion.
        participant_id: ID of the excluded participant.
        trial_id: ID of the excluded trial.
        count: Number of items excluded (default 1).
    """
    logger = get_exclusion_logger()
    if participant_id:
        logger.info(f"Excluded participant {participant_id}: {reason}")
    elif trial_id:
        logger.info(f"Excluded trial {trial_id}: {reason}")
    else:
        logger.info(f"Excluded {count} items: {reason}")

def log_pipeline_progress(step: str, message: str, details: Optional[Dict] = None) -> None:
    """
    Log a pipeline progress message.
    
    Args:
        step: Current pipeline step name.
        message: Progress description.
        details: Optional dictionary of metrics or stats.
    """
    logger = get_pipeline_logger()
    if details:
        detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
        logger.info(f"[{step}] {message} | {detail_str}")
    else:
        logger.info(f"[{step}] {message}")

def log_pipeline_error(step: str, error_message: str, exception: Optional[Exception] = None) -> None:
    """
    Log a pipeline error.
    
    Args:
        step: Pipeline step where error occurred.
        error_message: Description of the error.
        exception: Optional exception instance for traceback.
    """
    logger = get_pipeline_logger()
    logger.error(f"[{step}] ERROR: {error_message}", exc_info=exception)

def load_logging_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load logging configuration from a YAML file.
    
    Args:
        config_path: Path to the logging config file. Defaults to code/config.yaml.
        
    Returns:
        Dictionary containing logging configuration.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        return {}
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    return config.get('logging', {})

def main() -> None:
    """
    Main function to demonstrate logging infrastructure setup.
    """
    setup_logging()
    
    # Demonstrate logging functions
    quality_logger = get_quality_logger()
    exclusion_logger = get_exclusion_logger()
    pipeline_logger = get_pipeline_logger()
    
    pipeline_logger.info("Pipeline started")
    log_pipeline_progress("data_loading", "Loading raw data", {"rows": 1000})
    
    log_data_quality_warning("Missing gaze coordinates", participant_id="P001")
    log_exclusion("High data loss (>20%)", participant_id="P002", count=1)
    
    pipeline_logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
