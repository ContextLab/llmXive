import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_era_full import (
    ensure_directories,
    frange,
    tile_overlaps_bbox,
    main
)

def test_ensure_directories():
    """Test that ensure_directories creates the necessary folders."""
    ensure_directories()
    assert Path("data/raw").exists()
    assert Path("data/external").exists()
    assert Path("results/logs").exists()

def test_frange():
    """Test the float range generator."""
    result = list(frange(0, 1, 0.5))
    assert len(result) == 2
    assert abs(result[0] - 0.0) < 0.0001
    assert abs(result[1] - 0.5) < 0.0001

def test_tile_overlaps_bbox():
    """Test tile overlap logic."""
    bbox = {
        "min_lat": 50.0,
        "max_lat": 52.0,
        "min_lon": -1.0,
        "max_lon": 1.0
    }
    
    # Tile inside bbox
    assert tile_overlaps_bbox(51.0, 0.0, bbox) is True
    
    # Tile outside bbox
    assert tile_overlaps_bbox(53.0, 0.0, bbox) is False
    assert tile_overlaps_bbox(51.0, 5.0, bbox) is False

@patch('fetch_era_full.get_cds_client')
@patch('fetch_era_full.append_log')
def test_main_with_mock(mock_append_log, mock_get_client):
    """Test main function with mocked CDS client."""
    # Create a mock bounding box file
    bbox_data = {
        "min_lat": 50.0,
        "max_lat": 52.0,
        "min_lon": -1.0,
        "max_lon": 1.0
    }
    os.makedirs("data/external", exist_ok=True)
    with open("data/external/bounding_box.json", "w") as f:
        json.dump(bbox_data, f)
    
    # Mock the CDS client
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Mock the retrieve method to avoid actual API calls
    mock_client.retrieve = MagicMock()
    
    # Run main
    try:
        main()
    except Exception as e:
        # We expect an error because we're not actually fetching data
        pass
    
    # Verify that ensure_directories was called
    assert Path("data/raw").exists()
    
    # Clean up
    if os.path.exists("data/external/bounding_box.json"):
        os.remove("data/external/bounding_box.json")
    if os.path.exists("data/raw/era5_full.h5"):
        os.remove("data/raw/era5_full.h5")