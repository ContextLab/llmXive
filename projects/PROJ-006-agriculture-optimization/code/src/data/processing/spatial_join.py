import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, mapping
import numpy as np

# Import local project utilities
from src.config.constants import BUFFER_SIZE_KM, GRID_RESOLUTION_KM
from src.utils.io_helpers import setup_logging, write_csv_strict, write_json_strict

logger = setup_logging("spatial_join")

def apply_geodesic_buffer(df_survey: pd.DataFrame, buffer_km: float) -> gpd.GeoDataFrame:
    """
    Apply a geodesic buffer around household coordinates.
    
    Args:
        df_survey: DataFrame with 'latitude' and 'longitude' columns.
        buffer_km: Radius in kilometers.
        
    Returns:
        GeoDataFrame with buffered geometries.
    """
    logger.info(f"Applying geodesic buffer of {buffer_km} km...")
    
    # Filter out rows with missing coordinates
    valid_df = df_survey.dropna(subset=['latitude', 'longitude'])
    logger.info(f"Filtered {len(df_survey) - len(valid_df)} rows with missing coordinates.")
    
    if valid_df.empty:
        logger.error("No valid households with coordinates found.")
        raise ValueError("No valid households with coordinates found.")
    
    # Create Point geometries
    geometry = [Point(xy) for xy in zip(valid_df.longitude, valid_df.latitude)]
    gdf = gpd.GeoDataFrame(valid_df, geometry=geometry, crs="EPSG:4326")
    
    # Transform to a projected CRS for distance calculation (e.g., UTM zone 36S for Malawi/Tanzania approx)
    # Since we don't know exact zone, we use a generic equal-area projection or buffer in degrees approximated
    # For simplicity and robustness across regions in this synthetic/structural validation context,
    # we convert buffer_km to degrees approx (1 deg ~ 111km) or use a local projection if possible.
    # Better: Use geodesic buffer logic via pyproj or transform to UTM.
    # To avoid heavy deps, we will transform to a suitable UTM zone dynamically if possible, 
    # or use a generic buffer in meters after transforming to a global projection (e.g., Web Mercator is bad for area, 
    # but for small buffers < 1km it's acceptable, or use EPSG:3857).
    # Actually, best practice: Transform to UTM based on centroid longitude.
    
    # Dynamic UTM selection
    centroid_lon = gdf.geometry.centroid.x
    utm_zone = int((centroid_lon + 180) / 6) + 1
    # Determine hemisphere (simplified: assume southern hemisphere for Malawi/Tanzania context if lat < 0)
    # Malawi/Tanzania are in Southern Hemisphere.
    hemi = 'S' if valid_df.latitude.mean() < 0 else 'N'
    epsg_code = f"EPSG:{32600 + utm_zone if hemi == 'N' else 32700 + utm_zone}"
    
    logger.info(f"Transforming to UTM Zone {utm_zone} {hemi} (EPSG:{epsg_code.split(':')[1]})")
    
    gdf_projected = gdf.to_crs(epsg=int(epsg_code.split(':')[1]))
    
    # Buffer in meters
    buffer_m = buffer_km * 1000.0
    gdf_projected['geometry'] = gdf_projected.geometry.buffer(buffer_m)
    
    # Transform back to WGS84 for GeoJSON
    gdf_buffered = gdf_projected.to_crs(epsg=4326)
    
    return gdf_buffered

def extract_ndvi_from_granules(gdf_buffered: gpd.GeoDataFrame, synthetic_mode: bool = True) -> pd.DataFrame:
    """
    Extract mean NDVI for the buffer area.
    If synthetic mode, generates synthetic NDVI values consistent with the household.
    """
    logger.info("Extracting NDVI values...")
    
    if synthetic_mode:
        # Generate synthetic NDVI time-series stats for the household
        # In a real scenario, this would sample from rasterio over the geometry
        # Here we simulate the 'mean' NDVI derived from the time-series logic in T018b
        # We use a stochastic function based on household ID to ensure reproducibility
        
        results = []
        np.random.seed(42) # Global seed for reproducibility in synthetic mode
        
        for idx, row in gdf_buffered.iterrows():
            # Simulate a mean NDVI value (0.1 to 0.9 typical range)
            # Use household_id or index as seed for deterministic randomness
            seed_val = hash(str(row.get('household_id', idx))) % (2**32)
            rng = np.random.RandomState(seed_val)
            
            # Simulate seasonal variation + noise
            mean_ndvi = rng.uniform(0.3, 0.7)
            noise = rng.normal(0, 0.1)
            ndvi_val = max(0.0, min(1.0, mean_ndvi + noise))
            
            results.append({
                'household_id': row['household_id'],
                'mean_ndvi': ndvi_val,
                'buffer_area_km2': row.geometry.area / 1e6 if hasattr(row.geometry, 'area') else 0.0
            })
        
        return pd.DataFrame(results)
    else:
        # Real data path: Requires rasterio and actual tifs
        # This is a placeholder for the real logic which would iterate over granules
        # For now, raise if synthetic is not allowed and no data exists
        raise NotImplementedError("Real NDVI extraction requires pre-downloaded granules and rasterio logic.")

def verify_linkage_and_trigger_aggregation(
    df_survey: pd.DataFrame,
    df_joined: pd.DataFrame,
    data_source_type: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Verify linkage percentage and determine if aggregation is triggered.
    """
    total_households = len(df_survey)
    matched_households = len(df_joined)
    
    if total_households == 0:
        logger.critical("FATAL_NO_HOUSEHOLDS: No households in survey data.")
        raise SystemExit("FATAL_NO_HOUSEHOLDS: No households in survey data.")
    
    linkage_percentage = (matched_households / total_households) * 100.0
    logger.info(f"Linkage Percentage: {linkage_percentage:.2f}% ({matched_households}/{total_households})")
    
    # Trigger aggregation if linkage < 95% or N < 300
    triggered_aggregation = (linkage_percentage < 95.0) or (matched_households < 300)
    exclusion_reason = ""
    
    if linkage_percentage < 95.0:
        exclusion_reason = "Low linkage percentage (<95%)"
    if matched_households < 300:
        if exclusion_reason:
            exclusion_reason += "; "
        exclusion_reason += "Insufficient sample size (<300)"
    
    if not exclusion_reason:
        exclusion_reason = "None"
        
    validation_log = {
        "linkage_percentage": linkage_percentage,
        "total_valid_households": total_households,
        "matched_households": matched_households,
        "triggered_aggregation": triggered_aggregation,
        "exclusion_reason": exclusion_reason,
        "data_source_type": data_source_type
    }
    
    logger.info(f"Aggregation Triggered: {triggered_aggregation}")
    
    return df_joined, validation_log

def main():
    """
    Main entry point for spatial join processing.
    """
    project_root = Path(__file__).resolve().parents[3]
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    data_logs_dir = project_root / "data" / "logs"
    
    # Ensure output directories exist
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    data_logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Input files
    survey_file = data_raw_dir / "filtered_survey.csv"
    if not survey_file.exists():
        logger.error(f"Input file not found: {survey_file}")
        sys.exit(1)
    
    # Load survey data
    df_survey = pd.read_csv(survey_file)
    logger.info(f"Loaded {len(df_survey)} households from {survey_file}")
    
    # Determine data source type
    # Check if real data exists (T015c) or synthetic (T015b)
    # For this task, we assume if 'lsms_isa.csv' exists in raw, it's real, else synthetic
    # However, T015b generates 'survey_raw.csv' and 'filtered_survey.csv'.
    # We infer source type based on the presence of the raw source file or a flag.
    # Since we are in a pipeline, we check for the existence of the 'real' source.
    real_source_exists = (data_raw_dir / "lsms_isa.csv").exists()
    data_source_type = "Real" if real_source_exists else "Synthetic"
    logger.info(f"Detected data source type: {data_source_type}")
    
    # 1. Apply Buffer
    gdf_buffered = apply_geodesic_buffer(df_survey, BUFFER_SIZE_KM)
    
    # 2. Save Intermediate Artifact: buffered_coordinates.geojson
    buffered_geojson_path = data_processed_dir / "buffered_coordinates.geojson"
    gdf_buffered.to_file(buffered_geojson_path, driver='GeoJSON')
    logger.info(f"Saved buffered coordinates to {buffered_geojson_path}")
    
    # 3. Extract NDVI (Spatial Join)
    df_joined = extract_ndvi_from_granules(gdf_buffered, synthetic_mode=(data_source_type == "Synthetic"))
    
    # 4. Verify Linkage
    df_final, validation_log = verify_linkage_and_trigger_aggregation(
        df_survey, df_joined, data_source_type
    )
    
    # 5. Save Outputs
    # Output: spatial_joined_data.csv
    output_csv_path = data_processed_dir / "spatial_joined_data.csv"
    write_csv_strict(df_final, output_csv_path)
    logger.info(f"Saved spatial joined data to {output_csv_path}")
    
    # Mandatory Output: linkage_validation.json
    validation_json_path = data_logs_dir / "linkage_validation.json"
    
    # Mandatory Text for Synthetic Mode
    if data_source_type == "Synthetic":
        validation_log["geospatial_fuzzing_note"] = f"Geospatial fuzzing radius: {BUFFER_SIZE_KM} km (Source: Assumption - Synthetic Data Mode)"
    
    write_json_strict(validation_log, validation_json_path)
    logger.info(f"Saved linkage validation to {validation_json_path}")
    
    # Return status for pipeline
    if validation_log["triggered_aggregation"]:
        logger.warning("Aggregation triggered. Proceeding to aggregation step.")
    else:
        logger.info("No aggregation triggered.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
