"""
Project configuration and constants.

This module manages all project-wide constants, city definitions,
CRS settings, and path utilities.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Memory Safety & Planning Constants ---
# MAX_BLOCKS is set to [DEFERRED] as per task requirements.
# Actual values should be determined by plan.md or runtime profiling (T038b).
MAX_BLOCKS = 100  # Placeholder: Refer to plan.md for final tuning

# Missing Data Threshold (Placeholder: Refer to plan.md or T014b logic)
MISSING_DATA_THRESHOLD = 0.20

# GWR Bandwidths for sensitivity analysis (T034)
GWR_BANDWIDTHS = [100, 200, 500, 1000, 2000]

# --- CRS Settings ---
DEFAULT_CRS = "EPSG:3857"
# Template for local UTM CRS: EPSG:{zone}2N (Northern Hemisphere assumption for demo)
# Logic to determine zone dynamically is handled in utils/memory.py or ingest.py if needed.
LOCAL_CRS_TEMPLATE = "EPSG:{utm_zone}2N"

# --- City Definitions ---
# Includes New York City and Los Angeles as primary examples.
# Bounds are (minx, miny, maxx, maxy) in WGS84 (EPSG:4326) before reprojection.
CITIES: Dict[str, Dict[str, any]] = {
    "nyc": {
        "name": "New York City",
        "bounds": (-74.2591, 40.4774, -73.7002, 40.9176),
        "crs": "EPSG:3857",
        "utm_zone": 18  # Approximate for NYC
    },
    "la": {
        "name": "Los Angeles",
        "bounds": (-118.6681, 33.7037, -118.1553, 34.3373),
        "crs": "EPSG:3857",
        "utm_zone": 11  # Approximate for LA
    },
    "chicago": {
        "name": "Chicago",
        "bounds": (-87.9403, 41.6445, -87.5240, 42.0230),
        "crs": "EPSG:3857",
        "utm_zone": 16
    }
}

def get_path(key: str) -> Path:
    """
    Retrieve a standard project path based on a key.
    
    Args:
        key: Key name (e.g., 'DATA_DIR', 'CODE_DIR')
            
    Returns:
        Path object
    """
    path_map = {
        "DATA_DIR": PROJECT_ROOT / "data",
        "CODE_DIR": PROJECT_ROOT / "code",
        "TESTS_DIR": PROJECT_ROOT / "tests",
        "DOCS_DIR": PROJECT_ROOT / "docs",
        "RAW_DIR": PROJECT_ROOT / "data" / "raw",
        "PROCESSED_DIR": PROJECT_ROOT / "data" / "processed",
        "RESULTS_DIR": PROJECT_ROOT / "data" / "results",
        "FIGURES_DIR": PROJECT_ROOT / "data" / "results" / "figures",
        "SPEC_DIR": PROJECT_ROOT / "specs" / "001-urban-heat-osm",
    }
    if key not in path_map:
        raise KeyError(f"Unknown path key: {key}. Available keys: {list(path_map.keys())}")
    return path_map[key]

def get_city_bounds(city_name: str) -> Tuple[float, float, float, float]:
    """
    Get bounding box for a city in WGS84 (EPSG:4326).
    
    Args:
        city_name: City identifier (e.g., 'nyc')
            
    Returns:
        Tuple (minx, miny, maxx, maxy)
    """
    if city_name not in CITIES:
        raise ValueError(f"City '{city_name}' not found in configuration. Available: {list(CITIES.keys())}")
    return CITIES[city_name]["bounds"]

def get_city_crs(city_name: Optional[str] = None) -> str:
    """
    Get CRS for a city or default.
    
    Args:
        city_name: Optional city identifier. If None, returns DEFAULT_CRS.
            
    Returns:
        CRS string (e.g., 'EPSG:3857')
    """
    if city_name and city_name in CITIES:
        return CITIES[city_name].get("crs", DEFAULT_CRS)
    return DEFAULT_CRS

def get_city_utm_zone(city_name: str) -> Optional[int]:
    """
    Get the approximate UTM zone for a city for local projection.
    
    Args:
        city_name: City identifier
            
    Returns:
        UTM zone integer or None if not found
    """
    if city_name in CITIES:
        return CITIES[city_name].get("utm_zone")
    return None

def load_env_vars() -> Dict[str, str]:
    """
    Load all environment variables.
    
    Returns:
        Dictionary of environment variables
    """
    return dict(os.environ)

def save_config_to_json(path: Path) -> None:
    """
    Save current configuration to a JSON file for reproducibility.
    
    Args:
        path: Output file path
    """
    config = {
        "max_blocks": MAX_BLOCKS,
        "missing_data_threshold": MISSING_DATA_THRESHOLD,
        "default_crs": DEFAULT_CRS,
        "local_crs_template": LOCAL_CRS_TEMPLATE,
        "cities": {
            k: {
                "name": v["name"],
                "bounds": v["bounds"],
                "crs": v["crs"],
                "utm_zone": v.get("utm_zone")
            } for k, v in CITIES.items()
        },
        "paths": {k: str(v) for k, v in {
            "DATA_DIR": get_path("DATA_DIR"),
            "CODE_DIR": get_path("CODE_DIR"),
            "TESTS_DIR": get_path("TESTS_DIR"),
            "DOCS_DIR": get_path("DOCS_DIR"),
            "RAW_DIR": get_path("RAW_DIR"),
            "PROCESSED_DIR": get_path("PROCESSED_DIR"),
            "RESULTS_DIR": get_path("RESULTS_DIR"),
            "FIGURES_DIR": get_path("FIGURES_DIR"),
        }.items()},
        "gwr_bandwidths": GWR_BANDWIDTHS
    }
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)