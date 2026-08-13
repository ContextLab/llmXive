import logging
import sys
from typing import Optional

def handle_fatal_error(error: Exception, logger: Optional[logging.Logger] = None) -> None:
    """
    Handle a fatal error by logging it and exiting.
    
    This ensures we fail loudly and do not silently continue with bad state.
    """
    if logger is None:
        logger = logging.getLogger("error_handling")
    
    logger.critical(f"FATAL ERROR: {type(error).__name__}: {str(error)}")
    logger.critical("Pipeline aborted due to critical failure.")
    sys.exit(1)

def log_skipped_sample(sample_id: str, reason: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a skipped sample with a specific reason."""
    if logger is None:
        logger = logging.getLogger("error_handling")
    logger.warning(f"Skipped sample {sample_id}: {reason}")