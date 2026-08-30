import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_fixation_config() -> Dict[str, Any]:
    """Load fixation detection configuration from config.yaml.
    
    Returns:
        Dict containing fixation detection parameters.
    """
    config_path = get_project_root() / 'code' / 'config.yaml'
    if not config_path.exists():
        # Default configuration
        return {
            'ivt_duration_threshold': 100,  # ms
            'idt_dispersion_threshold': 30,  # pixels
            'algorithm': 'ivt'
        }
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('fixation_detection', {
            'ivt_duration_threshold': 100,
            'idt_dispersion_threshold': 30,
            'algorithm': 'ivt'
        })
    except Exception as e:
        logging.warning(f"Could not load fixation config: {e}. Using defaults.")
        return {
            'ivt_duration_threshold': 100,
            'idt_dispersion_threshold': 30,
            'algorithm': 'ivt'
        }

def calculate_velocity(gaze_df: pd.DataFrame) -> np.ndarray:
    """Calculate velocity between consecutive gaze points.
    
    Args:
        gaze_df: DataFrame with 'x', 'y', 'timestamp' columns.
        
    Returns:
        Array of velocities (pixels/ms). First element is 0.
    """
    if len(gaze_df) < 2:
        return np.zeros(len(gaze_df))
    
    x = gaze_df['x'].values
    y = gaze_df['y'].values
    timestamps = gaze_df['timestamp'].values
    
    # Calculate distances
    dx = np.diff(x)
    dy = np.diff(y)
    distances = np.sqrt(dx**2 + dy**2)
    
    # Calculate time differences
    dt = np.diff(timestamps).astype(float)
    dt[dt == 0] = 1e-6  # Avoid division by zero
    
    # Calculate velocities
    velocities = distances / dt
    
    # Prepend 0 for the first point
    return np.concatenate([[0], velocities])

def calculate_dispersion(points_x: List[float], points_y: List[float]) -> float:
    """Calculate dispersion (max distance between any two points) in a cluster.
    
    Args:
        points_x: List of x coordinates.
        points_y: List of y coordinates.
        
    Returns:
        Maximum Euclidean distance between any two points.
    """
    if len(points_x) < 2:
        return 0.0
    
    points = np.array(list(zip(points_x, points_y)))
    max_dist = 0.0
    
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dist = np.sqrt(np.sum((points[i] - points[j])**2))
            max_dist = max(max_dist, dist)
    
    return max_dist

def detect_fixations_ivt(
    gaze_df: pd.DataFrame,
    duration_threshold: float = 100,
    dispersion_threshold: float = 30
) -> List[Dict[str, Any]]:
    """Detect fixations using I-VT (Ivanchenko-Venice-Torino) algorithm.
    
    The I-VT algorithm groups consecutive gaze points that have low velocity
    (below a threshold) and high dispersion (above a threshold) into fixations.
    
    Args:
        gaze_df: DataFrame with 'x', 'y', 'timestamp' columns.
        duration_threshold: Minimum duration for a fixation in milliseconds.
        dispersion_threshold: Maximum dispersion for a fixation in pixels.
        
    Returns:
        List of fixation dictionaries with 'start_time', 'end_time', 'duration',
        'avg_x', 'avg_y', and 'dispersion' keys.
    """
    if len(gaze_df) == 0:
        return []
    
    # Calculate velocity
    velocities = calculate_velocity(gaze_df)
    
    # Identify potential fixation points (low velocity)
    # Using a simple threshold: velocity < 30 pixels/ms is considered a fixation
    velocity_threshold = 30
    is_fixation_point = velocities < velocity_threshold
    
    fixations = []
    current_fixation_indices = []
    
    for i in range(len(gaze_df)):
        if is_fixation_point.iloc[i] if isinstance(is_fixation_point, pd.Series) else is_fixation_point[i]:
            current_fixation_indices.append(i)
        else:
            # End of potential fixation
            if len(current_fixation_indices) >= 2:
                # Check if this cluster meets duration and dispersion criteria
                cluster_df = gaze_df.iloc[current_fixation_indices]
                duration = cluster_df['timestamp'].iloc[-1] - cluster_df['timestamp'].iloc[0]
                
                if duration >= duration_threshold:
                    points_x = cluster_df['x'].tolist()
                    points_y = cluster_df['y'].tolist()
                    dispersion = calculate_dispersion(points_x, points_y)
                    
                    if dispersion <= dispersion_threshold:
                        fixations.append({
                            'start_time': cluster_df['timestamp'].iloc[0],
                            'end_time': cluster_df['timestamp'].iloc[-1],
                            'duration': duration,
                            'avg_x': np.mean(points_x),
                            'avg_y': np.mean(points_y),
                            'dispersion': dispersion
                        })
            
            current_fixation_indices = []
    
    # Check if the last cluster is a fixation
    if len(current_fixation_indices) >= 2:
        cluster_df = gaze_df.iloc[current_fixation_indices]
        duration = cluster_df['timestamp'].iloc[-1] - cluster_df['timestamp'].iloc[0]
        
        if duration >= duration_threshold:
            points_x = cluster_df['x'].tolist()
            points_y = cluster_df['y'].tolist()
            dispersion = calculate_dispersion(points_x, points_y)
            
            if dispersion <= dispersion_threshold:
                fixations.append({
                    'start_time': cluster_df['timestamp'].iloc[0],
                    'end_time': cluster_df['timestamp'].iloc[-1],
                    'duration': duration,
                    'avg_x': np.mean(points_x),
                    'avg_y': np.mean(points_y),
                    'dispersion': dispersion
                })
    
    return fixations

def detect_fixations_idt(
    gaze_df: pd.DataFrame,
    dispersion_threshold: float = 30,
    duration_threshold: float = 100
) -> List[Dict[str, Any]]:
    """Detect fixations using I-DT (Ivanchenko-Duration-Threshold) algorithm.
    
    The I-DT algorithm groups consecutive gaze points that fall within a
    dispersion threshold into fixations.
    
    Args:
        gaze_df: DataFrame with 'x', 'y', 'timestamp' columns.
        dispersion_threshold: Maximum dispersion for a fixation in pixels.
        duration_threshold: Minimum duration for a fixation in milliseconds.
        
    Returns:
        List of fixation dictionaries.
    """
    if len(gaze_df) == 0:
        return []
    
    fixations = []
    current_cluster = [0]
    
    for i in range(1, len(gaze_df)):
        # Add current point to cluster
        current_cluster.append(i)
        
        # Check if cluster exceeds dispersion threshold
        cluster_df = gaze_df.iloc[current_cluster]
        points_x = cluster_df['x'].tolist()
        points_y = cluster_df['y'].tolist()
        dispersion = calculate_dispersion(points_x, points_y)
        
        if dispersion > dispersion_threshold:
            # Remove the last point and finalize the cluster
            current_cluster.pop()
            
            if len(current_cluster) >= 2:
                cluster_df = gaze_df.iloc[current_cluster]
                duration = cluster_df['timestamp'].iloc[-1] - cluster_df['timestamp'].iloc[0]
                
                if duration >= duration_threshold:
                    fixations.append({
                        'start_time': cluster_df['timestamp'].iloc[0],
                        'end_time': cluster_df['timestamp'].iloc[-1],
                        'duration': duration,
                        'avg_x': np.mean(cluster_df['x']),
                        'avg_y': np.mean(cluster_df['y']),
                        'dispersion': dispersion
                    })
            
            # Start new cluster with current point
            current_cluster = [i]
    
    # Check final cluster
    if len(current_cluster) >= 2:
        cluster_df = gaze_df.iloc[current_cluster]
        duration = cluster_df['timestamp'].iloc[-1] - cluster_df['timestamp'].iloc[0]
        points_x = cluster_df['x'].tolist()
        points_y = cluster_df['y'].tolist()
        dispersion = calculate_dispersion(points_x, points_y)
        
        if duration >= duration_threshold and dispersion <= dispersion_threshold:
            fixations.append({
                'start_time': cluster_df['timestamp'].iloc[0],
                'end_time': cluster_df['timestamp'].iloc[-1],
                'duration': duration,
                'avg_x': np.mean(cluster_df['x']),
                'avg_y': np.mean(cluster_df['y']),
                'dispersion': dispersion
            })
    
    return fixations

def process_gaze_data(
    gaze_df: pd.DataFrame,
    algorithm: str = 'ivt',
    **kwargs
) -> List[Dict[str, Any]]:
    """Process gaze data to detect fixations.
    
    Args:
        gaze_df: DataFrame with 'x', 'y', 'timestamp' columns.
        algorithm: Algorithm to use ('ivt' or 'idt').
        **kwargs: Additional parameters for the algorithm.
        
    Returns:
        List of fixation dictionaries.
    """
    config = load_fixation_config()
    
    if algorithm == 'ivt':
        duration_threshold = kwargs.get('duration_threshold', config.get('ivt_duration_threshold', 100))
        dispersion_threshold = kwargs.get('dispersion_threshold', config.get('idt_dispersion_threshold', 30))
        return detect_fixations_ivt(gaze_df, duration_threshold, dispersion_threshold)
    elif algorithm == 'idt':
        dispersion_threshold = kwargs.get('dispersion_threshold', config.get('idt_dispersion_threshold', 30))
        duration_threshold = kwargs.get('duration_threshold', config.get('ivt_duration_threshold', 100))
        return detect_fixations_idt(gaze_df, dispersion_threshold, duration_threshold)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Use 'ivt' or 'idt'.")

def main():
    """Main function for fixation detection."""
    logger = logging.getLogger(__name__)
    logger.info("Fixation detection module loaded successfully")
    
    # Example usage
    sample_data = pd.DataFrame({
        'x': [100, 102, 101, 100, 101],
        'y': [200, 201, 200, 199, 200],
        'timestamp': [1000, 1033, 1066, 1100, 1133]
    })
    
    fixations = process_gaze_data(sample_data, algorithm='ivt', duration_threshold=100, dispersion_threshold=30)
    logger.info(f"Detected {len(fixations)} fixations")
    
    for i, fixation in enumerate(fixations):
        logger.info(f"Fixation {i+1}: start={fixation['start_time']}, "
                   f"end={fixation['end_time']}, duration={fixation['duration']}ms")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()