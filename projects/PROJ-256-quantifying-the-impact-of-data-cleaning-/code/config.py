import json
import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()  # Load .env if present

class Config:
    """
    Simple configuration wrapper that loads a JSON file (if provided) and
    falls back to environment variables. Any unknown attribute access returns
    a no‑op callable to keep the rest of the code base tolerant.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        if config_path and os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""
        return self._config.get(key, os.getenv(key, default))

    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute (e.g., logger‑style
        methods like .info, .debug, .warning). This prevents AttributeError
        crashes across the heterogeneous code base.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

_global_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """Singleton accessor for the global Config instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config

def reload_config(config_path: Optional[str] = None) -> None:
    """Force re‑load of configuration."""
    global _global_config
    _global_config = Config(config_path)

def main() -> None:
    """Simple CLI to dump the current configuration."""
    cfg = get_config()
    print(json.dumps(cfg._config, indent=2))
