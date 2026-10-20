"""
Small helper to configure a project‑wide logger that writes to a file inside the ``logs`` directory.
"""
import logging
from pathlib import Path

def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Configure a root logger that writes INFO‑level messages to ``log_dir / pipeline.log``.
    Returns the logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    logger = logging.getLogger("molecular_properties")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if this function is called repeatedly
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh = logging.FileHandler(log_file, mode="a")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger that inherits the configuration from ``setup_logging``.
    """
    return logging.getLogger(f"molecular_properties.{name}")