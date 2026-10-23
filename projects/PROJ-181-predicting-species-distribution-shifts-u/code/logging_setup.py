"""
Logging setup helper for the project.

Reads the YAML configuration from ``logs/logging_config.yaml`` and configures
the root logger.  If a ``log_file`` is supplied, a ``FileHandler`` is attached
that writes to that file; otherwise a default log file named after the executing
script (e.g. ``main.log``) is created inside the ``logs`` directory.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

import yaml
from llmxive_toolkit import paths

def _load_config() -> dict:
    """Load the YAML logging configuration."""
    config_path = Path.cwd() / "logs" / "logging_config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Logging configuration not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def initialize_logging(log_file: Optional[Path] = None) -> None:
    """
    Initialise the project‑wide logging configuration.

    Parameters
    ----------
    log_file : Optional[Path]
        Path to the log file. If ``None`` a default file named
        ``<script>.log`` inside the ``logs`` folder is used.
    """
    cfg = _load_config()
    fmt = cfg.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    level_name = cfg.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Determine log file path
    if log_file is None:
        # Derive from the invoking script name (e.g. main.py -> main.log)
        script_name = Path(sys.argv[0]).stem
        log_file = paths.logs(f"{script_name}.log")
    else:
        log_file = Path(log_file)

    # Ensure the logs directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Reset any existing handlers to avoid duplicate logs
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

    root_logger.setLevel(level)

    formatter = logging.Formatter(fmt)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Optional console output for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)