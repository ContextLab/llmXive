import logging
import os
from pathlib import Path
from typing import Optional

from config import load_paths


def setup_logging(paths: Optional[dict] = None) -> None:
    """Setup logging configuration."""
    if paths is None:
        paths = load_paths()

    log_dir = paths.get("data_logs", paths["base"] / "data" / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
