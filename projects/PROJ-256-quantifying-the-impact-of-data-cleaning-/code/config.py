import os
from typing import Any, Dict, Optional

class Config:
    """
    Simple configuration holder that reads environment variables.
    It is deliberately permissive: any attribute access that is not
    explicitly defined returns a no‑op callable, preventing AttributeError
    in loosely‑typed call sites.
    """

    def __init__(self):
        # Example configuration keys; more can be added via env vars.
        self._settings: Dict[str, Any] = {
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv(
                "PROCESSED_DATA_PATH", "data/processed"
            ),
            "DATASET_URLS": os.getenv(
                "DATASET_URLS",
                "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip,"
                "https://archive.ics.uci.edu/ml/machine-learning-databases/00462/shopping%20dataset%20(1).zip",
            ),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        }

    # ------------------------------------------------------------------
    # Standard get method used throughout the project.
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    # ------------------------------------------------------------------
    # Fallback for any other attribute/method access.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        """
        Return a no‑op callable for any undefined attribute. This makes the
        Config object tolerant to arbitrary method names used in various
        scripts (e.g., ``config.info(...)``).
        """
        def _noop(*args, **kwargs):
            return None

        return _noop

# Helper to obtain a singleton Config instance.
_global_config = Config()

def get_config() -> Config:
    return _global_config

def reload_config() -> None:
    """Reload configuration from environment variables."""
    global _global_config
    _global_config = Config()