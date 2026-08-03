import os
import sys
import json
import math
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Generator
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, mapping
from datetime import datetime

# Local imports based on API surface
from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums

# Configuration
# Chunk size chosen to ensure memory safety for 50k cells (approx 1-2k rows per chunk)
# 50,000 / 2,000 = 25 chunks, keeping RAM usage well under 7GB
CHUNK_SIZE = 2000
TOTAL_CELLS = 50000
RANDOM_SEED = 42
GRID_RESOLUTION = 200  # meters

logger = get_logger(__name__)

def _generate_chunk_metadata(chunk_id: int, start_idx: int, end_idx: int, seed: int) -> Dict[str, Any]:
    """Generate deterministic metadata for a specific chunk."""
    np.random.seed(seed + chunk_id)
    # Generate spatial parameters for this chunk
    center_lat = np.random.uniform(40.0, 42.0)
    center_lon = np.random.uniform(-74.0, -72.0)
    
    # Stochastic noise parameters
    noise_mean = np.random.uniform(55.0, 75.0)
    noise_std = np.random.uniform(5.0, 15.0)
    traffic_factor = np.random.uniform(0.5, 2.0)
    land_use_factor = np.random.choice(['residential', 'commercial', 'industrial', 'park'])
    
    return {
        "chunk_id": chunk_id,
        "start_index": start_idx,
        "end_index": end_idx,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "noise_mean": noise_mean,
        "noise_std": noise_std,
        "traffic_factor": traffic_factor,
        "land_use_factor": land_use_factor,
        "generated_at": datetime.utcnow().isoformat()
    }

def _generate_chunk_data(chunk_id: int, start_idx: int, end_idx: int, base_seed: int) -> gpd.GeoDataFrame:
    """
    Generate a single chunk of synthetic data.
    This function ensures memory safety by only holding one chunk in memory at a time.
    """
    meta = _generate_chunk_metadata(chunk_id, start_idx, end_idx, base_seed)
    
    count = end_idx - start_idx
    np.random.seed(base_seed + chunk_id)
    
    # Generate grid indices
    grid_ids = [f"cell_{i:06d}" for i in range(start_idx, end_idx)]
    
    # Generate spatial coordinates with jitter
    # Create a rough grid pattern with random jitter
    rows = int(math.ceil(math.sqrt(count)))
    cols = int(math.ceil(count / rows))
    
    # Base grid spacing in degrees (approx 200m at this latitude)
    lat_step = GRID_RESOLUTION / 111320.0
    lon_step = GRID_RESOLUTION / (111320.0 * math.cos(math.radians(meta["center_lat"])))
    
    lats = []
    lons = []
    geometries = []
    
    for i in range(count):
        r = i // cols
        c = i % cols
        
        lat = meta["center_lat"] + (r - rows/2) * lat_step + np.random.uniform(-0.0005, 0.0005)
        lon = meta["center_lon"] + (c - cols/2) * lon_step + np.random.uniform(-0.0005, 0.0005)
        
        lats.append(lat)
        lons.append(lon)
        geometries.append(Point(lon, lat))
    
    # Generate noise metrics
    noise_db = np.random.normal(meta["noise_mean"], meta["noise_std"], count)
    # Ensure non-negative
    noise_db = np.maximum(noise_db, 30.0)
    
    # Generate covariates
    traffic_volume = np.random.uniform(0, 10000, count) * meta["traffic_factor"]
    population_density = np.random.uniform(0, 50000, count)
    
    # Land use assignment based on grid position (deterministic pattern with noise)
    land_uses = [meta["land_use_factor"]] * count
    for i in range(count):
        if np.random.random() < 0.1:
            land_uses[i] = np.random.choice(['residential', 'commercial', 'industrial', 'park'])
    
    # Create DataFrame
    df = pd.DataFrame({
        "grid_id": grid_ids,
        "geometry": geometries,
        "noise_db": noise_db,
        "traffic_volume": traffic_volume,
        "population_density": population_density,
        "land_use": land_uses,
        "date": datetime.utcnow().date()
    })
    
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
    return gdf, meta

def generate_synthetic_data_chunked(output_dir: Optional[str] = None, seed: int = RANDOM_SEED) -> List[str]:
    """
    Generate 50k grid cells in memory-safe chunks.
    
    This function satisfies FR-010 by:
    1. Processing data in chunks of CHUNK_SIZE rows
    2. Writing each chunk to disk immediately (parquet format)
    3. Never holding more than one chunk + metadata in memory
    4. Using a deterministic seed for reproducibility
    
    Args:
        output_dir: Directory to write chunk files. Defaults to data/raw/
        seed: Random seed for reproducibility
        
    Returns:
        List of paths to generated chunk files
    """
    if output_dir is None:
        project_root = get_project_root()
        output_dir = project_root / "data" / "raw"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting synthetic data generation for {TOTAL_CELLS} cells (chunk size: {CHUNK_SIZE})")
    logger.info(f"Output directory: {output_path}")
    
    chunk_files = []
    all_metadata = []
    
    # Process in chunks
    for chunk_id in range(0, TOTAL_CELLS, CHUNK_SIZE):
        start_idx = chunk_id
        end_idx = min(chunk_id + CHUNK_SIZE, TOTAL_CELLS)
        current_chunk_size = end_idx - start_idx
        
        logger.info(f"Generating chunk {chunk_id // CHUNK_SIZE + 1}: indices {start_idx} to {end_idx-1}")
        
        try:
            gdf, meta = _generate_chunk_data(chunk_id, start_idx, end_idx, seed)
            
            # Write chunk to disk immediately to free memory
            chunk_file = output_path / f"synthetic_data_chunk_{chunk_id:06d}_{end_idx:06d}.parquet"
            gdf.to_parquet(chunk_file, index=False)
            chunk_files.append(str(chunk_file))
            
            all_metadata.append(meta)
            
            # Explicitly delete large objects to ensure memory is freed
            del gdf
            del meta
            
        except Exception as e:
            logger.error(f"Failed to generate chunk {chunk_id}: {str(e)}")
            raise
    
    # Record all parameters in state file
    state_file = output_path.parent.parent / "state" / "projects" / "PROJ-304-statistical-analysis-of-publicly-availab.yaml"
    if not state_file.parent.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
    record_generated_parameters(all_metadata, str(state_file), seed, TOTAL_CELLS)
    
    logger.info(f"Successfully generated {len(chunk_files)} chunks containing {TOTAL_CELLS} cells")
    logger.info(f"Parameters recorded in {state_file}")
    
    # Update checksums for the new data
    compute_and_record_checksums()
    
    return chunk_files

def record_generated_parameters(metadata_list: List[Dict[str, Any]], state_file: str, seed: int, total_cells: int):
    """Record generated parameters in the project state YAML file."""
    import yaml
    
    state_data = {
        "project_id": "PROJ-304-statistical-analysis-of-publicly-availab",
        "task_id": "T005b",
        "generation_config": {
            "total_cells": total_cells,
            "chunk_size": CHUNK_SIZE,
            "random_seed": seed,
            "grid_resolution_meters": GRID_RESOLUTION,
            "num_chunks": len(metadata_list)
        },
        "chunk_parameters": metadata_list,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Read existing state if present
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            try:
                existing = yaml.safe_load(f) or {}
                # Merge new data
                existing.update(state_data)
                state_data = existing
            except yaml.YAMLError:
                logger.warning("Existing state file is not valid YAML, overwriting")
    
    # Write updated state
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Recorded generation parameters for {total_cells} cells in {state_file}")

def main():
    """Main entry point for synthetic data generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting synthetic data generation (T005b)")
    
    try:
        chunk_files = generate_synthetic_data_chunked()
        logger.info(f"Generation complete. Created {len(chunk_files)} files.")
        return 0
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())