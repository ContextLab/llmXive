"""
Trajectory analysis module for bird migration patterns.

Implements functions to compute weekly migration centroids,
geodesic distances, and trajectory shifts using great-circle geometry.
"""
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import polars as pl

# Configure logging
logger = logging.getLogger(__name__)

# Constants
EARTH_RADIUS_KM = 6371.0
WEEKS_IN_YEAR = 52

def lat_lon_to_cartesian(lat: float, lon: float) -> Tuple[float, float, float]:
    """
    Convert latitude/longitude to 3D Cartesian coordinates on unit sphere.
    
    Args:
        lat: Latitude in degrees (-90 to 90)
        lon: Longitude in degrees (-180 to 180)
        
    Returns:
        Tuple of (x, y, z) Cartesian coordinates
    """
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    x = math.cos(lat_rad) * math.cos(lon_rad)
    y = math.cos(lat_rad) * math.sin(lon_rad)
    z = math.sin(lat_rad)
    
    return (x, y, z)

def cartesian_to_lat_lon(x: float, y: float, z: float) -> Tuple[float, float]:
    """
    Convert 3D Cartesian coordinates back to latitude/longitude.
    
    Args:
        x, y, z: Cartesian coordinates
        
    Returns:
        Tuple of (latitude, longitude) in degrees
    """
    lat_rad = math.asin(z)
    lon_rad = math.atan2(y, x)
    
    return (math.degrees(lat_rad), math.degrees(lon_rad))

def geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula for numerical stability.
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
        
    Returns:
        Distance in kilometers
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c

def squared_geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the squared great-circle distance between two points.
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
        
    Returns:
        Squared distance in km^2
    """
    dist = geodesic_distance(lat1, lon1, lat2, lon2)
    return dist * dist

def compute_frechet_mean(centroids: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Compute the Fréchet mean (geodesic mean) of a set of latitude/longitude points.
    
    The Fréchet mean on a sphere is found by converting to 3D Cartesian coordinates,
    computing the arithmetic mean, and projecting back to the sphere.
    
    Args:
        centroids: List of (lat, lon) tuples in degrees
        
    Returns:
        Tuple of (mean_lat, mean_lon) in degrees
    """
    if not centroids:
        raise ValueError("Cannot compute mean of empty centroid list")
    
    # Convert to Cartesian coordinates
    cartesian_points = [lat_lon_to_cartesian(lat, lon) for lat, lon in centroids]
    
    # Compute arithmetic mean in 3D
    x_mean = sum(p[0] for p in cartesian_points) / len(cartesian_points)
    y_mean = sum(p[1] for p in cartesian_points) / len(cartesian_points)
    z_mean = sum(p[2] for p in cartesian_points) / len(cartesian_points)
    
    # Normalize to unit sphere
    magnitude = math.sqrt(x_mean**2 + y_mean**2 + z_mean**2)
    if magnitude < 1e-10:
        # Handle edge case where points cancel out (antipodal)
        logger.warning("Centroids nearly cancel out; returning origin")
        return (0.0, 0.0)
    
    x_mean /= magnitude
    y_mean /= magnitude
    z_mean /= magnitude
    
    # Convert back to lat/lon
    return cartesian_to_lat_lon(x_mean, y_mean, z_mean)

def compute_trajectory_shift(
    trajectory1: List[Tuple[float, float]],
    trajectory2: List[Tuple[float, float]]
) -> Dict[str, Any]:
    """
    Compute the shift between two trajectories.
    
    Args:
        trajectory1: First trajectory as list of (lat, lon) tuples
        trajectory2: Second trajectory as list of (lat, lon) tuples
        
    Returns:
        Dictionary with shift magnitude (km), direction (degrees from north),
        and per-point displacements
    """
    if len(trajectory1) != len(trajectory2):
        raise ValueError("Trajectories must have same length")
    
    if len(trajectory1) == 0:
        return {
            "magnitude": 0.0,
            "direction": 0.0,
            "displacements": []
        }
    
    displacements = []
    total_vector_x = 0.0
    total_vector_y = 0.0
    
    for (lat1, lon1), (lat2, lon2) in zip(trajectory1, trajectory2):
        dist = geodesic_distance(lat1, lon1, lat2, lon2)
        
        # Calculate direction (bearing) from point 1 to point 2
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        bearing = math.degrees(math.atan2(y, x))
        if bearing < 0:
            bearing += 360
        
        displacements.append({
            "distance_km": dist,
            "bearing_deg": bearing
        })
        
        # Accumulate for average shift vector
        total_vector_x += dist * math.cos(math.radians(bearing))
        total_vector_y += dist * math.sin(math.radians(bearing))
    
    # Compute average shift
    avg_magnitude = math.sqrt(total_vector_x**2 + total_vector_y**2) / len(trajectory1)
    avg_direction = math.degrees(math.atan2(total_vector_y, total_vector_x))
    if avg_direction < 0:
        avg_direction += 360
    
    return {
        "magnitude": avg_magnitude,
        "direction": avg_direction,
        "displacements": displacements
    }

def load_centroid_data(input_path: str) -> pl.DataFrame:
    """
    Load centroid data from a parquet file.
    
    Args:
        input_path: Path to the parquet file
        
    Returns:
        Polars DataFrame with centroid data
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Centroid data file not found: {input_path}")
    
    df = pl.read_parquet(input_path)
    required_cols = ["species", "year", "week", "lat", "lon"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def group_centroids_by_period(
    df: pl.DataFrame,
    species: str,
    year: int
) -> List[Tuple[float, float]]:
    """
    Group centroids by species and year, returning weekly centroids in order.
    
    Args:
        df: DataFrame with species, year, week, lat, lon columns
        species: Species name to filter
        year: Year to filter
        
    Returns:
        List of (lat, lon) tuples ordered by week
    """
    filtered = df.filter(
        (pl.col("species") == species) & (pl.col("year") == year)
    ).sort("week")
    
    centroids = list(zip(filtered["lat"].to_list(), filtered["lon"].to_list()))
    return centroids

def compute_weekly_centroids(
    input_path: str,
    output_path: str,
    grid_resolution: float = 0.5
) -> Dict[str, Any]:
    """
    Compute weekly migration centroids from preprocessed observations.
    
    Aggregates observations per species-year per week, calculating the
    geodesic (great-circle) mean latitude/longitude for each week.
    
    Args:
        input_path: Path to preprocessed data parquet file
        output_path: Path to write weekly centroids parquet file
        grid_resolution: Grid resolution in degrees (for reference)
        
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Computing weekly centroids from {input_path}")
    
    # Load preprocessed data
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pl.read_parquet(input_path)
    
    required_cols = ["species", "year", "week", "lat", "lon"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input: {missing}")
    
    logger.info(f"Loaded {len(df)} records")
    
    # Filter out invalid coordinates
    df = df.filter(
        (pl.col("lat").is_not_null()) &
        (pl.col("lon").is_not_null()) &
        (pl.col("lat") >= -90) &
        (pl.col("lat") <= 90) &
        (pl.col("lon") >= -180) &
        (pl.col("lon") <= 180)
    )
    
    logger.info(f"Filtered to {len(df)} valid records")
    
    # Group by species, year, week and compute geodesic mean
    centroids_data = []
    
    # Get unique species-year-week combinations
    groups = df.group_by(["species", "year", "week"]).agg(
        [
            pl.col("lat").alias("lat_list"),
            pl.col("lon").alias("lon_list")
        ]
    )
    
    for row in groups.iter_rows(named=True):
        species = row["species"]
        year = row["year"]
        week = row["week"]
        lats = row["lat_list"]
        lons = row["lon_list"]
        
        if len(lats) == 0 or len(lons) == 0:
            continue
        
        # Compute geodesic mean
        centroids = list(zip(lats, lons))
        mean_lat, mean_lon = compute_frechet_mean(centroids)
        
        centroids_data.append({
            "species": species,
            "year": year,
            "week": week,
            "lat": mean_lat,
            "lon": mean_lon,
            "observation_count": len(lats)
        })
    
    # Create output DataFrame
    result_df = pl.DataFrame(centroids_data)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to parquet
    result_df.write_parquet(output_path)
    
    stats = {
        "total_centroids": len(result_df),
        "unique_species": result_df["species"].n_unique(),
        "unique_years": result_df["year"].n_unique(),
        "output_path": str(output_path)
    }
    
    logger.info(f"Computed {stats['total_centroids']} weekly centroids")
    logger.info(f"Output written to {output_path}")
    
    return stats

def run_trajectory_analysis(
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run full trajectory analysis including centroid computation and shift detection.
    
    Args:
        input_path: Path to preprocessed data
        output_path: Path to write trajectory results
        
    Returns:
        Dictionary with analysis results
    """
    # First compute weekly centroids
    centroid_path = str(Path(output_path).parent / "weekly_centroids.parquet")
    centroid_stats = compute_weekly_centroids(input_path, centroid_path)
    
    # Load centroids
    centroids_df = load_centroid_data(centroid_path)
    
    # Compute shifts between years for each species
    results = []
    
    species_list = centroids_df["species"].unique().to_list()
    years = sorted(centroids_df["year"].unique().to_list())
    
    for species in species_list:
        for i in range(len(years) - 1):
            year1 = years[i]
            year2 = years[i + 1]
            
            traj1 = group_centroids_by_period(centroids_df, species, year1)
            traj2 = group_centroids_by_period(centroids_df, species, year2)
            
            if len(traj1) == 0 or len(traj2) == 0:
                continue
            
            shift = compute_trajectory_shift(traj1, traj2)
            
            results.append({
                "species": species,
                "year_from": year1,
                "year_to": year2,
                "shift_magnitude": shift["magnitude"],
                "shift_direction": shift["direction"],
                "centroid_count": len(traj1)
            })
    
    # Write results
    result_df = pl.DataFrame(results)
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    result_df.write_parquet(output_path)
    
    return {
        "centroids": centroid_stats,
        "shifts_computed": len(results),
        "output_path": str(output_path)
    }

def main():
    """Main entry point for trajectory analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute weekly migration centroids")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to preprocessed data parquet file"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write weekly centroids parquet file"
    )
    parser.add_argument(
        "--grid-res",
        type=float,
        default=0.5,
        help="Grid resolution in degrees"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        stats = compute_weekly_centroids(
            args.input,
            args.output,
            args.grid_res
        )
        print(json.dumps(stats, indent=2))
    except Exception as e:
        logger.error(f"Error computing centroids: {e}")
        raise

if __name__ == "__main__":
    main()
