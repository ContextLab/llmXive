"""
Logging configuration and utilities for the eye-tracking pipeline.

This module sets up multiple loggers for different purposes:
- Pipeline logger: General progress and status
- Quality logger: Data quality warnings
- Exclusion logger: Participant/trial exclusions
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def setup_logging(log_dir: Optional[Path] = None) -> None:
    """
    Setup logging infrastructure.
    
    Args:
        log_dir: Directory for log files. Defaults to project root.
    """
    if log_dir is None:
        log_dir = get_project_root() / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handlers
    pipeline_log = log_dir / "pipeline.log"
    quality_log = log_dir / "quality.log"
    exclusion_log = log_dir / "exclusions.log"
    
    pipeline_handler = logging.FileHandler(pipeline_log)
    pipeline_handler.setFormatter(detailed_formatter)
    pipeline_handler.setLevel(logging.DEBUG)
    
    quality_handler = logging.FileHandler(quality_log)
    quality_handler.setFormatter(detailed_formatter)
    quality_handler.setLevel(logging.WARNING)
    
    exclusion_handler = logging.FileHandler(exclusion_log)
    exclusion_handler.setFormatter(detailed_formatter)
    exclusion_handler.setLevel(logging.INFO)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(pipeline_handler)
    root_logger.addHandler(quality_handler)
    root_logger.addHandler(exclusion_handler)

def get_pipeline_logger() -> logging.Logger:
    """Get the pipeline logger."""
    return logging.getLogger("pipeline")

def get_quality_logger() -> logging.Logger:
    """Get the data quality logger."""
    return logging.getLogger("quality")

def get_exclusion_logger() -> logging.Logger:
    """Get the exclusion logger."""
    return logging.getLogger("exclusions")

def log_data_quality_warning(logger: logging.Logger, message: str) -> None:
    """Log a data quality warning."""
    logger.warning(f"[DATA QUALITY] {message}")

def log_exclusion(logger: logging.Logger, participant_id: int, reason: str) -> None:
    """Log a participant/trial exclusion."""
    logger.info(f"[EXCLUSION] Participant {participant_id}: {reason}")

def log_pipeline_progress(logger: logging.Logger, message: str) -> None:
    """Log pipeline progress."""
    logger.info(f"[PROGRESS] {message}")

def load_logging_config(config_path: Path) -> Dict[str, Any]:
    """
    Load logging configuration from YAML file.
    
    Args:
        config_path: Path to config file.
        
    Returns:
        Configuration dictionary.
    """
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}

def main():
    """Test logging setup."""
    setup_logging()
    
    pipeline_logger = get_pipeline_logger()
    quality_logger = get_quality_logger()
    exclusion_logger = get_exclusion_logger()
    
    pipeline_logger.info("Pipeline initialized")
    quality_logger.warning("Data quality check: some warnings")
    exclusion_logger.info("Excluding participant 123")

if __name__ == "__main__":
    main()
