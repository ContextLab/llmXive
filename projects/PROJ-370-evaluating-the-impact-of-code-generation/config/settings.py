import os
import json
from pathlib import Path
from typing import Dict, Any, List

def get_config() -> Dict[str, Any]:
    """Load configuration from config/config.json if it exists."""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

def get_target_repos() -> List[str]:
    """Get list of target repositories from config or defaults."""
    config = get_config()
    return config.get("target_repos", [
        "microsoft/vscode",
        "python/cpython"
    ])

def get_paths() -> Dict[str, str]:
    """Get base paths for data and results."""
    base = Path(__file__).parent.parent
    return {
        "base": str(base),
        "data_raw": str(base / "data" / "raw"),
        "data_derived": str(base / "data" / "derived"),
        "data_annotations": str(base / "data" / "annotations"),
        "results": str(base / "results"),
        "specs": str(base / "specs"),
        "logs": str(base / "logs")
    }

def ensure_directories():
    """Create all required directories if they don't exist."""
    paths = get_paths()
    for path_str in paths.values():
        Path(path_str).mkdir(parents=True, exist_ok=True)