import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import logging
import pandas as pd
from pathlib import Path
from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(name: str = "extraction") -> logging.Logger:
    return get_logger(name)

def define_generic_roi_grid(img_shape: Tuple[int, int], grid_size: int = 3) -> List[Dict[str, Any]]:
    """
    Define a generic 3x3 grid ROI fallback for face images.
    Returns a list of ROI definitions with coordinates.
    """
    h, w = img_shape
    roi_list = []
    step_h = h // grid_size
    step_w = w // grid_size
    
    for r in range(grid_size):
        for c in range(grid_size):
            y1, y2 = r * step_h, (r + 1) * step_h
            x1, x2 = c * step_w, (c + 1) * step_w
            roi_list.append({
                "name": f"grid_{r}_{c}",
                "y1": y1, "y2": y2,
                "x1": x1, "x2": x2,
                "type": "grid"
            })
    return roi_list

def get_roi_annotations_fallback(gaze_data: pd.DataFrame, img_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
    """
    Fallback function to generate ROI annotations if missing.
    Uses the generic 3x3 grid.
    """
    return define_generic_roi_grid(img_shape)

def calculate_fixation_in_roi(gaze_points: List[Dict], roi: Dict) -> float:
    """
    Calculate total fixation duration within a specific ROI.
    gaze_points: List of dicts with 'x', 'y', 'duration'
    roi: Dict with 'x1', 'x2', 'y1', 'y2'
    """
    total_duration = 0.0
    for point in gaze_points:
        if (roi['x1'] <= point['x'] <= roi['x2'] and
            roi['y1'] <= point['y'] <= roi['y2']):
            total_duration += point.get('duration', 0.0)
    return total_duration

def calculate_saccade_amplitude(gaze_points: List[Dict]) -> float:
    """
    Calculate average saccade amplitude from a sequence of gaze points.
    """
    if len(gaze_points) < 2:
        return 0.0
    
    amplitudes = []
    for i in range(1, len(gaze_points)):
        p1 = gaze_points[i-1]
        p2 = gaze_points[i]
        dist = np.sqrt((p2['x'] - p1['x'])**2 + (p2['y'] - p1['y'])**2)
        amplitudes.append(dist)
    
    return np.mean(amplitudes) if amplitudes else 0.0

def calculate_dispersion(gaze_points: List[Dict]) -> float:
    """
    Calculate spatial dispersion (standard deviation of x and y).
    """
    if len(gaze_points) < 2:
        return 0.0
    
    xs = [p['x'] for p in gaze_points]
    ys = [p['y'] for p in gaze_points]
    
    return np.std(xs) + np.std(ys)

def extract_face_features(row: pd.Series) -> Dict[str, Any]:
    """
    Extract features from a single participant record (row).
    Implements T018 logic: fixation duration, saccade amplitude, dispersion.
    Handles missing ROI annotations with fallback.
    """
    logger = get_logger_wrapper("extraction")
    
    # Initialize result dict
    features = {
        'participant_id': row.get('participant_id', 'unknown'),
        'trial_id': row.get('trial_id', 'unknown'),
        'emotion_label': row.get('emotion_label', 'neutral'),
        'response_time': row.get('response_time', 0.0),
        'fixation_duration_eye': 0.0,
        'fixation_duration_mouth': 0.0,
        'saccade_amplitude': 0.0,
        'dispersion': 0.0,
        'total_fixations': 0
    }
    
    # Extract gaze data
    # Assume gaze data is stored as a list of dicts or a string representation
    gaze_data = row.get('gaze_coordinates')
    
    if not gaze_data or not isinstance(gaze_data, list):
        logger.warning(f"No valid gaze data for participant {features['participant_id']}")
        return features
    
    # Handle ROI annotations
    roi_data = row.get('roi_annotations')
    img_shape = row.get('image_shape', (480, 640)) # Default fallback shape
    
    if not roi_data:
        logger.info(f"Applying generic ROI fallback for participant {features['participant_id']}")
        roi_data = get_roi_annotations_fallback(gaze_data, img_shape)
    
    # Identify Eye and Mouth ROIs
    # In a real scenario, we'd look for specific names. 
    # For fallback grid, we might assume top rows are eyes, bottom is mouth?
    # Or we just calculate total fixation for now if specific ROIs aren't named.
    # Let's assume specific ROIs exist if not fallback.
    eye_roi = None
    mouth_roi = None
    
    for roi in roi_data:
        name = roi.get('name', '').lower()
        if 'eye' in name or 'top' in name: # Heuristic for fallback
            eye_roi = roi
        if 'mouth' in name or 'bottom' in name:
            mouth_roi = roi
    
    # Calculate metrics
    total_fix_duration = 0.0
    
    for roi in roi_data:
        duration = calculate_fixation_in_roi(gaze_data, roi)
        total_fix_duration += duration
        
        if roi == eye_roi:
            features['fixation_duration_eye'] = duration
        elif roi == mouth_roi:
            features['fixation_duration_mouth'] = duration
    
    # If no specific eye/mouth found, assign totals to eye (conservative) or 0
    if not eye_roi and not mouth_roi:
        features['fixation_duration_eye'] = total_fix_duration
        
    features['saccade_amplitude'] = calculate_saccade_amplitude(gaze_data)
    features['dispersion'] = calculate_dispersion(gaze_data)
    features['total_fixations'] = len(gaze_data)
    
    return features

def process_participant_record(row: pd.Series) -> Dict[str, Any]:
    """Wrapper for extract_face_features to match expected interface."""
    return extract_face_features(row)

def main():
    """
    Main entry point for testing extraction logic directly.
    """
    logger = get_logger_wrapper("extraction")
    logger.info("Extraction module loaded successfully.")
    # This is a module-level test
    test_row = pd.Series({
        'participant_id': 'P001',
        'gaze_coordinates': [{'x': 100, 'y': 100, 'duration': 0.1}, {'x': 105, 'y': 105, 'duration': 0.1}],
        'image_shape': (480, 640)
    })
    result = extract_face_features(test_row)
    logger.info(f"Test extraction result: {result}")

if __name__ == "__main__":
    main()
