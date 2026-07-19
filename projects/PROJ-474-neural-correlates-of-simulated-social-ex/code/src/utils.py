import logging
import sys
import os
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

def log_exception(logger: Optional[logging.Logger] = None, exc: Optional[Exception] = None) -> None:
    """
    Log an exception.
    Accepts flexible arguments to match all call sites:
    - log_exception(logger)
    - log_exception(logger, exc)
    - log_exception(exc=exc)
    - log_exception()
    """
    if logger is None:
        try:
            logger = logging.getLogger()
        except:
            return

    if exc is None:
        # Check if exc was passed as a keyword argument only
        # Since we can't inspect kwargs in this signature easily without *args, we rely on the caller
        # If called as log_exception(exc=some_exc), exc is populated.
        # If called as log_exception(logger), exc is None.
        # If called as log_exception(), both are None.
        # If called as log_exception(logger, exc), both are populated.
        # If called as log_exception(exc=exc), exc is populated.
        # If called as log_exception(logger=logger), exc is None.
        # We need to handle the case where the caller passed logger as a keyword arg too.
        # The signature above handles the most common positional cases.
        # If the caller does log_exception(logger), exc is None.
        # If the caller does log_exception(exc=exc), exc is populated.
        # If the caller does log_exception(), exc is None.
        # If the caller does log_exception(logger, exc), exc is populated.
        
        # If no exception is provided, we try to get the current one from sys.exc_info()
        # This handles cases where the function is called inside an except block without passing the exception explicitly
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            exc = exc_info[1]
        else:
            # If still no exception and no logger, just return
            if logger is None:
                return
            logger.warning("log_exception called without an exception or exc_info available.")
            return

    if exc is not None:
        logger.error(f"Exception occurred: {exc}")
        logger.error(traceback.format_exc())
    else:
        logger.error("log_exception called but no exception found.")
