import logging
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration."""
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    return root_logger

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a schema from a YAML file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(schema: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """Validate data against a schema (basic implementation)."""
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return False
    return True

def validate_song_record(record: Dict[str, Any]) -> bool:
    """Validate a song record against expected fields."""
    required_fields = ['species_id', 'lat', 'lon', 'song_metric_1', 'song_metric_2']
    for field in required_fields:
        if field not in record:
            logger.warning(f"Invalid song record: missing {field}")
            return False
    return True

def validate_climate_snapshot(record: Dict[str, Any]) -> bool:
    """Validate a climate snapshot against expected fields."""
    required_fields = ['lat', 'lon', 'temperature', 'precipitation', 'elevation']
    for field in required_fields:
        if field not in record:
            logger.warning(f"Invalid climate snapshot: missing {field}")
            return False
    return True

def validate_analysis_dataset(record: Dict[str, Any]) -> bool:
    """Validate an analysis dataset record against expected fields."""
    required_fields = ['species_id', 'lat', 'lon', 'song_metric_1', 'song_metric_2',
                     'temperature', 'precipitation', 'elevation']
    for field in required_fields:
        if field not in record:
            logger.warning(f"Invalid analysis dataset: missing {field}")
            return False
    return True

def reproject_coordinates(lat: float, lon: float, from_crs: str, to_crs: str) -> tuple:
    """Reproject coordinates from one CRS to another."""
    try:
        import pyproj
        transformer = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True)
        new_lon, new_lat = transformer.transform(lon, lat)
        return new_lat, new_lon
    except ImportError:
        logger.error("pyproj not installed. Cannot reproject coordinates.")
        raise
    except Exception as e:
        logger.error(f"Error reprojecting coordinates: {e}")
        raise

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(size: float) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def load_csv_with_validation(file_path: str, validator_func, schema: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Load a CSV file and validate each row."""
    import csv
    rows = []
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if not validator_func(row):
                logger.warning(f"Invalid row {i+1} in {file_path}: {row}")
                continue
            rows.append(row)
    return rows