import logging
import sys
from pathlib import Path

def setup_logging(level=logging.INFO):
    """Configure the logging system."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name):
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def warning_handler(message):
    """Handle warning messages by logging them."""
    logger = get_logger(__name__)
    logger.warning(message)

def log_warning(message: str, filename: str, error: str) -> None:
    """
    Log a warning message to stderr with a specific format.
    
    This function implements the exact interface required for T006.
    It logs to stderr with the format: WARNING [filename]: {error}
    
    Args:
        message: The original warning message (for context/logging).
        filename: The name of the file where the warning occurred.
        error: The specific error description to append.
    
    Note:
        This task is a stub/interface definition only. It does not implement
        the skip/continue logic (FR-007), which is handled in T016.
        The functional behavior of skipping malformed files and continuing
        the pipeline is implemented in T016 (ast_parser.py).
    """
    # Format the message exactly as specified: WARNING [filename]: {error}
    formatted_message = f"WARNING [{filename}]: {error}"
    
    # Log to stderr explicitly as per requirement
    print(formatted_message, file=sys.stderr)
    
    # Also log via the standard logger for consistency with other logging
    logger = get_logger(__name__)
    logger.warning(formatted_message)

if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging module initialized")
    
    # Test the log_warning function
    log_warning("Test message", "test_file.py", "Test error occurred")