import os
import json
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Simple configuration wrapper that reads environment variables and falls
    back to a supplied default.  The class is deliberately tolerant: any
    attribute access that is not explicitly defined returns a no‑op callable,
    preventing AttributeError in loosely‑typed call‑sites.
    """

    def __init__(self):
        # Load a JSON config file if present
        self._config: Dict[str, Any] = {}
        config_path = os.getenv("CONFIG_JSON", "")
        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value from the environment or the JSON dict."""
        return os.getenv(key, self._config.get(key, default))

    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute.  This satisfies
        scripts that treat the Config object like a logger (e.g. ``config.info()``).
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

    def __setattr__(self, name: str, value: Any):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._config[name] = value

_global_config: Optional[Config] = None

def get_config() -> Config:
    """Return a singleton Config instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config() -> None:
    """Force re‑loading of the configuration."""
    global _global_config
    _global_config = Config()

def main() -> None:
    """Simple CLI to dump the current configuration (useful for debugging)."""
    cfg = get_config()
    print(json.dumps(cfg._config, indent=2))
