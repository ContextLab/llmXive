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

if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging module initialized")
