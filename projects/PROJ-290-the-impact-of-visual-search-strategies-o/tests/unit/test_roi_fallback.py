"""
Unit tests for T013: Generic ROI Fallback logic.

These tests verify that the 3x3 grid is correctly generated and applied
to records missing `roi_annotations`.
"""

import json
import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.roi_fallback import (
    define_generic_roi_grid,
    apply_roi_fallback,
    run_roi_fallback_pipeline
)
from utils.logging import get_logger


class TestDefineGenericROIGrid:
    def test_grid_dimensions(self):
        """Test that the grid produces 9 regions."""
        grid = define_generic_roi_grid(200, 200)
        assert len(grid) == 9
        
    def test_grid_keys(self):
        """Test that grid keys follow the expected pattern."""
        grid = define_generic_roi_grid(200, 200)
        expected_keys = [f"grid_{r}_{c}" for r in range(3) for c in range(3)]
        assert set(grid.keys()) == set(expected_keys)
        
    def test_grid_coordinates(self):
        """Test that coordinates are within bounds."""
        w, h = 200, 200
        grid = define_generic_roi_grid(w, h)
        for key, region in grid.items():
            assert 0 <= region["x_min"] < w
            assert 0 <= region["y_min"] < h
            assert region["x_max"] <= w
            assert region["y_max"] <= h
            assert region["x_max"] > region["x_min"]
            assert region["y_max"] > region["y_min"]

class TestApplyROIFallback:
    def setup_method(self):
        self.logger = get_logger("test_roi_fallback")
        
    def test_no_missing_annotations(self):
        """Test that no fallback is applied if all records have annotations."""
        data = [
            {"id": 1, "roi_annotations": {"custom": "data"}},
            {"id": 2, "roi_annotations": {"custom": "data"}}
        ]
        updated, count = apply_roi_fallback(data, self.logger)
        assert count == 0
        assert updated[0]["roi_annotations"] == {"custom": "data"}
        
    def test_missing_annotations(self):
        """Test that fallback is applied to missing annotations."""
        data = [
            {"id": 1, "roi_annotations": None},
            {"id": 2}, # Key missing entirely
            {"id": 3, "roi_annotations": {"valid": "data"}}
        ]
        updated, count = apply_roi_fallback(data, self.logger)
        assert count == 2
        assert "grid_0_0" in updated[0]["roi_annotations"]
        assert "grid_0_0" in updated[1]["roi_annotations"]
        assert updated[2]["roi_annotations"] == {"valid": "data"}
        
    def test_empty_list(self):
        """Test handling of empty data list."""
        data = []
        updated, count = apply_roi_fallback(data, self.logger)
        assert count == 0
        assert updated == []

class TestROIFallbackPipeline:
    def test_run_pipeline_with_json(self, tmp_path):
        """Test the full pipeline with a JSON input file."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        data = [
            {"participant_id": "P1", "roi_annotations": None},
            {"participant_id": "P2", "roi_annotations": {"existing": "roi"}}
        ]
        
        with open(input_file, 'w') as f:
            json.dump(data, f)
            
        result = run_roi_fallback_pipeline(
            input_data_path=input_file,
            output_data_path=output_file,
            force_overwrite=True
        )
        
        assert result["status"] == "success"
        assert result["fallbacks_applied"] == 1
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            output_data = json.load(f)
            
        assert "grid_0_0" in output_data[0]["roi_annotations"]
        assert output_data[1]["roi_annotations"] == {"existing": "roi"}

    def test_run_pipeline_no_input(self):
        """Test that pipeline fails gracefully if input not found."""
        result = run_roi_fallback_pipeline(
            input_data_path=Path("/nonexistent/path/file.json")
        )
        assert result["status"] == "error"