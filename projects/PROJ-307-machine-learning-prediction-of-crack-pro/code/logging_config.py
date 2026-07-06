"""
Logging configuration module.
"""
import logging
import sys
from pathlib import Path
from code.config import ensure_dirs

def setup_logging(log_file: str = "app.log") -> None:
    """Configure root logger."""
    ensure_dirs()
    log_path = Path("logs") / log_file
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
