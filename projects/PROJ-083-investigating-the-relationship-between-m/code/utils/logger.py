import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Union

class LoggerConfig:
    def __init__(self, name: str, level: int = logging.INFO, log_file: Optional[Path] = None):
        self.name = name
        self.level = level
        self.log_file = log_file
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._setup_handlers()

    def _setup_handlers(self):
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

def setup_logger(name: str, log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file output.
    """
    if isinstance(log_file, str):
        log_file = Path(log_file)
    
    config = LoggerConfig(name, level, log_file)
    return config.logger

def handle_exception(logger: logging.Logger, exc: Exception, msg: str = "An error occurred"):
    """
    Logs an exception with full traceback.
    """
    logger.error(f"{msg}: {exc}")
    logger.error(traceback.format_exc())

def log_critical_failure(logger: logging.Logger, error_code: str, details: str):
    """
    Logs a critical failure and prepares the system for halting.
    This function does not exit the process itself to allow the caller to decide the exit code,
    but it logs the critical event.
    """
    logger.critical(f"CRITICAL FAILURE [{error_code}]: {details}")
    logger.critical("Pipeline halted due to critical error.")