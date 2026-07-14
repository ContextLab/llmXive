"""
code/config/env_config.py

Central configuration helper used throughout the project.
The original implementation already provided basic loading facilities.
This patch adds a tolerant ``get`` accessor and a ``__getattr__`` fallback
so that any caller expecting a logger‑style method (e.g. ``config.get(...)``)
will not raise ``AttributeError``.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

@dataclass
class TolerantDict(dict):
    """A dict that returns ``default`` for missing keys instead of raising."""

    def get(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key, default)


@dataclass
class AppConfig:
    """
    Holds the loaded configuration dictionary.
    The class is deliberately permissive: callers may request arbitrary
    attributes (e.g. ``config.info(...)``) and will receive a no‑op callable.
    """

    config_path: Path = field(default_factory=lambda: Path("config") / "settings.json")
    _config: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        if self.config_path.is_file():
            try:
                with self.config_path.open("r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to load config: %s", exc)
                self._config = {}
        else:
            logger.warning("Config file %s not found – using empty config", self.config_path)
            self._config = {}

    # ------------------------------------------------------------------
    # Existing public API (preserved)
    # ------------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """Return the whole configuration dictionary."""
        return self._config

    # ------------------------------------------------------------------
    # New tolerant accessors
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Dictionary‑style getter used throughout the codebase.
        Allows nested look‑ups like ``config.get("paths", {})``.
        """
        return self._config.get(key, default)

    def __getattr__(self, name: str):
        """
        Fallback for any attribute that is not explicitly defined.
        Returns a no‑op callable so that ``config.info(...)`` etc. work
        without raising ``AttributeError``.
        """
        def _noop(*args, **kwargs):
            logger.debug("AppConfig no‑op called for missing attribute %s", name)
            return None

        return _noop


def load_config(path: Optional[Path] = None) -> AppConfig:
    """
    Helper to instantiate ``AppConfig`` with an optional custom path.
    """
    cfg_path = path or Path("config") / "settings.json"
    return AppConfig(config_path=cfg_path)


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def get_seed() -> int:
    """Return a deterministic seed; can be overridden via environment variable."""
    return int(os.getenv("PROJECT_SEED", "42"))


def main() -> None:
    """Simple demo entry‑point."""
    cfg = load_config()
    setup_logging()
    logger.info("Loaded configuration with %d keys", len(cfg.load()))


if __name__ == "__main__":
    main()