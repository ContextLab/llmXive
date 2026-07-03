"""
Unit tests for fixation metric calculation (eye/mouth duration).
Tests the `extract_face_features` and related ROI functions from code/features/extraction.py.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
# Assuming tests are run from project root or via pytest discovery
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from features.extraction import (
    define_generic_roi_grid,
    get_roi_annotations_fallback,
    calculate_fixation_in_roi,
    extract_face_features
)
from utils.logging import get_logger

logger = get_logger(__name__)

# --- Mock Data Helpers ---

def create_mock_gaze_data(n_points=100, noise=5.0):
    """
    Generates mock gaze data with x, y coordinates, timestamp, and event type.
    Simulates a pattern where points cluster around 'eyes' and 'mouth' regions.
    """
    np.random.seed(42)
    # Base coordinates (0-1000 image space)
    # Eyes cluster around (300, 300) and (700, 300)
    # Mouth cluster around (500, 700)
    
    data = []
    for i in range(n_points):
        t = i * 16.67  # ~60Hz sampling
        # Randomly assign to region: 0=left_eye, 1=right_eye, 2=mouth
        region = np.random.choice([0, 1, 2], p=[0.3, 0.3, 0.4])
        
        if region == 0: # Left Eye
            x = 300 + np.random.normal(0, noise)
            y = 300 + np.random.normal(0, noise)
        elif region == 1: # Right Eye
            x = 700 + np.random.normal(0, noise)
            y = 300 + np.random.normal(0, noise)
        else: # Mouth
            x = 500 + np.random.normal(0, noise)
            y = 700 + np.random.normal(0, noise)
        
        data.append({
            'x': x,
            'y': y,
            'timestamp': t,
            'event': 'fixation'
        })
    return data

def create_mock_roi_annotations():
    """
    Returns a list of ROI definitions matching the expected schema.
    """
    return [
        {
            "label": "left_eye",
            "x": 250, "y": 250, "width": 100, "height": 100
        },
        {
            "label": "right_eye",
            "x": 650, "y": 250, "width": 100, "height": 100
        },
        {
            "label": "mouth",
            "x": 450, "y": 650, "width": 100, "height": 100
        }
    ]

# --- Test Cases ---

class TestROIDefinitions:
    def test_define_generic_roi_grid_returns_3x3(self):
        """Verify that the generic fallback returns a 3x3 grid structure."""
        width, height = 1000, 1000
        grid = define_generic_roi_grid(width, height)
        assert len(grid) == 9, "Generic fallback must return 9 ROIs for 3x3 grid."
        # Check specific ROIs exist
        labels = [r['label'] for r in grid]
        assert 'top_left' in labels
        assert 'center' in labels
        assert 'bottom_right' in labels

    def test_get_roi_annotations_fallback_uses_grid(self):
        """Verify fallback logic when provided annotations are missing/invalid."""
        # Pass None
        fallback = get_roi_annotations_fallback(None, 1000, 1000)
        assert fallback is not None
        assert len(fallback) == 9

        # Pass empty list
        fallback = get_roi_annotations_fallback([], 1000, 1000)
        assert len(fallback) == 9

        # Pass valid list -> should return valid list
        valid = create_mock_roi_annotations()
        fallback = get_roi_annotations_fallback(valid, 1000, 1000)
        assert fallback == valid

class TestFixationCalculation:
    def test_calculate_fixation_in_roi_basic(self):
        """Test that fixation duration is correctly calculated for a specific ROI."""
        gaze_data = create_mock_gaze_data(n_points=100)
        roi = {
            "label": "mouth",
            "x": 450, "y": 650, "width": 100, "height": 100
        }
        
        duration = calculate_fixation_in_roi(gaze_data, roi)
        
        # With 40% of points in mouth region (40 points), and ~16.67ms per point:
        # Expected duration should be roughly 40 * 16.67 = 666.8 ms
        # Allow some tolerance for noise and boundary checks
        assert 500 < duration < 800, f"Expected mouth duration around 667ms, got {duration}"

    def test_calculate_fixation_in_roi_empty_roi(self):
        """Test calculation when no points fall into the ROI."""
        gaze_data = create_mock_gaze_data(n_points=100)
        # Define an ROI far away from any data
        roi = {
            "label": "far_away",
            "x": 0, "y": 0, "width": 10, "height": 10
        }
        
        duration = calculate_fixation_in_roi(gaze_data, roi)
        assert duration == 0.0, "Duration should be 0 if no points in ROI."

class TestFeatureExtraction:
    def test_extract_face_features_computes_eye_mouth_ratio(self):
        """
        Main test: Ensure extract_face_features returns a dictionary containing
        eye duration, mouth duration, and the calculated ratio.
        """
        gaze_data = create_mock_gaze_data(n_points=200)
        rois = create_mock_roi_annotations()
        
        result = extract_face_features(gaze_data, rois)
        
        # Check keys exist
        assert 'left_eye_duration' in result
        assert 'right_eye_duration' in result
        assert 'mouth_duration' in result
        assert 'total_eye_duration' in result
        assert 'eye_to_mouth_ratio' in result
        
        # Check types
        assert isinstance(result['left_eye_duration'], (int, float))
        assert isinstance(result['eye_to_mouth_ratio'], (int, float))
        
        # Check logic: Eye duration should be > 0, Mouth > 0
        assert result['total_eye_duration'] > 0
        assert result['mouth_duration'] > 0
        
        # Check ratio calculation
        expected_ratio = result['total_eye_duration'] / result['mouth_duration'] if result['mouth_duration'] > 0 else 0.0
        # Allow small floating point errors
        assert np.isclose(result['eye_to_mouth_ratio'], expected_ratio, rtol=1e-5)

    def test_extract_face_features_handles_missing_rois(self):
        """Test that extraction handles missing specific ROIs gracefully."""
        gaze_data = create_mock_gaze_data(n_points=200)
        # Provide only mouth ROI
        partial_rois = [create_mock_roi_annotations()[2]]
        
        result = extract_face_features(gaze_data, partial_rois)
        
        # Eye durations should be 0 or NaN depending on implementation, 
        # but function shouldn't crash.
        assert result['mouth_duration'] > 0
        # If eye ROI is missing, total_eye_duration might be 0
        assert result['total_eye_duration'] == 0.0
        
    def test_extract_face_features_with_fallback_rois(self):
        """Test extraction when using generic fallback ROIs."""
        gaze_data = create_mock_gaze_data(n_points=200)
        # Pass None to trigger fallback
        result = extract_face_features(gaze_data, None)
        
        assert 'total_eye_duration' in result
        assert 'eye_to_mouth_ratio' in result
        # With 3x3 grid, 'eyes' and 'mouth' might map to specific grid cells
        # or the function might handle the mapping internally.
        # The key is that it runs without error and returns a ratio.
        assert isinstance(result['eye_to_mouth_ratio'], float)