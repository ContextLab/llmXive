import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.utils.config import get_data_path, get_config

# Global logger registry to ensure single instance per component
_loggers: Dict[str, logging.Logger] = {}
_log_levels: Dict[str, int] = {}

class PipelineLogger:
    """
    A wrapper around Python's logging.Logger to enforce project-specific
    logging standards, including automatic provenance context injection.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Ensure handlers are not duplicated if logger is re-acquired
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.logger.propagate = False

    def _setup_handlers(self) -> None:
        """Configure console and file handlers."""
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(console_formatter)
        self.logger.addHandler(ch)

        # File handler (logs to data/processed/logs/)
        log_dir = get_data_path() / "processed" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{run_id}.log"
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        fh.setFormatter(file_formatter)
        self.logger.addHandler(fh)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self.logger.exception(msg, *args, **kwargs)

    def set_level(self, level: int) -> None:
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

def setup_logging() -> PipelineLogger:
    """
    Initialize the main pipeline logger and return the instance.
    This function ensures logging is configured once at pipeline start.
    """
    if "pipeline_main" not in _loggers:
        _loggers["pipeline_main"] = PipelineLogger("pipeline_main")
        # Also configure root logger to avoid duplicate console output from third-party libs
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.WARNING)
            root_logger.addHandler(ch)
    return _loggers["pipeline_main"]

def set_log_level(level: int) -> None:
    """
    Set the log level for all registered loggers.
    """
    for logger in _loggers.values():
        logger.set_level(level)
    # Also update root
    logging.getLogger().setLevel(level)

def get_logger(name: Optional[str] = None) -> PipelineLogger:
    """
    Retrieve or create a named logger instance.
    If name is None, returns the main pipeline logger.
    """
    if name is None:
        return setup_logging()
    
    if name not in _loggers:
        _loggers[name] = PipelineLogger(name)
    
    return _loggers[name]
