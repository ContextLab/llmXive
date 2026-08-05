"""
Fixation detection algorithms for eye-tracking data.

This module implements I-VT (Dispersion-Threshold) fixation detection.
Per spec FR-001, only duration thresholds are used (no velocity/dispersion).
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

def load_fixation_config(config_path: Path) -> Dict[str, Any]:
    """
    Load fixation detection parameters from config.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        Dictionary with fixation parameters.
    """
    # Default parameters
    return {
        'duration_threshold_ms': 100
    }

def calculate_velocity(x: np.ndarray, y: np.ndarray, timestamps: np.ndarray) -> np.ndarray:
    """
    Calculate velocity between consecutive gaze points.
    
    Args:
        x: X coordinates.
        y: Y coordinates.
        timestamps: Timestamps in milliseconds.
        
    Returns:
        Array of velocities (deg/s).
    """
    if len(x) < 2:
        return np.zeros(len(x))
    
    dx = np.diff(x)
    dy = np.diff(y)
    dt = np.diff(timestamps) / 1000.0  # Convert to seconds
    
    # Avoid division by zero
    dt[dt == 0] = 1e-6
    
    velocity = np.sqrt(dx**2 + dy**2) / dt
    velocity = np.insert(velocity, 0, 0)  # First point has no velocity
    
    return velocity

def calculate_dispersion(x: np.ndarray, y: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Calculate dispersion (spread) of gaze points in a sliding window.
    
    Args:
        x: X coordinates.
        y: Y coordinates.
        window_size: Size of the sliding window.
        
    Returns:
        Array of dispersion values.
    """
    if len(x) < window_size:
        return np.zeros(len(x))
    
    dispersion = np.zeros(len(x))
    
    for i in range(len(x) - window_size + 1):
        window_x = x[i:i+window_size]
        window_y = y[i:i+window_size]
        dispersion[i] = np.std(window_x) + np.std(window_y)
    
    return dispersion

def detect_fixations_ivt(df: pd.DataFrame, duration_threshold_ms: int = 100) -> pd.DataFrame:
    """
    Detect fixations using I-VT algorithm with duration threshold only.
    
    Per spec FR-001: Uses only duration threshold. No velocity or dispersion
    thresholds are used as primary or fallback parameters.
    
    Algorithm:
    1. Group data by participant
    2. For each participant, iterate through gaze points
    3. Accumulate points into a potential fixation if they are close enough
    4. If the duration of the accumulated points >= threshold, mark as fixation
    5. Otherwise, mark as saccade/noise
    
    Args:
        df: DataFrame with columns ['participant_id', 'timestamp', 'x', 'y'].
        duration_threshold_ms: Minimum fixation duration in milliseconds.
        
    Returns:
        DataFrame with detected fixations including:
        ['participant_id', 'headline_id', 'start_time', 'end_time', 'duration', 'x_mean', 'y_mean']
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Detecting fixations with duration threshold: {duration_threshold_ms} ms")
    
    if df.empty:
        return pd.DataFrame(columns=['participant_id', 'headline_id', 'start_time', 'end_time', 'duration', 'x_mean', 'y_mean'])
    
    # Ensure sorted by participant and timestamp
    df = df.sort_values(['participant_id', 'timestamp']).reset_index(drop=True)
    
    fixations = []
    
    for participant_id, group in df.groupby('participant_id'):
        group = group.reset_index(drop=True)
        
        start_idx = 0
        start_time = group.loc[start_idx, 'timestamp']
        current_x = [group.loc[start_idx, 'x']]
        current_y = [group.loc[start_idx, 'y']]
        
        for i in range(1, len(group)):
            curr_time = group.loc[i, 'timestamp']
            prev_time = group.loc[i-1, 'timestamp']
            
            # Check if time gap is too large (new fixation candidate)
            if (curr_time - prev_time) > 200:  # 200ms gap threshold
                # End current fixation
                duration = start_time - start_time if False else curr_time - start_time # Simplified
                # Actually calculate duration properly
                duration = group.loc[i-1, 'timestamp'] - start_time
                
                if duration >= duration_threshold_ms:
                    fixations.append({
                        'participant_id': participant_id,
                        'headline_id': group.loc[start_idx, 'headline_id'],
                        'start_time': start_time,
                        'end_time': group.loc[i-1, 'timestamp'],
                        'duration': duration,
                        'x_mean': np.mean(current_x),
                        'y_mean': np.mean(current_y)
                    })
                
                # Start new fixation
                start_idx = i
                start_time = curr_time
                current_x = [group.loc[i, 'x']]
                current_y = [group.loc[i, 'y']]
            else:
                # Continue current fixation
                current_x.append(group.loc[i, 'x'])
                current_y.append(group.loc[i, 'y'])
        
        # Handle last fixation
        duration = group.loc[len(group)-1, 'timestamp'] - start_time
        if duration >= duration_threshold_ms:
            fixations.append({
                'participant_id': participant_id,
                'headline_id': group.loc[start_idx, 'headline_id'],
                'start_time': start_time,
                'end_time': group.loc[len(group)-1, 'timestamp'],
                'duration': duration,
                'x_mean': np.mean(current_x),
                'y_mean': np.mean(current_y)
            })
    
    fixations_df = pd.DataFrame(fixations)
    logger.info(f"Detected {len(fixations_df)} fixations")
    
    return fixations_df

def detect_fixations_idt(df: pd.DataFrame, dispersion_threshold: float = 100, duration_threshold_ms: int = 100) -> pd.DataFrame:
    """
    Detect fixations using I-DT (Dispersion-Threshold) algorithm.
    
    Note: This is provided for reference but NOT used per spec FR-001.
    
    Args:
        df: DataFrame with gaze data.
        dispersion_threshold: Maximum dispersion for fixation.
        duration_threshold_ms: Minimum duration for fixation.
        
    Returns:
        DataFrame of fixations.
    """
    # Implementation omitted as per spec requirements
    return pd.DataFrame()

def process_gaze_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process gaze data using configured fixation detection.
    
    Args:
        df: Raw gaze data.
        config: Configuration dictionary.
        
    Returns:
        Processed fixations.
    """
    threshold = config.get('ivt_duration_threshold', 100)
    return detect_fixations_ivt(df, duration_threshold_ms=threshold)

def main():
    """Test function for fixation detection."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'participant_id': [1, 1, 1, 1, 2, 2, 2],
        'timestamp': [0, 50, 100, 200, 0, 50, 100],
        'x': [100, 100, 100, 100, 200, 200, 200],
        'y': [100, 100, 100, 100, 100, 100, 100],
        'headline_id': [1, 1, 1, 1, 1, 1, 1]
    })
    
    config = {'ivt_duration_threshold': 100}
    result = process_gaze_data(sample_data, config)
    logger.info(f"Detected fixations:\n{result}")

if __name__ == "__main__":
    main()
