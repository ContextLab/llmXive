import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from shapely.geometry import Point, Polygon

# Import from the project's utility module
from code.utils.roi_mapping import is_point_in_roi, map_single_point_to_roi, map_gaze_to_rois

@pytest.fixture
def sample_roi_config():
    return {
        "source_attribution": {
            "vertices": [(0, 0), (100, 0), (100, 50), (0, 50)]
        },
        "headline_body": {
            "vertices": [(0, 50), (800, 50), (800, 150), (0, 150)]
        }
    }

@pytest.fixture
def sample_gaze_data():
    return pd.DataFrame({
        'x': [50, 400, 150],
        'y': [25, 75, 200],
        'timestamp': [100, 200, 300],
        'participant_id': ['P1', 'P1', 'P1']
    })

def test_is_point_in_roi_inside():
    roi_vertices = [(0, 0), (100, 0), (100, 50), (0, 50)]
    point = Point(50, 25)
    roi_polygon = Polygon(roi_vertices)
    assert is_point_in_roi(point, roi_polygon) is True

def test_is_point_in_roi_outside():
    roi_vertices = [(0, 0), (100, 0), (100, 50), (0, 50)]
    point = Point(150, 25)
    roi_polygon = Polygon(roi_vertices)
    assert is_point_in_roi(point, roi_polygon) is False

def test_map_single_point_to_roi_found(sample_roi_config):
    point = Point(50, 25)
    roi_name, matched = map_single_point_to_roi(point, sample_roi_config)
    assert roi_name == "source_attribution"
    assert matched is True

def test_map_single_point_to_roi_not_found(sample_roi_config):
    point = Point(200, 200)
    roi_name, matched = map_single_point_to_roi(point, sample_roi_config)
    assert roi_name is None
    assert matched is False

def test_map_gaze_to_rois(sample_roi_config, sample_gaze_data):
    result = map_gaze_to_rois(sample_gaze_data, sample_roi_config)
    assert 'roi_type' in result.columns
    assert result.iloc[0]['roi_type'] == 'source_attribution'
    assert result.iloc[1]['roi_type'] == 'headline_body'
    assert result.iloc[2]['roi_type'] is None  # Outside any ROI

def test_map_gaze_to_rois_empty_dataframe(sample_roi_config):
    empty_df = pd.DataFrame(columns=['x', 'y', 'timestamp', 'participant_id'])
    result = map_gaze_to_rois(empty_df, sample_roi_config)
    assert 'roi_type' in result.columns
    assert len(result) == 0
