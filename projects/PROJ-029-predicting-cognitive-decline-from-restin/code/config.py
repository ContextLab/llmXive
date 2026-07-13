import os
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "raw_data_dir": str(PROJECT_ROOT / "data" / "raw"),
    "processed_data_dir": str(PROJECT_ROOT / "data" / "processed"),
    "artifacts_dir": str(PROJECT_ROOT / "data" / "artifacts"),
    "figures_dir": str(PROJECT_ROOT / "figures"),
    "log_dir": str(PROJECT_ROOT / "logs"),
    "random_seed": 42,
    "max_runtime_hours": 6,
    "memory_limit_gb": 7,
    "n_jobs": 2,
    "log_level": "INFO"
}

_config_cache = None

def get_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        import json
        try:
            with open(config_path, 'r') as f:
                custom = json.load(f)
                _config_cache = {**DEFAULT_CONFIG, **custom}
        except Exception:
            _config_cache = DEFAULT_CONFIG
    else:
        _config_cache = DEFAULT_CONFIG
    
    return _config_cache

def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)
