"""Simple setup for standard logging."""
import logging
import sys

def setup_logging(log_level: int = logging.INFO, log_file: str = None) -> None:
    """Configure logging to console and optionally file."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )
