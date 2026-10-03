import logging
import os
import sys
import json
import yaml
import hashlib
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import math

# Optional heavy dependencies for reprojection
try:
    import pyproj
    import pandas as pd
    import geopandas as gpd
    HAS_GEOSPACE = True
except ImportError:
    HAS_GEOSPACE = False
    pyproj = None
    pd = None
    gpd = None

# Optional state manager imports if available in other modules
# We define a local wrapper to avoid circular imports if utils is imported early
def _update_state_file(artifact_path: str, project_id: str = "PROJ-334-predicting-avian-song-variation-with-cli"):
    """
    Wrapper to update state file. 
    Tries to import from state_manager if available, otherwise logs warning.
    """
    if HAS_GEOSPACE:
        try:
            from state_manager import compute_file_hash, load_state, save_state
            state_path = Path("state") / "projects" / f"{project_id}.yaml"
            if state_path.exists():
                state = load_state(state_path)
                state["artifact_hashes"][artifact_path] = compute_file_hash(artifact_path)
                save_state(state_path, state)
        except Exception as e:
            logging.warning(f"Could not update state file for {artifact_path}: {e}")
    else:
        logging.warning("Geo-space libraries not installed, cannot update state file.")


def setup_logging(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dictionary against a schema definition.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    for field, value in data.items():
        if field in properties:
            prop_def = properties[field]
            expected_type = prop_def.get('type')
            
            # Basic type checking
            if expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            elif expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
            elif expected_type == 'integer':
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' must be an integer, got {type(value).__name__}")
            # Add more type checks if needed based on schema complexity
        else:
            # Optional: warn on extra fields? For now, we allow them.
            pass

    return len(errors) == 0, errors


def validate_song_record(record: Dict[str, Any], schema: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """Validate a single SongRecord row against the schema."""
    if schema is None:
        schema_path = "contracts/song_record.schema.yaml"
        if not Path(schema_path).exists():
            # Fallback if schema not yet generated in this specific run context
            # but we expect it to exist per T007
            raise FileNotFoundError(f"Schema file {schema_path} not found. Run T007 first.")
        schema = load_schema(schema_path)
    
    return validate_schema(record, schema)


def validate_climate_snapshot(record: Dict[str, Any], schema: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """Validate a single ClimateSnapshot row against the schema."""
    if schema is None:
        schema_path = "contracts/climate_snapshot.schema.yaml"
        if not Path(schema_path).exists():
            raise FileNotFoundError(f"Schema file {schema_path} not found. Run T007 first.")
        schema = load_schema(schema_path)
    
    return validate_schema(record, schema)


def validate_analysis_dataset(record: Dict[str, Any], schema: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """Validate a single AnalysisDataset row against the schema."""
    if schema is None:
        schema_path = "contracts/analysis_dataset.schema.yaml"
        if not Path(schema_path).exists():
            raise FileNotFoundError(f"Schema file {schema_path} not found. Run T007 first.")
        schema = load_schema(schema_path)
    
    return validate_schema(record, schema)


def reproject_coordinates(df: 'pd.DataFrame', input_crs: str, output_crs: str = "EPSG:4326") -> 'pd.DataFrame':
    """
    Reproject coordinates in a pandas DataFrame to EPSG:4326 (WGS84).
    
    Args:
        df: DataFrame containing 'lat' and 'lon' columns (or 'latitude', 'longitude').
        input_crs: The source CRS string (e.g., "EPSG:4326", "EPSG:26910").
        output_crs: The target CRS string (default "EPSG:4326").
    
    Returns:
        A new DataFrame with updated coordinates.
    
    Raises:
        ImportError: If pyproj/pandas/geopandas are not installed.
        ValueError: If CRS transformation fails or columns are missing.
    """
    if not HAS_GEOSPACE:
        raise ImportError("pyproj, pandas, or geopandas is required for reprojection. Install them via requirements.txt.")

    # Normalize column names
    lat_col = 'lat' if 'lat' in df.columns else ('latitude' if 'latitude' in df.columns else None)
    lon_col = 'lon' if 'lon' in df.columns else ('longitude' if 'longitude' in df.columns else None)

    if not lat_col or not lon_col:
        raise ValueError("DataFrame must contain 'lat'/'latitude' and 'lon'/'longitude' columns.")

    # Create a GeoDataFrame temporarily for transformation
    # We assume the input coordinates are in the specified input_crs
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs=input_crs
    )

    # Reproject
    if gdf.crs is None:
        gdf.set_crs(input_crs, inplace=True)
    
    gdf_reprojected = gdf.to_crs(output_crs)

    # Extract new coordinates
    new_lons = gdf_reprojected.geometry.x
    new_lats = gdf_reprojected.geometry.y

    # Create a new dataframe to avoid SettingWithCopyWarning
    result_df = df.copy()
    result_df[lon_col] = new_lons.values
    result_df[lat_col] = new_lats.values

    return result_df


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero."""
    if b == 0:
        return default
    return a / b


def format_bytes(size: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def load_csv_with_validation(filepath: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    Load a CSV file and validate each row against a schema.
    Returns a list of valid rows. Raises an error if validation fails.
    """
    schema_path = f"contracts/{schema_name}.schema.yaml"
    schema = load_schema(schema_path)
    
    valid_rows = []
    errors = []

    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Convert numeric strings to floats where appropriate
            # This is a basic coercion; strict validation might require more logic
            for key, value in row.items():
                if value is not None and value != '':
                    try:
                        # Try float first
                        row[key] = float(value)
                        # If it's an integer in the schema, keep as int if possible
                        if key in schema.get('properties', {}) and schema['properties'][key].get('type') == 'integer':
                            row[key] = int(row[key])
                    except ValueError:
                        pass # Keep as string

            is_valid, row_errors = validate_schema(row, schema)
            if is_valid:
                valid_rows.append(row)
            else:
                errors.append(f"Row {i+2}: {row_errors}")
    
    if errors:
        # Log first few errors
        logging.error(f"Validation failed for {len(errors)} rows in {filepath}. First 3 errors: {errors[:3]}")
        raise ValueError(f"Schema validation failed for {len(errors)} rows in {filepath}")
    
    return valid_rows


def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def update_state_file(artifact_path: str, project_id: str = "PROJ-334-predicting-avian-song-variation-with-cli"):
    """
    Updates the project state file with the hash of the given artifact.
    """
    _update_state_file(artifact_path, project_id)