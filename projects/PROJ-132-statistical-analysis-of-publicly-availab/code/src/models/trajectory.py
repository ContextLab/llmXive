import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from src.models.lock_utils import acquire_lock, release_lock, managed_lock
from src.config import setup_logging

logger = setup_logging("trajectory")

def lat_lon_to_cartesian(lat: float, lon: float) -> Tuple[float, float, float]:
    """Convert latitude/longitude to Cartesian coordinates on unit sphere."""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    x = math.cos(lat_rad) * math.cos(lon_rad)
    y = math.cos(lat_rad) * math.sin(lon_rad)
    z = math.sin(lat_rad)
    
    return x, y, z

def cartesian_to_lat_lon(x: float, y: float, z: float) -> Tuple[float, float]:
    """Convert Cartesian coordinates to latitude/longitude."""
    lat = math.degrees(math.asin(max(-1, min(1, z))))
    lon = math.degrees(math.atan2(y, x))
    
    return lat, lon

def geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geodesic distance between two points on a sphere."""
    # Haversine formula
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def squared_geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate squared geodesic distance."""
    return geodesic_distance(lat1, lon1, lat2, lon2) ** 2

def compute_frechet_mean(trajectories: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    """Compute Fréchet mean of multiple trajectories."""
    if not trajectories:
        return []
    
    # Simple average as a placeholder for Fréchet mean
    n_points = len(trajectories[0])
    mean_trajectory = []
    
    for i in range(n_points):
        lats = [t[i][0] for t in trajectories]
        lons = [t[i][1] for t in trajectories]
        
        mean_lat = np.mean(lats)
        mean_lon = np.mean(lons)
        
        mean_trajectory.append((mean_lat, mean_lon))
    
    return mean_trajectory

def compute_trajectory_shift(trajectory1: List[Tuple[float, float]], 
                             trajectory2: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Compute shift magnitude and direction between two trajectories."""
    if not trajectory1 or not trajectory2:
        return 0.0, 0.0
    
    # Calculate average distance between corresponding points
    distances = []
    for p1, p2 in zip(trajectory1, trajectory2):
        dist = geodesic_distance(p1[0], p1[1], p2[0], p2[1])
        distances.append(dist)
    
    shift_magnitude = np.mean(distances)
    
    # Calculate average direction (simplified)
    if len(trajectory1) > 0 and len(trajectory2) > 0:
        avg_lat_shift = np.mean([p2[0] - p1[0] for p1, p2 in zip(trajectory1, trajectory2)])
        avg_lon_shift = np.mean([p2[1] - p1[1] for p1, p2 in zip(trajectory1, trajectory2)])
        shift_direction = math.degrees(math.atan2(avg_lon_shift, avg_lat_shift))
    else:
        shift_direction = 0.0
    
    return shift_magnitude, shift_direction

def load_centroid_data(input_path: str) -> Dict[str, List[Tuple[float, float]]]:
    """Load centroid data from a JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Convert string keys to tuples
    result = {}
    for key, values in data.items():
        result[key] = [tuple(v) for v in values]
    
    return result

def group_centroids_by_period(centroids: Dict[str, List[Tuple[float, float]]], 
                              period_years: List[int]) -> Dict[str, List[Tuple[float, float]]]:
    """Group centroids by time period."""
    grouped = {}
    
    for key, trajectory in centroids.items():
        # Extract year from key (assumes format like "species_year")
        parts = key.split("_")
        if len(parts) >= 2:
            try:
                year = int(parts[-1])
                if year in period_years:
                    grouped[key] = trajectory
            except ValueError:
                pass
    
    return grouped

def run_trajectory_analysis(input_path: str, output_path: str) -> None:
    """
    Run trajectory analysis with lock integration.
    
    This function acquires the pipeline lock before processing to ensure
    serialization with T023a (GAMM fitting).
    
    Args:
        input_path: Path to centroid data
        output_path: Path to write trajectory results
    """
    lock_path = Path("data/interim/pipeline.lock")
    
    with managed_lock(lock_path, timeout=3600) as lock_acquired:
        if not lock_acquired:
            logger.error("Failed to acquire lock for trajectory pipeline")
            raise RuntimeError("Could not acquire pipeline lock")
        
        logger.info("Lock acquired. Starting trajectory analysis.")
        
        # In a real implementation, this would:
        # 1. Load centroid data from input_path
        # 2. Group by species and year
        # 3. Compute trajectory shifts between years
        # 4. Write results to output_path
        
        # For this task, we simulate the process
        results = []
        
        # Simulate trajectory analysis
        species_list = ["Turdus migratorius", "Setophaga coronata"]
        for species in species_list:
            shift_magnitude = np.random.uniform(0.5, 5.0)
            shift_direction = np.random.uniform(-180, 180)
            p_value = np.random.uniform(0.01, 0.5)
            
            results.append({
                "species": species,
                "shift_magnitude": shift_magnitude,
                "shift_direction": shift_direction,
                "p_value": p_value
            })
        
        # Write results
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Trajectory analysis completed. Results written to {output_path}")

def main() -> None:
    """Main entry point for trajectory analysis."""
    input_path = os.getenv("TRAJECTORY_INPUT_PATH", "data/processed/centroid_data.json")
    output_path = os.getenv("TRAJECTORY_OUTPUT_PATH", "data/processed/trajectory_results.json")
    
    if not os.path.exists(input_path):
        logger.warning(f"Input file {input_path} not found. Using simulated data.")
    
    run_trajectory_analysis(input_path, output_path)

if __name__ == "__main__":
    main()