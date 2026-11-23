import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import json
import logging

# Configuration defaults
DEFAULT_CONFIG = {
    "sample_size": 5,
    "min_events": 10,
    "deferred_threshold": 0.5,
    "data_dir": "data",
    "raw_dir": "data/raw",
    "derived_dir": "data/derived",
    "validation_dir": "data/validation",
    "logs_dir": "data/logs",
    "figures_dir": "figures",
    "project_root": ".",
}

_config_cache: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """Load configuration from config.json or return defaults."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                _config_cache = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load config.json: {e}. Using defaults.")
            _config_cache = DEFAULT_CONFIG.copy()
    else:
        _config_cache = DEFAULT_CONFIG.copy()
    
    # Ensure paths are absolute relative to project root
    project_root = _config_cache.get("project_root", ".")
    base = Path(project_root)
    
    for key in ["data_dir", "raw_dir", "derived_dir", "validation_dir", "logs_dir", "figures_dir"]:
        if key in _config_cache:
            path_val = _config_cache[key]
            if not os.path.isabs(path_val):
                _config_cache[key] = str(base / path_val)
        
    return _config_cache

def get_config_summary() -> str:
    """Return a string summary of the current configuration."""
    cfg = get_config()
    return json.dumps(cfg, indent=2)

def get_min_events() -> int:
    """Get the minimum events threshold."""
    return get_config().get("min_events", 10)

def get_sample_size() -> int:
    """Get the target sample size."""
    return get_config().get("sample_size", 5)

def get_deferred_threshold() -> float:
    """Get the deferred threshold."""
    return get_config().get("deferred_threshold", 0.5)

def get_data_dir() -> str:
    """Get the data directory path."""
    return get_config().get("data_dir", "data")

def get_raw_dir() -> str:
    """Get the raw data directory path."""
    return get_config().get("raw_dir", "data/raw")

def get_output_dir() -> str:
    """Get the derived output directory path."""
    return get_config().get("derived_dir", "data/derived")

def ensure_directories_exist(*args: Union[Dict[str, Any], List[str], str, Path, None]) -> None:
  """
  Robust directory creation utility that adapts to various call signatures found in the codebase.
  
  Supported call patterns:
  1. ensure_directories_exist(config_dict) -> creates dirs listed in config (raw_dir, derived_dir, etc.)
  2. ensure_directories_exist([path_str, ...], logger) -> creates list of paths
  3. ensure_directories_exist(path_str) -> creates single path
  4. ensure_directories_exist(Path_obj) -> creates single path
  5. ensure_directories_exist() -> no-op
  6. ensure_directories_exist([path_str], logger) -> creates list
  """
  # Flatten args to a list of potential items
  items = []
  for arg in args:
      if arg is None:
          continue
      if isinstance(arg, dict):
          # Case 1: Config dict
          # Extract known directory keys
          for key in ["raw_dir", "derived_dir", "validation_dir", "logs_dir", "figures_dir", "data_dir"]:
              if key in arg:
                  items.append(arg[key])
      elif isinstance(arg, list):
          # Case 2: List of paths
          items.extend(arg)
      elif isinstance(arg, (str, Path)):
          # Case 3: Single path
          items.append(arg)
      # Ignore logger objects or other types
  
  for item in items:
      if item is None:
          continue
      try:
          # Convert to Path and create
          p = Path(item)
          p.mkdir(parents=True, exist_ok=True)
      except (TypeError, ValueError, OSError) as e:
          # Log warning but do not halt if a path is invalid
          logging.warning(f"Could not create directory {item}: {e}")
