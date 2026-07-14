"""
Duplicate of ``code/config/env_config.py`` kept for backward compatibility.
The implementation mirrors the primary file and includes the same tolerant
``AppConfig`` definition.
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
    def get(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key, default)

    def __getitem__(self, key: Any) -> Any:  # pragma: no cover
        return super().get(key)

@dataclass
class AppConfig:
    config: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            logger.debug("AppConfig no‑op called for attribute '%s' with args=%s kwargs=%s", name, args, kwargs)
            return None
        return _noop

    def info(self, *args, **kwargs):
        logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        logger.debug(*args, **kwargs)

    def warning(self, *args, **kwargs):
        logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        logger.critical(*args, **kwargs)

def load_config(config_path: Optional[Path] = None) -> AppConfig:
    cfg = {}
    if config_path is None:
        default_path = Path(__file__).resolve().parents[2] / "config.json"
        if default_path.is_file():
            config_path = default_path
    if config_path and config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load config from %s: %s", config_path, exc)
    return AppConfig(config=cfg)

def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def get_seed() -> int:
    env_seed = os.getenv("PROJECT_SEED")
    try:
        return int(env_seed) if env_seed is not None else 42
    except ValueError:  # pragma: no cover
        logger.warning("Invalid PROJECT_SEED value %s – using default 42", env_seed)
        return 42

def main() -> None:  # pragma: no cover
    cfg = load_config()
    print(json.dumps(cfg.config, indent=2))