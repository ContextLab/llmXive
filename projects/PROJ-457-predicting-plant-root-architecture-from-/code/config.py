import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Canonical default configuration. Every key any pipeline script may
# request is present here, so ``config["KEY"]`` never raises KeyError
# even when ``config.yaml`` is missing or partial.
DEFAULT_CONFIG: Dict[str, Any] = {
    "DATA_PATH": "data",
    "RAW_DATA_PATH": "data/raw",
    "PROCESSED_PATH": "data/processed",
    "ARTIFACTS_PATH": "artifacts",
    "LOGS_PATH": "artifacts/logs",
    "LOG_PATH": "artifacts/logs/pipeline.log",
    "LOG_LEVEL": "INFO",
    "MODEL_PATH": "artifacts/models",
    "PLOTS_PATH": "artifacts/reports/plots",
    "REPORTS_PATH": "artifacts/reports",
    "SEED": 42,
}


def get_config() -> Dict[str, Any]:
    """
    Loads configuration from config.yaml (project root), merged over
    DEFAULT_CONFIG so that all standard keys are always present.
    """
    config: Dict[str, Any] = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            loaded = yaml.safe_load(f)
        if isinstance(loaded, dict):
            config.update(loaded)
    return config


def _resolve(path_str: str) -> Path:
    """Resolve a possibly-relative path against the project root."""
    p = Path(path_str)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures logging to file and console.

    Reads LOG_LEVEL and LOG_PATH from config.yaml if available.
    Creates the log directory (artifacts/logs/) if it does not exist.
    """
    try:
        config = get_config()
        cfg_level = config.get("LOG_LEVEL", log_level)
        cfg_log_path = config.get("LOG_PATH", DEFAULT_CONFIG["LOG_PATH"])
    except Exception:
        cfg_level = log_level
        cfg_log_path = DEFAULT_CONFIG["LOG_PATH"]

    level = getattr(logging, str(cfg_level).upper(), logging.INFO)

    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers to prevent duplicates on re-calls
    logger.handlers = []

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (always under artifacts/logs/ by default)
    log_file = _resolve(str(cfg_log_path))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.debug("Logging initialised; log file: %s", log_file)
    return logger
