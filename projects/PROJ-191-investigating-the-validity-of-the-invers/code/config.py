import logging
import os
import sys
from pathlib import Path
from typing import Optional

class ProjectConfig:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.data_results = self.root / "data" / "results"
        self.code_dir = self.root / "code"
        
        # Ensure directories exist
        for d in [self.data_raw, self.data_processed, self.data_results]:
            d.mkdir(parents=True, exist_ok=True)

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the project.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    """
    return logging.getLogger(name)
