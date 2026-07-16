import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

# Default project root if not overridden by environment
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Return the project root directory."""
    root_str = os.environ.get("LLMXIVE_PROJECT_ROOT")
    if root_str:
        return Path(root_str).resolve()
    return _DEFAULT_ROOT

def get_data_path(sub_path: str = "") -> Path:
    """Return the path to the data directory, optionally with a sub-path."""
    root = get_project_root()
    base = root / "data"
    if sub_path:
        return base / sub_path
    return base

def get_output_path(sub_path: str = "") -> Path:
    """Return the path to the outputs directory, optionally with a sub-path."""
    root = get_project_root()
    base = root / "outputs"
    if sub_path:
        return base / sub_path
    return base

class Configuration:
    """Simple configuration holder."""
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return self._config.copy()

def get_config() -> Configuration:
    """Load configuration from environment or defaults."""
    config_path = os.environ.get("LLMXIVE_CONFIG_PATH")
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            data = json.load(f)
        return Configuration(data)
    return Configuration()

def main() -> None:
    """CLI entry point for config inspection."""
    root = get_project_root()
    cfg = get_config()
    print(f"Project Root: {root}")
    print(f"Data Path: {get_data_path()}")
    print(f"Output Path: {get_output_path()}")
    print(f"Config: {cfg.to_dict()}")

if __name__ == "__main__":
    main()