"""
Configuration loader for the project.
Handles loading YAML configuration, dataset IDs, ROI definitions, and path management.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# Default configuration file path relative to project root
DEFAULT_CONFIG_PATH = "code/config/project_config.yaml"

def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the main project configuration file."""
    path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_PATH)
    
    if not path.exists():
        # Return a sensible default if config is missing during initial setup
        return {
            "datasets": {
                "exclusion": "ds000246",
                "reward": "ds004738"
            },
            "rois": ["Ventral Striatum", "OFC"],
            "paths": {
                "raw_fmri": "data/raw-fmri",
                "processed_fmri": "data/processed-fmri",
                "behavioral": "data/behavioral",
                "results": "data/results"
            },
            "analysis": {
                "smoothing_fwhm": 6.0,
                "alpha": 0.05
            }
        }

    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get the full configuration dictionary."""
    return _load_config(config_path)

def get_all_dataset_ids() -> List[str]:
    """Return a list of all dataset IDs defined in the config."""
    config = get_config()
    datasets = config.get("datasets", {})
    return [v for v in datasets.values() if isinstance(v, str)]

def get_dataset_id(dataset_type: str = "exclusion") -> str:
    """Get a specific dataset ID by type (exclusion or reward)."""
    config = get_config()
    datasets = config.get("datasets", {})
    return datasets.get(dataset_type, "ds000246")

def get_roi_definition(roi_name: str) -> Dict[str, Any]:
    """Get the definition for a specific ROI (e.g., mask path, threshold)."""
    config = get_config()
    rois = config.get("rois", [])
    # Simple lookup for now; in a full config, this would be a dict of dicts
    if roi_name in rois:
        return {"name": roi_name, "source": "atlas"}
    return {}

def get_roi_coordinates(roi_name: str) -> Optional[Dict[str, float]]:
    """Get MNI coordinates for a specific ROI if defined in config."""
    config = get_config()
    # Assuming a structure like: "roi_coords": {"Ventral Striatum": {"x": 10, "y": 10, "z": -5}}
    coords = config.get("roi_coords", {})
    return coords.get(roi_name)

def get_path(key: str, base: Optional[Path] = None) -> Path:
    """Get a path from the config, optionally resolving against a base directory."""
    config = get_config()
    paths = config.get("paths", {})
    rel_path = paths.get(key, key) # Default to key if not found
    
    full_path = Path(rel_path)
    if base:
        full_path = base / full_path
    
    return full_path

def get_analysis_params() -> Dict[str, Any]:
    """Get analysis parameters (smoothing, alpha, etc.)."""
    config = get_config()
    return config.get("analysis", {})

def ensure_paths_exist() -> List[Path]:
    """Ensure all directories defined in the config exist. Creates them if missing."""
    config = get_config()
    paths = config.get("paths", {})
    created = []
    
    for key, rel_path in paths.items():
        p = Path(rel_path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(p)
    
    return created

def get_all_roi_names() -> List[str]:
    """Return a list of all ROI names from config."""
    config = get_config()
    return config.get("rois", [])
