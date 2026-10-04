import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from data.validate import (
    define_generic_roi_grid,
    apply_roi_fallback,
    validate_dataset,
    write_validation_report
)

class TestROIFallback:
    """Tests for Generic ROI Fallback (3x3 grid) logic."""

    def test_define_generic_roi_grid_basic(self):
        """Test that 3x3 grid is generated correctly."""
        grid = define_generic_roi_grid(64, 64)
        
        assert len(grid) == 9
        assert "top_left" in grid
        assert "bottom_right" in grid
        assert "middle_center" in grid
        
        # Check dimensions
        for name, (x, y, w, h) in grid.items():
            assert x >= 0
            assert y >= 0
            assert w > 0
            assert h > 0

    def test_define_generic_roi_grid_dimensions(self):
        """Test grid dimensions match input image size."""
        width, height = 128, 64
        grid = define_generic_roi_grid(width, height)
        
        cell_w = width // 3
        cell_h = height // 3
        
        for name, (x, y, w, h) in grid.items():
            assert w == cell_w
            assert h == cell_h

    def test_apply_roi_fallback_missing_column(self):
        """Test fallback when roi_annotations column is missing."""
        df = pd.DataFrame({
            "participant_id": [1, 2, 3],
            "gaze_coordinates": [[1, 2], [3, 4], [5, 6]],
            "response_times": [0.5, 0.6, 0.7]
        })
        
        modified_df, fallback_info = apply_roi_fallback(df)
        
        assert "roi_annotations" in modified_df.columns
        assert fallback_info["applied"] is True
        assert fallback_info["records_modified"] == 3
        assert fallback_info["grid_type"] == "3x3"
        
        # Check that all records have grid
        for idx, row in modified_df.iterrows():
            assert isinstance(row["roi_annotations"], dict)
            assert len(row["roi_annotations"]) == 9

    def test_apply_roi_fallback_empty_annotations(self):
        """Test fallback for records with empty roi_annotations."""
        df = pd.DataFrame({
            "participant_id": [1, 2, 3],
            "gaze_coordinates": [[1, 2], [3, 4], [5, 6]],
            "response_times": [0.5, 0.6, 0.7],
            "roi_annotations": [
                {"top_left": (0, 0, 10, 10)},  # Valid
                None,  # Missing
                {}  # Empty
            ]
        })
        
        modified_df, fallback_info = apply_roi_fallback(df)
        
        assert fallback_info["applied"] is True
        assert fallback_info["records_modified"] == 2
        
        # First record should be unchanged
        assert len(modified_df.iloc[0]["roi_annotations"]) == 1
        
        # Other records should have full grid
        for idx in [1, 2]:
            assert len(modified_df.iloc[idx]["roi_annotations"]) == 9

    def test_apply_roi_fallback_no_missing(self):
        """Test that no fallback is applied when all annotations are valid."""
        df = pd.DataFrame({
            "participant_id": [1, 2, 3],
            "gaze_coordinates": [[1, 2], [3, 4], [5, 6]],
            "response_times": [0.5, 0.6, 0.7],
            "roi_annotations": [
                {"top_left": (0, 0, 10, 10)},
                {"middle_center": (10, 10, 20, 20)},
                {"bottom_right": (20, 20, 30, 30)}
            ]
        })
        
        modified_df, fallback_info = apply_roi_fallback(df)
        
        assert fallback_info["applied"] is False
        assert fallback_info["records_modified"] == 0

    def test_validate_dataset_with_roi_fallback(self):
        """Test full validation pipeline with ROI fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "validation_report.json")
            
            df = pd.DataFrame({
                "participant_id": [1, 2, 3],
                "gaze_coordinates": [[1, 2], [3, 4], [5, 6]],
                "response_times": [0.5, 0.6, 0.7],
                "emotion_labels": ["happy", "sad", "neutral"]
            })
            
            required_vars = ["gaze_coordinates", "response_times", "emotion_labels", "roi_annotations"]
            
            success = validate_dataset(
                df, 
                required_vars, 
                output_path=output_path,
                image_width=64,
                image_height=64
            )
            
            assert success is True
            assert Path(output_path).exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["status"] in ["PASS", "WARN"]
            assert report["roi_fallback_applied"] is True
            assert report["roi_fallback_details"]["records_modified"] == 3

    def test_validate_dataset_critical_missing(self):
        """Test that validation fails when critical variables are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "validation_report.json")
            
            df = pd.DataFrame({
                "participant_id": [1, 2, 3],
                "response_times": [0.5, 0.6, 0.7]
                # Missing gaze_coordinates and emotion_labels
            })
            
            required_vars = ["gaze_coordinates", "response_times", "emotion_labels", "roi_annotations"]
            
            success = validate_dataset(
                df, 
                required_vars, 
                output_path=output_path
            )
            
            assert success is False
            assert Path(output_path).exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["status"] == "FAIL"
            assert "gaze_coordinates" in report["missing_variables"]
            assert "emotion_labels" in report["missing_variables"]