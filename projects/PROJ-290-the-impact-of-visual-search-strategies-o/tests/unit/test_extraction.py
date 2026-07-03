import pytest
import numpy as np
from features.extraction import (
    define_generic_roi_grid,
    get_roi_annotations_fallback,
    calculate_fixation_in_roi,
    calculate_saccade_amplitude,
    calculate_dispersion,
    extract_face_features
)

def test_define_generic_roi_grid():
    """Test that the 3x3 grid is generated correctly."""
    width, height = 640, 480
    rois = define_generic_roi_grid(width, height)
    
    assert len(rois) == 9
    # Check first ROI
    assert rois[0]["id"] == "grid_0_0"
    assert rois[0]["x"] == 0.0
    assert rois[0]["y"] == 0.0
    assert rois[0]["width"] == 1/3
    assert rois[0]["height"] == 1/3
    
    # Check center ROI
    assert rois[4]["id"] == "grid_1_1"
    assert rois[4]["x"] == 1/3
    assert rois[4]["y"] == 1/3

def test_get_roi_annotations_fallback_existing():
    """Test that existing annotations are returned."""
    existing = [{"id": "eye", "x": 0, "y": 0}]
    result = get_roi_annotations_fallback(existing, 640, 480)
    assert result is existing

def test_get_roi_annotations_fallback_missing():
    """Test that fallback grid is generated when annotations are missing."""
    result = get_roi_annotations_fallback(None, 640, 480)
    assert len(result) == 9

def test_calculate_fixation_in_roi_pixel_coords():
    """Test fixation calculation with pixel coordinates."""
    roi = {
        "x_px": 0, "y_px": 0, "width_px": 100, "height_px": 100
    }
    gaze_data = [
        {"x": 50, "y": 50, "duration": 100}, # Inside
        {"x": 150, "y": 50, "duration": 200}  # Outside
    ]
    
    result = calculate_fixation_in_roi(gaze_data, roi, 640, 480)
    assert result["total_duration_ms"] == 100
    assert result["fixation_count"] == 1

def test_calculate_fixation_in_roi_normalized_coords():
    """Test fixation calculation with normalized coordinates."""
    roi = {
        "x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5 # 0-50% of image
    }
    # Image 640x480. ROI covers 0-320, 0-240.
    gaze_data = [
        {"x": 100, "y": 100, "duration": 100}, # Inside
        {"x": 400, "y": 100, "duration": 200}  # Outside
    ]
    
    result = calculate_fixation_in_roi(gaze_data, roi, 640, 480)
    assert result["total_duration_ms"] == 100
    assert result["fixation_count"] == 1

def test_calculate_saccade_amplitude():
    """Test saccade amplitude calculation."""
    gaze_data = [
        {"x": 0, "y": 0},
        {"x": 3, "y": 4} # Distance 5
    ]
    amp = calculate_saccade_amplitude(gaze_data)
    assert amp == 5.0

def test_calculate_saccade_amplitude_single_point():
    """Test saccade amplitude with insufficient data."""
    gaze_data = [{"x": 0, "y": 0}]
    amp = calculate_saccade_amplitude(gaze_data)
    assert amp == 0.0

def test_calculate_dispersion():
    """Test dispersion calculation."""
    gaze_data = [
        {"x": 0, "y": 0},
        {"x": 10, "y": 0},
        {"x": 0, "y": 5}
    ]
    # Width 10, Height 5 -> Area 50
    disp = calculate_dispersion(gaze_data)
    assert disp == 50.0

def test_extract_face_features():
    """Test full extraction pipeline."""
    gaze_data = [
        {"x": 50, "y": 50, "duration": 100},
        {"x": 100, "y": 100, "duration": 200}
    ]
    features = extract_face_features(gaze_data, 640, 480, None)
    
    assert features["total_gaze_points"] == 2
    assert "roi_metrics" in features
    assert features["saccade_amplitude_px"] > 0
    assert features["dispersion_px2"] > 0