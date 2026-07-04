"""
Project configuration and constants.
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

# Constants
MAX_BLOCKS = 100
DEFAULT_CRS = "EPSG:3857"
LOCAL_CRS_TEMPLATE = "EPSG:{utm_zone}2N"

# City Definitions (Example)
CITIES = {
    "nyc": {
        "name": "New York City",
        "bounds": (-74.2591, 40.4774, -73.7002, 40.9176), # (minx, miny, maxx, maxy)
        "crs": "EPSG:3857"
    },
    "la": {
        "name": "Los Angeles",
        "bounds": (-118.6681, 33.7037, -118.1553, 34.3373),
        "crs": "EPSG:3857"
    }
}

def get_path(key: str) -> Path:
    """
    Retrieve a path from configuration or environment.
    
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
    }
    return path_map.get(key, Path(key))

def get_city_bounds(city_name: str) -> Tuple[float, float, float, float]:
    """
    Get bounding box for a city.
    
    Args:
        city_name: City identifier (e.g., 'nyc')
        
    Returns:
        Tuple (minx, miny, maxx, maxy)
    """
    if city_name not in CITIES:
        raise ValueError(f"City '{city_name}' not found in configuration.")
    return CITIES[city_name]["bounds"]

def get_city_crs(city_name: Optional[str] = None) -> str:
    """
    Get CRS for a city or default.
    
    Args:
        city_name: Optional city identifier
        
    Returns:
        CRS string
    """
    if city_name and city_name in CITIES:
        return CITIES[city_name].get("crs", DEFAULT_CRS)
    return DEFAULT_CRS

def load_env_vars() -> Dict[str, str]:
    """
    Load all environment variables.
    
    Returns:
        Dictionary of environment variables
    """
    return dict(os.environ)

def save_config_to_json(path: Path) -> None:
    """
    Save current configuration to a JSON file.
    
    Args:
        path: Output file path
    """
    config = {
        "max_blocks": MAX_BLOCKS,
        "default_crs": DEFAULT_CRS,
        "cities": CITIES,
        "paths": {k: str(v) for k, v in {
            "DATA_DIR": get_path("DATA_DIR"),
            "CODE_DIR": get_path("CODE_DIR"),
            "TESTS_DIR": get_path("TESTS_DIR"),
            "DOCS_DIR": get_path("DOCS_DIR"),
            "RAW_DIR": get_path("RAW_DIR"),
            "PROCESSED_DIR": get_path("PROCESSED_DIR"),
            "RESULTS_DIR": get_path("RESULTS_DIR"),
        }.items()}
    }
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)