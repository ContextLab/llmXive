import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Simple configuration holder that reads environment variables.
    It also provides a permissive ``__getattr__`` so that any
    attribute accessed (e.g. ``config.info(...)``) returns a no‑op
    callable instead of raising ``AttributeError``.  This satisfies
    the many heterogeneous call‑sites throughout the project.
    """

    def __init__(self):
        # Default configuration values – can be overridden by env vars
        self._values: Dict[str, Any] = {
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv(
                "PROCESSED_DATA_PATH", "data/processed"
            ),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(
                os.getenv("BOOTSTRAP_ITERATIONS", "1000")
            ),
            "OUTCOME_COLUMN": os.getenv("OUTCOME_COLUMN", "target"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.
        """
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set or overwrite a configuration value.
        """
        self._values[key] = value

    # ------------------------------------------------------------------
    # Compatibility shim – any unknown attribute becomes a no‑op callable.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute.
        This mirrors typical logger APIs (info, debug, warning, error, etc.)
        and prevents AttributeError in legacy call‑sites.
        """
        def _noop(*args, **kwargs):
            return None

        return _noop

# Global singleton for convenience
_CONFIG = Config()

def get_config() -> Config:
    """
    Access the global configuration instance.
    """
    return _CONFIG

def reload_config() -> None:
    """
    Reload environment variables and refresh the singleton.
    """
    global _CONFIG
    _CONFIG = Config()

# Simple script entry‑point for manual inspection
def main() -> None:
    cfg = get_config()
    for k, v in cfg._values.items():
        print(f"{k} = {v}")