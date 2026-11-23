import logging
from pathlib import Path
from typing import Optional
from llmxive_toolkit import paths

def _ensure_log_directory(log_dir: Path) -> Path:
    """
    Ensure that the log directory exists.
    
    Parameters
    ----------
    log_dir : Path
        Desired directory for log files.
        
    Returns
    -------
    Path
        The now existing directory.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def initialize_logging(log_file: Optional[Path] = None) -> None:
    """
    Initialise the project-wide logging configuration.
    
    Configures the root logger with the required format:
    %(asctime)s - %(name)s - %(levelname)s - %(message)s
    
    Args:
        log_file: Optional path to the log file. If None, defaults to logs/pipeline.log.
    """
    # Use toolkit to ensure logs directory exists
    log_dir = paths.path("logs")
    _ensure_log_directory(log_dir)
    
    if log_file is None:
        log_file = log_dir / "pipeline.log"
    
    # Required format per T003
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Clear existing handlers to avoid duplicate logs in interactive environments
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
