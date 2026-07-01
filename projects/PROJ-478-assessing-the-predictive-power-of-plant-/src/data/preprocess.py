"""
Preprocessing utilities for spatial thinning and density-based background sampling.

Implements:
- Spatial thinning with configurable minimum distance (default 10 km, min 1 km).
- Density-based background sampling using exactly [deferred] points per species.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
import logging
import warnings

# Import logging utilities from existing project surface
from src.utils.logging import get_logger, log_provenance

# Import configuration constants
import src.utils.config as config

logger = get_logger(__name__)

# Constants
DEFAULT_THIN_DISTANCE_KM = 10.0
MIN_THIN_DISTANCE_KM = 1.0
EARTH_RADIUS_KM = 6371.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth (in km).
    
    Args:
        lat1, lon1: Coordinates of point 1 (degrees)
        lat2, lon2: Coordinates of point 2 (degrees)
        
    Returns:
        Distance in kilometers.
    """
    # Convert to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return EARTH_RADIUS_KM * c

def spatial_thinning(
    df: pd.DataFrame,
    min_distance_km: float = DEFAULT_THIN_DISTANCE_KM,
    species_col: str = 'species',
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform spatial thinning on occurrence records.
    
    Removes records that are closer than `min_distance_km` to any other record
    within the same species.
    
    Args:
        df: DataFrame with occurrence records.
        min_distance_km: Minimum distance in km between retained points.
                        Must be >= MIN_THIN_DISTANCE_KM.
        species_col: Column name for species identifier.
        lat_col: Column name for latitude.
        lon_col: Column name for longitude.
        seed: Random seed for reproducibility when breaking ties.
        
    Returns:
        DataFrame with thinned records.
        
    Raises:
        ValueError: If min_distance_km is below the minimum allowed threshold.
    """
    if min_distance_km < MIN_THIN_DISTANCE_KM:
        raise ValueError(
            f"Minimum distance {min_distance_km} km is below the allowed "
            f"minimum of {MIN_THIN_DISTANCE_KM} km."
        )
    
    if seed is not None:
        np.random.seed(seed)
    
    # Validate columns
    required_cols = [species_col, lat_col, lon_col]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with invalid coordinates
    valid_coords = df[lat_col].notna() & df[lon_col].notna()
    df_clean = df[valid_coords].copy()
    initial_count = len(df_clean)
    
    if initial_count == 0:
        logger.warning("No valid coordinates found for thinning.")
        return df_clean
    
    thinned_records = []
    
    # Process each species independently
    species_groups = df_clean.groupby(species_col)
    
    for species, group in species_groups:
        if len(group) == 1:
            thinned_records.append(group)
            continue
        
        # Reset index to ensure unique identifiers for this group
        group = group.reset_index(drop=True)
        kept_indices = []
        
        # Greedy thinning: iterate through points, keep if far enough from all kept
        for i, row in group.iterrows():
            lat_i, lon_i = row[lat_col], row[lon_col]
            
            # Check distance to all currently kept points for this species
            is_far_enough = True
            for kept_idx in kept_indices:
                kept_row = group.iloc[kept_idx]
                dist = haversine_distance(
                    lat_i, lon_i,
                    kept_row[lat_col], kept_row[lon_col]
                )
                if dist < min_distance_km:
                    is_far_enough = False
                    break
            
            if is_far_enough:
                kept_indices.append(i)
        
        if kept_indices:
            thinned_records.append(group.iloc[kept_indices])
    
    if not thinned_records:
        result = df_clean.iloc[0:0]  # Empty dataframe with same schema
    else:
        result = pd.concat(thinned_records, ignore_index=True)
    
    final_count = len(result)
    retention_rate = final_count / initial_count if initial_count > 0 else 0.0
    
    logger.info(
        f"Spatial thinning complete for {df_clean[species_col].nunique()} species. "
        f"Retained {final_count}/{initial_count} records ({retention_rate:.2%}). "
        f"Distance threshold: {min_distance_km} km."
    )
    
    # Log provenance
    log_provenance(
        operation="spatial_thinning",
        inputs={
            "initial_records": initial_count,
            "final_records": final_count,
            "min_distance_km": min_distance_km
        },
        outputs={
            "retention_rate": retention_rate
        }
    )
    
    return result

def generate_background_points(
    occurrence_df: pd.DataFrame,
    extent: Tuple[float, float, float, float],
    n_points: int,
    species_col: str = 'species',
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    density_weight: float = 1.0,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate density-based background points for a single species.
    
    Samples points within the bounding box of the occurrence data,
    weighted by the density of existing occurrences.
    
    Args:
        occurrence_df: DataFrame with occurrence records for ONE species.
        extent: Tuple (min_lon, max_lon, min_lat, max_lat) defining the sampling box.
        n_points: EXACT number of background points to generate.
        species_col: Column name for species identifier.
        lat_col: Column name for latitude.
        lon_col: Column name for longitude.
        density_weight: Weight factor for density-based sampling (higher = more clustered).
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with `n_points` background rows, including 'species' and coordinates.
        
    Raises:
        ValueError: If occurrence_df is empty or has no valid coordinates.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Validate input
    valid_coords = occurrence_df[lat_col].notna() & occurrence_df[lon_col].notna()
    df_valid = occurrence_df[valid_coords]
    
    if len(df_valid) == 0:
        raise ValueError("No valid occurrence records provided for background sampling.")
    
    min_lon, max_lon, min_lat, max_lat = extent
    
    # Create a grid for density estimation (kernel density estimation approximation)
    # We use a simple histogram-based density approach for efficiency
    grid_resolution = 50
    x_bins = np.linspace(min_lon, max_lon, grid_resolution + 1)
    y_bins = np.linspace(min_lat, max_lat, grid_resolution + 1)
    
    # Calculate density weights based on occurrence distribution
    hist, _, _ = np.histogram2d(
        df_valid[lon_col], df_valid[lat_col],
        bins=[x_bins, y_bins]
    )
    
    # Normalize and apply power law for density weighting
    hist = hist + 1e-6  # Avoid zero weights
    weights = hist ** density_weight
    weights = weights / weights.sum()
    
    # Sample grid cells based on weights
    grid_indices = np.random.choice(
        len(weights.flatten()),
        size=n_points,
        replace=True,
        p=weights.flatten()
    )
    
    # Convert grid indices to coordinates (center of the cell)
    grid_lons = []
    grid_lats = []
    
    for idx in grid_indices:
        row_idx = idx // (grid_resolution + 1)
        col_idx = idx % (grid_resolution + 1)
        
        # Center of the cell
        lon_center = (x_bins[col_idx] + x_bins[col_idx + 1]) / 2
        lat_center = (y_bins[row_idx] + y_bins[row_idx + 1]) / 2
        
        # Add small jitter to avoid exact grid alignment
        jitter_lon = np.random.uniform(
            -0.5 * (x_bins[1] - x_bins[0]),
            0.5 * (x_bins[1] - x_bins[0])
        )
        jitter_lat = np.random.uniform(
            -0.5 * (y_bins[1] - y_bins[0]),
            0.5 * (y_bins[1] - y_bins[0])
        )
        
        grid_lons.append(lon_center + jitter_lon)
        grid_lats.append(lat_center + jitter_lat)
    
    # Filter points that fall outside the extent (safety check)
    valid_mask = (
        (np.array(grid_lons) >= min_lon) & (np.array(grid_lons) <= max_lon) &
        (np.array(grid_lats) >= min_lat) & (np.array(grid_lats) <= max_lat)
    )
    
    grid_lons = [x for i, x in enumerate(grid_lons) if valid_mask[i]]
    grid_lats = [x for i, x in enumerate(grid_lats) if valid_mask[i]]
    
    # If we lost points due to edge effects, regenerate until we hit n_points
    while len(grid_lons) < n_points:
        needed = n_points - len(grid_lons)
        new_indices = np.random.choice(
            len(weights.flatten()),
            size=needed,
            replace=True,
            p=weights.flatten()
        )
        for idx in new_indices:
            row_idx = idx // (grid_resolution + 1)
            col_idx = idx % (grid_resolution + 1)
            lon_center = (x_bins[col_idx] + x_bins[col_idx + 1]) / 2
            lat_center = (y_bins[row_idx] + y_bins[row_idx + 1]) / 2
            jitter_lon = np.random.uniform(
                -0.5 * (x_bins[1] - x_bins[0]),
                0.5 * (x_bins[1] - x_bins[0])
            )
            jitter_lat = np.random.uniform(
                -0.5 * (y_bins[1] - y_bins[0]),
                0.5 * (y_bins[1] - y_bins[0])
            )
            new_lon = lon_center + jitter_lon
            new_lat = lat_center + jitter_lat
            if (min_lon <= new_lon <= max_lon) and (min_lat <= new_lat <= max_lat):
                grid_lons.append(new_lon)
                grid_lats.append(new_lat)
    
    # Create the background DataFrame
    background_df = pd.DataFrame({
        'species': [df_valid[species_col].iloc[0]] * n_points,
        lat_col: grid_lats[:n_points],
        lon_col: grid_lons[:n_points],
        'presence': [0] * n_points  # 0 indicates background/absence
    })
    
    logger.info(
        f"Generated {n_points} density-based background points for species "
        f"{df_valid[species_col].iloc[0]}."
    )
    
    log_provenance(
        operation="background_sampling",
        inputs={
            "species": df_valid[species_col].iloc[0],
            "n_occurrences": len(df_valid),
            "n_points_requested": n_points,
            "density_weight": density_weight
        },
        outputs={
            "n_points_generated": n_points
        }
    )
    
    return background_df

def preprocess_species_data(
    df: pd.DataFrame,
    min_distance_km: float = DEFAULT_THIN_DISTANCE_KM,
    n_background_points: int = 10000,
    species_col: str = 'species',
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    End-to-end preprocessing for a single species dataset.
    
    1. Spatial thinning of occurrence records.
    2. Generation of density-based background points.
    3. Merging occurrence and background data.
    
    Args:
        df: DataFrame with occurrence records (must contain at least one species).
        min_distance_km: Minimum distance for spatial thinning (km).
        n_background_points: EXACT number of background points to generate per species.
        species_col: Column name for species identifier.
        lat_col: Column name for latitude.
        lon_col: Column name for longitude.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (processed_df, stats_dict):
            - processed_df: Combined occurrence (presence=1) and background (presence=0) data.
            - stats_dict: Dictionary with thinning and sampling statistics.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Validate input
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    valid_coords = df[lat_col].notna() & df[lon_col].notna()
    df_valid = df[valid_coords].copy()
    
    if df_valid.empty:
        raise ValueError("No valid coordinates in input DataFrame.")
    
    stats = {
        "species": df_valid[species_col].iloc[0],
        "initial_records": len(df_valid),
        "thinned_records": 0,
        "background_points": 0,
        "total_final_records": 0
    }
    
    # Step 1: Spatial thinning
    thinned_df = spatial_thinning(
        df_valid,
        min_distance_km=min_distance_km,
        species_col=species_col,
        lat_col=lat_col,
        lon_col=lon_col,
        seed=seed
    )
    stats["thinned_records"] = len(thinned_df)
    
    # Step 2: Generate background points
    # Calculate extent from thinned data
    min_lon = thinned_df[lon_col].min()
    max_lon = thinned_df[lon_col].max()
    min_lat = thinned_df[lat_col].min()
    max_lat = thinned_df[lat_col].max()
    
    # Expand extent by 10% to ensure coverage
    lon_range = max_lon - min_lon
    lat_range = max_lat - min_lat
    extent = (
        min_lon - 0.1 * lon_range,
        max_lon + 0.1 * lon_range,
        min_lat - 0.1 * lat_range,
        max_lat + 0.1 * lat_range
    )
    
    try:
        background_df = generate_background_points(
            thinned_df,
            extent=extent,
            n_points=n_background_points,
            species_col=species_col,
            lat_col=lat_col,
            lon_col=lon_col,
            seed=seed
        )
    except ValueError as e:
        logger.error(f"Failed to generate background points: {e}")
        background_df = pd.DataFrame(columns=[species_col, lat_col, lon_col, 'presence'])
    
    stats["background_points"] = len(background_df)
    
    # Step 3: Prepare occurrence data (presence=1)
    occurrence_df = thinned_df.copy()
    occurrence_df['presence'] = 1
    
    # Step 4: Combine
    if background_df.empty:
        processed_df = occurrence_df
    else:
        processed_df = pd.concat([occurrence_df, background_df], ignore_index=True)
    
    stats["total_final_records"] = len(processed_df)
    
    logger.info(
        f"Preprocessing complete for {stats['species']}: "
        f"{stats['thinned_records']} thinned occurrences + "
        f"{stats['background_points']} background points = "
        f"{stats['total_final_records']} total records."
    )
    
    return processed_df, stats

# Placeholder for the [deferred] points requirement
# The actual value should be injected via configuration or command line arguments
# when this module is used in the full pipeline.
# For now, we use a default that satisfies the "exactly [deferred] points" requirement
# by making it a parameter with a default value that the calling code must override.
DEFAULT_BACKGROUND_POINTS = 10000  # This is a placeholder; replace with actual [deferred] value

if __name__ == "__main__":
    # Example usage for testing (requires real data)
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess species occurrence data.")
    parser.add_argument("--input", required=True, help="Path to input CSV with occurrences.")
    parser.add_argument("--output", required=True, help="Path to output CSV.")
    parser.add_argument("--distance", type=float, default=DEFAULT_THIN_DISTANCE_KM,
                        help="Minimum distance for thinning (km).")
    parser.add_argument("--background", type=int, default=DEFAULT_BACKGROUND_POINTS,
                        help="Number of background points to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    
    args = parser.parse_args()
    
    # Load real data
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
        exit(1)
    
    # Process
    processed_df, stats = preprocess_species_data(
        df,
        min_distance_km=args.distance,
        n_background_points=args.background,
        seed=args.seed
    )
    
    # Save
    processed_df.to_csv(args.output, index=False)
    print(f"Saved {len(processed_df)} records to {args.output}")
    print(f"Stats: {stats}")
