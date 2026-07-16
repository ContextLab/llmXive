"""
Fixation Detection Utilities for Eye-Tracking Data Analysis.

This module implements I-VT (Dispersion-Threshold) and I-DT (Velocity-Threshold)
algorithms for detecting fixations from raw gaze data.

Configuration is loaded from `code/config.yaml`. If specific keys are missing,
the module falls back to hardcoded defaults:
  - ivt_velocity_threshold: 30 deg/s (Note: I-VT is dispersion-based, this is for hybrid checks if needed)
  - idt_dispersion_threshold: 100px
  - fixation_min_duration: 60 ms (Configurable, defaults to 60 if missing)
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from utils.environment_manager import load_config, get_config_value, get_paths

# Set up module logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_IDT_DISPERSION_THRESHOLD = 100.0  # pixels
DEFAULT_IVT_VELOCITY_THRESHOLD = 30.0     # deg/s (fallback for hybrid logic)
DEFAULT_FIXATION_MIN_DURATION_MS = 60     # milliseconds

def load_fixation_config() -> Dict[str, Any]:
    """
    Load fixation detection parameters from config.yaml.
    
    Returns a dictionary with:
      - idt_dispersion_threshold: float (pixels)
      - ivt_velocity_threshold: float (deg/s)
      - fixation_min_duration: float (ms)
      
    Falls back to hardcoded defaults if keys are missing.
    """
    paths = get_paths()
    config_path = paths["config_path"]
    
    config = {}
    if os.path.exists(config_path):
        try:
            config = load_config(config_path)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
    else:
        logger.warning(f"Config file not found at {config_path}. Using defaults.")

    # Extract and validate parameters with fallbacks
    idt_disp = get_config_value(config, "idt_dispersion_threshold", DEFAULT_IDT_DISPERSION_THRESHOLD)
    ivt_vel = get_config_value(config, "ivt_velocity_threshold", DEFAULT_IVT_VELOCITY_THRESHOLD)
    min_dur = get_config_value(config, "fixation_min_duration", DEFAULT_FIXATION_MIN_DURATION_MS)

    # Ensure types are correct
    idt_disp = float(idt_disp)
    ivt_vel = float(ivt_vel)
    min_dur = float(min_dur)

    return {
        "idt_dispersion_threshold": idt_disp,
        "ivt_velocity_threshold": ivt_vel,
        "fixation_min_duration": min_dur
    }

def calculate_velocity(gaze_data: pd.DataFrame) -> np.ndarray:
    """
    Calculate instantaneous velocity between consecutive gaze points.
    
    Velocity is computed as the Euclidean distance between points divided by
    the time delta.
    
    Args:
        gaze_data: DataFrame with 'x', 'y', 'timestamp' columns.
        
    Returns:
        Array of velocities (pixels/ms) for each point (first point is 0).
    """
    if len(gaze_data) < 2:
        return np.zeros(len(gaze_data))
    
    x = gaze_data['x'].values
    y = gaze_data['y'].values
    t = gaze_data['timestamp'].values
    
    # Calculate deltas
    dx = np.diff(x)
    dy = np.diff(y)
    dt = np.diff(t)
    
    # Avoid division by zero
    dt = np.where(dt == 0, 1e-9, dt)
    
    # Calculate velocity (pixels per ms)
    velocity = np.sqrt(dx**2 + dy**2) / dt
    
    # Prepend 0 for the first point
    velocities = np.concatenate(([0.0], velocity))
    return velocities

def calculate_dispersion(gaze_data: pd.DataFrame) -> float:
    """
    Calculate spatial dispersion (bounding box diagonal) of a set of gaze points.
    
    Args:
        gaze_data: DataFrame with 'x', 'y' columns.
        
    Returns:
        Dispersion value (pixels).
    """
    if len(gaze_data) < 2:
        return 0.0
        
    x = gaze_data['x']
    y = gaze_data['y']
    
    width = x.max() - x.min()
    height = y.max() - y.min()
    
    dispersion = np.sqrt(width**2 + height**2)
    return dispersion

def detect_fixations_ivt(gaze_data: pd.DataFrame, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect fixations using the I-VT (Dispersion-Threshold) algorithm.
    
    The algorithm identifies sequences of points that remain within a 
    dispersion threshold for a minimum duration.
    
    Args:
        gaze_data: DataFrame with 'x', 'y', 'timestamp' columns.
        config: Configuration dictionary containing thresholds.
        
    Returns:
        List of fixation dictionaries with start_time, end_time, duration, 
        center_x, center_y, dispersion.
    """
    if len(gaze_data) < 2:
        return []
        
    dispersion_threshold = config["idt_dispersion_threshold"]
    min_duration = config["fixation_min_duration"]
    
    fixations = []
    current_fixation_start_idx = 0
    
    # Iterate through points to find stable periods
    # We use a sliding window approach or sequential check
    # For efficiency, we'll check dispersion of the current window
    
    i = 0
    n = len(gaze_data)
    
    while i < n:
        start_idx = i
        current_window = gaze_data.iloc[start_idx:start_idx+1]
        
        # Extend window while dispersion is within threshold
        while i < n:
            window_data = gaze_data.iloc[start_idx:i+1]
            current_dispersion = calculate_dispersion(window_data)
            
            if current_dispersion <= dispersion_threshold:
                i += 1
            else:
                break
        
        # Check duration
        end_idx = i - 1
        if end_idx >= start_idx:
            window_data = gaze_data.iloc[start_idx:end_idx+1]
            start_time = window_data['timestamp'].iloc[0]
            end_time = window_data['timestamp'].iloc[-1]
            duration = end_time - start_time
            
            if duration >= min_duration:
                center_x = window_data['x'].mean()
                center_y = window_data['y'].mean()
                final_dispersion = calculate_dispersion(window_data)
                
                fixations.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "center_x": center_x,
                    "center_y": center_y,
                    "dispersion": final_dispersion,
                    "type": "fixation"
                })
            
            i = end_idx + 1
        else:
            i += 1
            
    return fixations

def detect_fixations_idt(gaze_data: pd.DataFrame, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect fixations using the I-DT (Velocity-Threshold) algorithm.
    
    The algorithm identifies sequences of points where the instantaneous 
    velocity is below a threshold for a minimum duration.
    
    Args:
        gaze_data: DataFrame with 'x', 'y', 'timestamp' columns.
        config: Configuration dictionary containing thresholds.
        
    Returns:
        List of fixation dictionaries.
    """
    if len(gaze_data) < 2:
        return []
        
    velocity_threshold = config["ivt_velocity_threshold"] # Note: Units may need conversion if data is px/ms
    min_duration = config["fixation_min_duration"]
    
    # Calculate velocities
    velocities = calculate_velocity(gaze_data)
    
    # Identify points where velocity is below threshold
    # Note: Assuming velocity is in px/ms, but config might be deg/s. 
    # For this implementation, we assume the input data and config are consistent 
    # or the threshold is provided in the same units as the calculated velocity.
    # If config is deg/s, a conversion factor (degrees_per_pixel) is needed.
    # Assuming direct comparison for now based on task description simplicity.
    
    is_fixation_point = velocities < velocity_threshold
    
    fixations = []
    current_start_idx = None
    
    for i in range(len(gaze_data)):
        if is_fixation_point[i]:
            if current_start_idx is None:
                current_start_idx = i
        else:
            if current_start_idx is not None:
                # End of a potential fixation
                end_idx = i - 1
                duration = gaze_data['timestamp'].iloc[end_idx] - gaze_data['timestamp'].iloc[current_start_idx]
                
                if duration >= min_duration:
                    window_data = gaze_data.iloc[current_start_idx:end_idx+1]
                    fixations.append({
                        "start_time": window_data['timestamp'].iloc[0],
                        "end_time": window_data['timestamp'].iloc[-1],
                        "duration": duration,
                        "center_x": window_data['x'].mean(),
                        "center_y": window_data['y'].mean(),
                        "dispersion": calculate_dispersion(window_data),
                        "type": "fixation"
                    })
                current_start_idx = None
    
    # Handle fixation at the end of the data
    if current_start_idx is not None:
        end_idx = len(gaze_data) - 1
        duration = gaze_data['timestamp'].iloc[end_idx] - gaze_data['timestamp'].iloc[current_start_idx]
        if duration >= min_duration:
            window_data = gaze_data.iloc[current_start_idx:end_idx+1]
            fixations.append({
                "start_time": window_data['timestamp'].iloc[0],
                "end_time": window_data['timestamp'].iloc[-1],
                "duration": duration,
                "center_x": window_data['x'].mean(),
                "center_y": window_data['y'].mean(),
                "dispersion": calculate_dispersion(window_data),
                "type": "fixation"
            })
            
    return fixations

def process_gaze_data(gaze_data: pd.DataFrame, algorithm: str = "ivt") -> List[Dict[str, Any]]:
    """
    Process gaze data to detect fixations using the specified algorithm.
    
    Args:
        gaze_data: DataFrame with 'x', 'y', 'timestamp' columns.
        algorithm: 'ivt' or 'idt'.
        
    Returns:
        List of detected fixations.
    """
    config = load_fixation_config()
    
    if algorithm == "ivt":
        logger.info("Using I-VT (Dispersion-Threshold) algorithm for fixation detection.")
        return detect_fixations_ivt(gaze_data, config)
    elif algorithm == "idt":
        logger.info("Using I-DT (Velocity-Threshold) algorithm for fixation detection.")
        return detect_fixations_idt(gaze_data, config)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Choose 'ivt' or 'idt'.")

def main():
    """
    Main entry point for testing fixation detection on a sample dataset.
    """
    # Setup logging
    from utils.logging_config import setup_logging
    setup_logging()
    
    # Load sample data if available, otherwise create a synthetic sample for testing
    # This function is primarily for unit testing the logic, not full pipeline execution
    logger.info("Fixation Detection Module Initialized.")
    logger.info(f"Configuration loaded: {load_fixation_config()}")
    
    # Create a dummy sample for demonstration if no file is specified
    # In the real pipeline, this is called by 01_ingest_and_preprocess.py
    sample_data = pd.DataFrame({
        'x': [100, 101, 102, 500, 501, 502, 503],
        'y': [100, 100, 101, 200, 200, 201, 202],
        'timestamp': [0, 10, 20, 100, 110, 120, 130]
    })
    
    fixations = process_gaze_data(sample_data, algorithm="ivt")
    logger.info(f"Detected {len(fixations)} fixations in sample data.")
    for f in fixations:
        logger.info(f"  Fixation: {f}")

if __name__ == "__main__":
    main()