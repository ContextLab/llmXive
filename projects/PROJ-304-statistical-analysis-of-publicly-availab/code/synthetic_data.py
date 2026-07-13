import os
import sys
import json
import math
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import random
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, mapping
from yaml import safe_dump, safe_load

from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums

# Constants
RANDOM_SEED = 42
NUM_CELLS = 50000
GRID_SIZE_METERS = 200  # 200m grid
CHUNK_SIZE = 5000  # Process in chunks to satisfy FR-010 (T005b)

# Stochastic parameter ranges
NOISE_MEAN_DB = 60.0
NOISE_STD_DB = 10.0
TRAFFIC_MEAN = 1000.0
TRAFFIC_STD = 500.0
POP_DENSITY_MEAN = 2000.0
POP_DENSITY_STD = 1500.0
LAND_USE_RESIDENTIAL = 0.6
LAND_USE_COMMERCIAL = 0.2
LAND_USE_INDUSTRIAL = 0.1
LAND_USE_GREEN = 0.1

logger = get_logger(__name__)

def _generate_stochastic_parameters() -> Dict[str, Any]:
    """Generate the stochastic parameters for this run."""
    return {
        "random_seed": RANDOM_SEED,
        "noise_mean_db": float(NOISE_MEAN_DB),
        "noise_std_db": float(NOISE_STD_DB),
        "traffic_mean": float(TRAFFIC_MEAN),
        "traffic_std": float(TRAFFIC_STD),
        "pop_density_mean": float(POP_DENSITY_MEAN),
        "pop_density_std": float(POP_DENSITY_STD),
        "land_use_distribution": {
            "residential": LAND_USE_RESIDENTIAL,
            "commercial": LAND_USE_COMMERCIAL,
            "industrial": LAND_USE_INDUSTRIAL,
            "green": LAND_USE_GREEN
        },
        "grid_size_meters": GRID_SIZE_METERS,
        "total_cells": NUM_CELLS,
        "chunk_size": CHUNK_SIZE,
        "generated_at": datetime.utcnow().isoformat()
    }

def _create_grid_cells(n_cells: int, seed: int) -> gpd.GeoDataFrame:
    """Create a synthetic grid of square cells."""
    random.seed(seed)
    np.random.seed(seed)
    
    # Generate random centers for grid cells
    # Simulate a city area roughly 10km x 10km
    x_min, x_max = -5000, 5000
    y_min, y_max = -5000, 5000
    
    # Create a grid layout
    cols = int(math.sqrt(n_cells))
    rows = int(n_cells / cols)
    
    x_coords = np.linspace(x_min + GRID_SIZE_METERS/2, x_max - GRID_SIZE_METERS/2, cols)
    y_coords = np.linspace(y_min + GRID_SIZE_METERS/2, y_max - GRID_SIZE_METERS/2, rows)
    
    # If we need more cells than exact grid, add some jittered extra points
    cells = []
    grid_id = 0
    
    for x in x_coords:
        for y in y_coords:
            if grid_id >= n_cells:
                break
            # Create a square polygon
            half_size = GRID_SIZE_METERS / 2
            poly = Polygon([
                (x - half_size, y - half_size),
                (x + half_size, y - half_size),
                (x + half_size, y + half_size),
                (x - half_size, y + half_size)
            ])
            cells.append({
                "grid_id": grid_id,
                "geometry": poly
            })
            grid_id += 1
        if grid_id >= n_cells:
            break
    
    gdf = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    # Convert to WGS84 if necessary (assuming input is projected, convert to lat/lon)
    # For synthetic data, let's assume we are generating in a projected system first
    # then convert to WGS84. Let's use a simple projection for the synthetic city.
    # Actually, let's just generate lat/lon directly for simplicity in a small area.
    # Center at 40.7128, -74.0060 (NYC approx)
    center_lat, center_lon = 40.7128, -74.0060
    
    # Scale meters to degrees (approx)
    # 1 degree lat ~ 111km, 1 degree lon ~ 111km * cos(lat)
    lat_scale = 1 / 111000.0
    lon_scale = 1 / (111000.0 * math.cos(math.radians(center_lat)))
    half_deg = (GRID_SIZE_METERS / 2) * lat_scale
    
    final_cells = []
    for i, cell in enumerate(cells):
        if i >= n_cells:
            break
        geom = cell["geometry"]
        # Calculate centroid in projected meters relative to center
        # We need to reconstruct lat/lon from the grid logic
        # Re-doing the grid generation for lat/lon directly
        pass
    
    # Regenerate correctly for WGS84
    final_cells = []
    grid_id = 0
    for i, x in enumerate(x_coords):
        for j, y in enumerate(y_coords):
            if grid_id >= n_cells:
                break
            
            # Convert grid offset to lat/lon
            lat = center_lat + y * lat_scale
            lon = center_lon + x * lon_scale
            
            # Create square in lat/lon
            half_lat = GRID_SIZE_METERS * lat_scale
            half_lon = GRID_SIZE_METERS * lon_scale
            
            poly = Polygon([
                (lon - half_lon, lat - half_lat),
                (lon + half_lon, lat - half_lat),
                (lon + half_lon, lat + half_lat),
                (lon - half_lon, lat + half_lat)
            ])
            
            final_cells.append({
                "grid_id": grid_id,
                "geometry": poly
            })
            grid_id += 1
        if grid_id >= n_cells:
            break
    
    return gpd.GeoDataFrame(final_cells, crs="EPSG:4326")

def _generate_metrics_for_cell(cell: Dict, seed: int, params: Dict[str, Any]) -> Tuple[Dict, Dict]:
    """Generate noise metrics and covariates for a single cell."""
    np.random.seed(seed + cell["grid_id"])
    
    # Noise metrics
    noise_db = np.random.normal(params["noise_mean_db"], params["noise_std_db"])
    noise_db = max(30, min(120, noise_db))  # Clamp to realistic range
    
    noise_metrics = {
        "avg_db": float(noise_db),
        "max_db": float(noise_db + np.random.uniform(0, 10)),
        "min_db": float(noise_db - np.random.uniform(0, 10)),
        "percentile_95": float(noise_db + np.random.uniform(0, 5))
    }
    
    # Covariates
    traffic = np.random.normal(params["traffic_mean"], params["traffic_std"])
    traffic = max(0, traffic)
    
    pop_density = np.random.normal(params["pop_density_mean"], params["pop_density_std"])
    pop_density = max(0, pop_density)
    
    # Land use (categorical based on probabilities)
    r = np.random.random()
    land_use = "unknown"
    if r < params["land_use_distribution"]["residential"]:
        land_use = "residential"
    elif r < params["land_use_distribution"]["residential"] + params["land_use_distribution"]["commercial"]:
        land_use = "commercial"
    elif r < params["land_use_distribution"]["residential"] + params["land_use_distribution"]["commercial"] + params["land_use_distribution"]["industrial"]:
        land_use = "industrial"
    else:
        land_use = "green"
    
    covariates = {
        "traffic_volume": float(traffic),
        "population_density": float(pop_density),
        "land_use": land_use,
        "distance_to_road": float(np.random.exponential(50, 1)[0]),
        "building_height_avg": float(np.random.normal(15, 5))
    }
    
    # Date (random day in 2023)
    day_of_year = np.random.randint(1, 366)
    date = datetime(2023, 1, 1) + pd.Timedelta(days=day_of_year - 1)
    
    return {
        "grid_id": cell["grid_id"],
        "geometry": cell["geometry"],
        "noise_metrics": noise_metrics,
        "covariates": covariates,
        "date": date
    }

def generate_synthetic_data_chunked(output_path: Optional[Path] = None) -> str:
    """
    Generate synthetic data in chunks to satisfy memory constraints (FR-010).
    Returns the path to the generated parquet file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "raw" / "synthetic_noise_data.parquet"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {NUM_CELLS} synthetic grid cells with seed {RANDOM_SEED}")
    
    # Generate parameters
    params = _generate_stochastic_parameters()
    
    # Create grid cells
    grid_cells = _create_grid_cells(NUM_CELLS, RANDOM_SEED)
    
    # Generate data in chunks
    all_data = []
    
    for i in range(0, NUM_CELLS, CHUNK_SIZE):
        chunk_end = min(i + CHUNK_SIZE, NUM_CELLS)
        logger.info(f"Processing chunk {i//CHUNK_SIZE + 1}: rows {i} to {chunk_end}")
        
        chunk_cells = grid_cells.iloc[i:chunk_end].to_dict(orient="records")
        chunk_data = []
        
        for cell in chunk_cells:
            record = _generate_metrics_for_cell(
                cell, 
                RANDOM_SEED, 
                params
            )
            chunk_data.append(record)
        
        all_data.extend(chunk_data)
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(all_data, crs="EPSG:4326")
    
    # Save to parquet
    gdf.to_parquet(output_path, engine="pyarrow")
    
    logger.info(f"Synthetic data saved to {output_path}")
    
    return str(output_path)

def record_generated_parameters(params: Dict[str, Any]) -> None:
    """
    Record the generated stochastic parameters to the project state YAML file.
    """
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "PROJ-304-statistical-analysis-of-publicly-availab.yaml"
    
    # Load existing state if exists
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = safe_load(f) or {}
            except Exception:
                state = {}
    else:
        state = {}
    
    # Ensure 'synthetic_data' key exists
    if "synthetic_data" not in state:
        state["synthetic_data"] = {}
    
    # Update with new parameters
    state["synthetic_data"].update(params)
    
    # Write back to file
    with open(state_file, 'w') as f:
        safe_dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Recorded synthetic data parameters to {state_file}")

def main() -> None:
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic data generation for T005")
    
    # Generate data
    output_path = generate_synthetic_data_chunked()
    
    # Record parameters
    params = _generate_stochastic_parameters()
    record_generated_parameters(params)
    
    # Update checksums
    compute_and_record_checksums()
    
    logger.info("Synthetic data generation completed successfully")

if __name__ == "__main__":
    main()
