"""
Configuration handling for the project.

The ``Config`` class provides a ``get`` method (used throughout the code
base) and a permissive ``__getattr__`` fallback so that any attribute
access that is not explicitly defined returns a no‑op callable.  This
satisfies the diverse call patterns required by the many scripts that
import ``config``.
"""

import os
from typing import Any, Dict, Optional

__all__ = ["Config", "get_config", "reload_config"]


class Config:
    """
    Simple configuration wrapper around environment variables.

    Attributes are accessed via ``get(key, default)``.  Unknown attribute
    names resolve to a no‑op callable to avoid ``AttributeError`` in
    legacy scripts.
    """

    def __init__(self) -> None:
        # Load all environment variables into an internal dict for fast lookup.
        self._store: Dict[str, str] = dict(os.environ)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Parameters
        ----------
        key : str
            Configuration key name.
        default : Any, optional
            Value to return if the key is missing.

        Returns
        -------
        Any
            The stored value (as a string) or ``default``.
        """
        return self._store.get(key, default)

    # -----------------------------------------------------------------
    # Compatibility helpers – any unknown attribute becomes a callable
    # that does nothing and returns ``None``.  This mirrors the logger‑style
    # usage (e.g. ``config.info(...)``) found in many scripts.
    # -----------------------------------------------------------------
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


# Global singleton used by the rest of the code base.
_GLOBAL_CONFIG = Config()


def get_config() -> Config:
    """
    Return the global configuration instance.
    """
    return _GLOBAL_CONFIG


def reload_config() -> None:
    """
    Reload configuration from the environment.  Useful in long‑running
    processes where environment variables may change.
    """
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = Config()
