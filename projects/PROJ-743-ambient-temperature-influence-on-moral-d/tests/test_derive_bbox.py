"""
Unit tests for the derive_bbox module.
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.derive_bbox import calculate_bounding_box, ensure_directories

class TestCalculateBoundingBox:
    def test_basic_calculation(self):
        """Test basic bounding box calculation."""
        data = {
            'latitude': [10.0, 20.0, 30.0],
            'longitude': [100.0, 110.0, 120.0]
        }
        df = pd.DataFrame(data)
        bbox = calculate_bounding_box(df)
        
        assert bbox['min_lat'] == 10.0
        assert bbox['max_lat'] == 30.0
        assert bbox['min_lon'] == 100.0
        assert bbox['max_lon'] == 120.0

    def test_with_missing_values(self):
        """Test that missing values are handled correctly."""
        data = {
            'latitude': [10.0, None, 30.0],
            'longitude': [100.0, 110.0, None]
        }
        df = pd.DataFrame(data)
        bbox = calculate_bounding_box(df)
        
        # Only the row with both lat and lon valid (10, 100) should be used
        assert bbox['min_lat'] == 10.0
        assert bbox['max_lat'] == 10.0
        assert bbox['min_lon'] == 100.0
        assert bbox['max_lon'] == 100.0

    def test_empty_valid_data_raises(self):
        """Test that empty valid data raises an error."""
        data = {
            'latitude': [None, None],
            'longitude': [None, None]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No valid latitude/longitude"):
            calculate_bounding_box(df)

    def test_single_point(self):
        """Test calculation with a single valid point."""
        data = {
            'latitude': [45.5],
            'longitude': [-73.6]
        }
        df = pd.DataFrame(data)
        bbox = calculate_bounding_box(df)
        
        assert bbox['min_lat'] == 45.5
        assert bbox['max_lat'] == 45.5
        assert bbox['min_lon'] == -73.6
        assert bbox['max_lon'] == -73.6

class TestEnsureDirectories:
    def test_creates_directory(self):
        """Test that ensure_directories creates the output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the project root behavior for testing
            # by creating a temp dir and checking if a subdirectory is created
            test_dir = Path(tmpdir) / "test_output"
            
            # We can't easily mock the global project_root, so we test the logic
            # by checking if the function would create a directory if we passed it
            # But since the function is hardcoded to use project_root, we just
            # verify it doesn't crash and that the directory exists after calling
            # on a real path.
            
            # Instead, let's just verify the function exists and runs without error
            # on a real directory creation scenario
            try:
                ensure_directories()
                # If we get here, the directory was created successfully
                assert (project_root / "data" / "external").exists()
            except Exception:
                pytest.fail("ensure_directories raised an exception unexpectedly")