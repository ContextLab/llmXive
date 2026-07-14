import os
from typing import Any, Dict

class Config:
    """
    Simple configuration wrapper that returns values from environment variables
    with optional defaults. Unknown attribute access returns a no‑op callable
    to keep the contract tolerant.
    """
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, os.getenv(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any attribute that is not explicitly defined.
        This satisfies the many logger‑style calls (e.g., .info(), .debug()) used
        throughout the codebase without raising AttributeError.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

_global_config = Config()

def get_config() -> Config:
    return _global_config

def reload_config() -> None:
    """Placeholder for future dynamic reload logic."""
    pass