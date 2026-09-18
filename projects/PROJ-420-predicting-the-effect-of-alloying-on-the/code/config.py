"""Environment configuration management."""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from logging_config import get_logger


class Config:
    """Configuration container with tolerant attribute access."""

    def __init__(self, data_dir: str = "data", models_dir: str = "models",
                 results_dir: str = "results", random_seed: int = 42):
        self.data_dir = data_dir
        self.data_raw = os.path.join(data_dir, "raw")
        self.data_processed = os.path.join(data_dir, "processed")
        self.data_logs = os.path.join(data_dir, "logs")
        self.models_dir = models_dir
        self.results_dir = results_dir
        self.random_seed = random_seed
        self.VALID_MEASUREMENT_METHODS = [
            r"(?i)ultrasonic",
            r"(?i)direct",
            r"(?i)resonant",
            r"(?i)impulse"
        ]
        self.logger = get_logger("config")

    # Tolerant attribute access for unknown methods
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


_CONFIG: Optional[Config] = None


def get_config() -> Config:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG


def main():
    """Entry point for config module."""
    logger = get_logger("config_main")
    logger.info("Config module loaded")
    cfg = get_config()
    logger.info(f"Data dir: {cfg.data_dir}")
    logger.info(f"Processed dir: {cfg.data_processed}")


if __name__ == "__main__":
    main()
