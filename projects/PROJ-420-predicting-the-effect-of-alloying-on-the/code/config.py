"""Environment configuration management."""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from logging_config import get_logger

# ----------------------------------------------------------------------
# Module‑level constants expected by downstream code and tests
# ----------------------------------------------------------------------
# Root directories – exposed as pathlib.Path objects for easy joining.
DATA_ROOT: Path = Path("data")
MODEL_ROOT: Path = Path("models")
RESULT_ROOT: Path = Path("results")

# Global random seed used for reproducibility across the pipeline.
RANDOM_SEED: int = 42

# Accepted measurement method regexes (case‑insensitive).
VALID_MEASUREMENT_METHODS = [
    r"(?i)ultrasonic",
    r"(?i)direct",
    r"(?i)resonant",
    r"(?i)impulse",
]

# ----------------------------------------------------------------------
# Config container – retains backward‑compatible attribute names.
# ----------------------------------------------------------------------
class Config:
    """Configuration container with tolerant attribute access."""

    def __init__(
        self,
        data_dir: str = "data",
        models_dir: str = "models",
        results_dir: str = "results",
        random_seed: int = RANDOM_SEED,
    ):
        # Base directory paths (string form for legacy code)
        self.data_dir = data_dir
        self.data_raw = os.path.join(data_dir, "raw")
        self.data_processed = os.path.join(data_dir, "processed")
        self.data_logs = os.path.join(data_dir, "logs")
        self.models_dir = models_dir
        self.results_dir = results_dir

        # Back‑compatible alias used by older scripts (e.g. main.py)
        # Allows `CONFIG.results` to resolve to the same path as
        # `CONFIG.results_dir`.
        self.results = self.results_dir

        # Random seed for reproducibility
        self.random_seed = random_seed

        # Measurement‑method whitelist
        self.VALID_MEASUREMENT_METHODS = VALID_MEASUREMENT_METHODS

        # Logger instance for this configuration module
        self.logger = get_logger("config")

    # Tolerant attribute access for unknown methods – returns a no‑op.
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None

        return _noop

    @property
    def results(self) -> str:  # type: ignore[override]
        """Alias for `results_dir` to keep backward compatibility."""
        return self.results_dir

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary‑style getter used by some legacy callers."""
        return getattr(self, key, default)


_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """Singleton accessor for the Config instance."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG


def main():
    """Entry point for config module – useful for ad‑hoc inspection."""
    logger = get_logger("config_main")
    logger.info("Config module loaded")
    cfg = get_config()
    logger.info(f"Data dir: {cfg.data_dir}")
    logger.info(f"Processed dir: {cfg.data_processed}")


if __name__ == "__main__":
    main()
