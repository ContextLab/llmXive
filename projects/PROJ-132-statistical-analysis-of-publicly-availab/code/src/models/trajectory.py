"""
Trajectory analysis module implementing Riemannian manifold statistics on the 2-sphere (S^2).

This module computes Fréchet means, geodesic distances, and trajectory shifts using
scipy and geopy, adhering to the constraint of not using geomstats.
"""
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from geopy.distance import geodesic
import pandas as pd

logger = logging.getLogger(__name__)

# Constants
EARTH_RADIUS_KM = 6371.0
CONVERGENCE_THRESHOLD = 1e-6
MAX_ITERATIONS = 100
LEARNING_RATE = 0.1

def lat_lon_to_cartesian(lat: float, lon: float) -> Tuple[float, float, float]:
    """
    Convert latitude and longitude (in degrees) to 3D Cartesian coordinates on unit sphere.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        
    Returns:
        Tuple of (x, y, z) coordinates
    """
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    x = math.cos(lat_rad) * math.cos(lon_rad)
    y = math.cos(lat_rad) * math.sin(lon_rad)
    z = math.sin(lat_rad)
    
    return (x, y, z)

def cartesian_to_lat_lon(x: float, y: float, z: float) -> Tuple[float, float]:
    """
    Convert 3D Cartesian coordinates to latitude and longitude (in degrees).
    
    Args:
        x, y, z: Cartesian coordinates
        
    Returns:
        Tuple of (latitude, longitude) in degrees
    """
    # Normalize to unit sphere
    r = math.sqrt(x*x + y*y + z*z)
    if r == 0:
        return (0.0, 0.0)
        
    x, y, z = x/r, y/r, z/r
    
    lat = math.degrees(math.asin(max(-1, min(1, z))))
    lon = math.degrees(math.atan2(y, x))
    
    return (lat, lon)

def geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute geodesic distance between two points on Earth in kilometers.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    return geodesic((lat1, lon1), (lat2, lon2)).km

def squared_geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute squared geodesic distance between two points on Earth.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Squared distance in km^2
    """
    dist = geodesic_distance(lat1, lon1, lat2, lon2)
    return dist * dist

def compute_frechet_mean(points: List[Tuple[float, float]], max_iter: int = MAX_ITERATIONS, 
                         tol: float = CONVERGENCE_THRESHOLD, eta: float = LEARNING_RATE) -> Tuple[float, float]:
    """
    Compute Fréchet mean on the 2-sphere using iterative gradient descent.
    
    The Fréchet mean minimizes the sum of squared geodesic distances to all points.
    Uses the exponential map for updates on the manifold.
    
    Args:
        points: List of (lat, lon) tuples
        max_iter: Maximum iterations
        tol: Convergence tolerance
        eta: Learning rate
        
    Returns:
        (lat, lon) of the Fréchet mean
    """
    if not points:
        raise ValueError("Cannot compute Fréchet mean of empty list")
        
    if len(points) == 1:
        return points[0]
        
    # Initialize mean as centroid (arithmetic mean projected to sphere)
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    
    # Simple initialization: use first point
    mu_lat, mu_lon = points[0]
    
    for iteration in range(max_iter):
        # Compute gradient of sum of squared distances
        gradient_lat = 0.0
        gradient_lon = 0.0
        
        for pt_lat, pt_lon in points:
            # Compute gradient of squared geodesic distance at mu
            # Gradient points in direction of pt with magnitude proportional to distance
            dist = geodesic_distance(mu_lat, mu_lon, pt_lat, pt_lon)
            
            if dist < 1e-10:
                continue
                
            # Direction from mu to pt (approximate on sphere)
            # Using great circle direction
            # For small distances, we can approximate gradient
            # Gradient of d^2(mu, p) = -2 * exp_mu^{-1}(p)
            
            # Compute bearing from mu to pt
            lat1_rad = math.radians(mu_lat)
            lat2_rad = math.radians(pt_lat)
            dlon_rad = math.radians(pt_lon - mu_lon)
            
            # Bearing calculation
            y = math.sin(dlon_rad) * math.cos(lat2_rad)
            x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
            bearing = math.atan2(y, x)
            
            # Gradient magnitude: -2 * dist (direction toward pt)
            grad_mag = -2.0 * dist
            
            # Update gradient components (approximate in local tangent plane)
            gradient_lat += grad_mag * math.cos(bearing)
            gradient_lon += grad_mag * math.sin(bearing) / max(abs(math.cos(math.radians(mu_lat))), 1e-10)
        
        # Update mean using exponential map approximation
        # For small steps, mu_new = mu + eta * gradient
        delta_lat = -eta * gradient_lat / len(points)
        delta_lon = -eta * gradient_lon / len(points)
        
        new_lat = mu_lat + delta_lat
        new_lon = mu_lon + delta_lon
        
        # Check convergence
        delta = math.sqrt(delta_lat**2 + delta_lon**2)
        
        mu_lat, mu_lon = new_lat, new_lon
        
        if delta < tol:
            logger.debug(f"Fréchet mean converged at iteration {iteration}")
            break
    
    return (mu_lat, mu_lon)

def compute_trajectory_shift(centroids_period1: List[Tuple[float, float]], 
                             centroids_period2: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Compute trajectory shift between two periods using Fréchet means.
    
    Args:
        centroids_period1: List of (lat, lon) centroids for period 1
        centroids_period2: List of (lat, lon) centroids for period 2
        
    Returns:
        Dictionary with shift_magnitude (km) and shift_direction (degrees)
    """
    if not centroids_period1 or not centroids_period2:
        raise ValueError("Cannot compute shift with empty centroid lists")
        
    # Compute Fréchet means for each period
    mean1 = compute_frechet_mean(centroids_period1)
    mean2 = compute_frechet_mean(centroids_period2)
    
    # Compute shift magnitude (geodesic distance)
    shift_magnitude = geodesic_distance(mean1[0], mean1[1], mean2[0], mean2[1])
    
    # Compute shift direction (bearing from mean1 to mean2)
    lat1_rad = math.radians(mean1[0])
    lat2_rad = math.radians(mean2[0])
    dlon_rad = math.radians(mean2[1] - mean1[1])
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    bearing = math.degrees(math.atan2(y, x))
    
    # Normalize bearing to [0, 360)
    if bearing < 0:
        bearing += 360.0
        
    return {
        "shift_magnitude": shift_magnitude,
        "shift_direction": bearing,
        "mean_period1_lat": mean1[0],
        "mean_period1_lon": mean1[1],
        "mean_period2_lat": mean2[0],
        "mean_period2_lon": mean2[1]
    }

def load_centroid_data(filepath: str) -> pd.DataFrame:
    """
    Load centroid data from JSON or CSV file.
    
    Args:
        filepath: Path to data file
        
    Returns:
        DataFrame with columns: species, year, week, lat, lon
    """
    path = Path(filepath)
    
    if path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def group_centroids_by_period(df: pd.DataFrame, period_col: str = 'year', 
                              species_col: str = 'species') -> Dict[str, Dict[str, List[Tuple[float, float]]]]:
    """
    Group centroids by species and time period for trajectory analysis.
    
    Args:
        df: DataFrame with centroid data
        period_col: Column name for time period
        species_col: Column name for species
        
    Returns:
        Nested dict: {species: {period: [(lat, lon), ...]}}
    """
    result = {}
    
    for species in df[species_col].unique():
        species_df = df[df[species_col] == species]
        result[species] = {}
        
        for period in species_df[period_col].unique():
            period_df = species_df[species_df[period_col] == period]
            centroids = list(zip(period_df['lat'].values, period_df['lon'].values))
            result[species][period] = centroids
            
    return result

def run_trajectory_analysis(input_path: str, output_path: str, 
                            period1: Any, period2: Any) -> None:
    """
    Run full trajectory analysis pipeline.
    
    Args:
        input_path: Path to input centroid data
        output_path: Path to output results JSON
        period1: Identifier for first period (e.g., year)
        period2: Identifier for second period (e.g., year)
    """
    logger.info(f"Running trajectory analysis from {input_path}")
    
    # Load data
    df = load_centroid_data(input_path)
    
    # Group by species and periods
    grouped = group_centroids_by_period(df)
    
    results = []
    
    for species, periods in grouped.items():
        if period1 not in periods or period2 not in periods:
            logger.warning(f"Skipping {species}: missing period data")
            continue
            
        try:
            shift = compute_trajectory_shift(
                periods[period1],
                periods[period2]
            )
            shift['species'] = species
            results.append(shift)
            logger.info(f"Computed shift for {species}: {shift['shift_magnitude']:.2f} km")
        except Exception as e:
            logger.error(f"Failed to compute shift for {species}: {e}")
            
    # Write results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results written to {output_path}")

def main():
    """Main entry point for trajectory analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run trajectory analysis on bird migration centroids')
    parser.add_argument('--input', type=str, required=True, help='Input centroid data file')
    parser.add_argument('--output', type=str, required=True, help='Output results file')
    parser.add_argument('--period1', type=str, default='2010', help='First period identifier')
    parser.add_argument('--period2', type=str, default='2020', help='Second period identifier')
    
    args = parser.parse_args()
    
    setup_logging = logging.getLogger(__name__)
    setup_logging.basicConfig(level=logging.INFO)
    
    run_trajectory_analysis(args.input, args.output, args.period1, args.period2)

if __name__ == '__main__':
    main()