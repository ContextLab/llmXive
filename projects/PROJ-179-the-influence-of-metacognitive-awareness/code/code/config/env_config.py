"""
code/code/config/env_config.py

Duplicate of ``code/config/env_config.py`` for legacy import paths.
The implementation mirrors the primary file and adds the same tolerant
``get`` method and ``__getattr__`` fallback.
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

    def load(self) -> Dict[str, Any]:
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            logger.debug("AppConfig no‑op called for missing attribute %s", name)
            return None

        return _noop


def load_config(path: Optional[Path] = None) -> AppConfig:
    cfg_path = path or Path("config") / "settings.json"
    return AppConfig(config_path=cfg_path)


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def get_seed() -> int:
    return int(os.getenv("PROJECT_SEED", "42"))


def main() -> None:
    cfg = load_config()
    setup_logging()
    logger.info("Loaded configuration with %d keys", len(cfg.load()))


if __name__ == "__main__":
    main()