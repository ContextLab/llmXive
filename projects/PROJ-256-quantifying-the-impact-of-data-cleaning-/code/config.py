import os
from typing import Any, Dict, Optional

class Config:
    """
    Simple configuration holder that reads values from environment variables
    with sensible defaults. It also provides a permissive ``__getattr__`` and
    ``get`` method to avoid attribute errors across the codebase.
    """

    # Default configuration values
    DATASET_URLS: Dict[str, str] = {}
    OUTPUT_PATH: str = "output"
    RANDOM_SEED: int = 42
    BOOTSTRAP_ITERATIONS: int = 1000

    def __init__(self):
        # Populate from environment where available
        self.DATASET_URLS = self._env_json("DATASET_URLS", default={})
        self.OUTPUT_PATH = os.getenv("OUTPUT_PATH", self.OUTPUT_PATH)
        self.RANDOM_SEED = int(os.getenv("RANDOM_SEED", self.RANDOM_SEED))
        self.BOOTSTRAP_ITERATIONS = int(
            os.getenv("BOOTSTRAP_ITERATIONS", self.BOOTSTRAP_ITERATIONS)
        )

    @staticmethod
    def _env_json(var_name: str, default: Any) -> Any:
        """Parse a JSON‑encoded environment variable, falling back to default."""
        import json

        raw = os.getenv(var_name)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return default
        return default

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """
        Dictionary‑style getter used throughout the project.
        """
        return getattr(self, key, default)

    def __getattr__(self, name: str):
        """
        Fallback for any attribute that does not exist – returns a no‑op
        callable to keep the code tolerant of future extensions.
        """
        def _noop(*args, **kwargs):
            return None

        return _noop

_CONFIG_INSTANCE: Optional[Config] = None

def get_config() -> Config:
    """
    Retrieve a singleton Config instance.
    """
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = Config()
    return _CONFIG_INSTANCE

def reload_config() -> None:
    """
    Force re‑initialisation of the global Config singleton.
    """
    global _CONFIG_INSTANCE
    _CONFIG_INSTANCE = Config()