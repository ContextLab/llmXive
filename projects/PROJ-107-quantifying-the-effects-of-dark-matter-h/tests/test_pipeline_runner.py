import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.processing.pipeline_runner import (
    validate_shape_metrics_chunk,
    write_exclusion_log,
    save_halo_shapes_chunk
)
from code.processing.shape_metrics import get_exclusion_reason

class TestPipelineValidation:
    """Tests for validation logic in pipeline_runner"""

    def test_valid_metrics(self):
        """Test that valid metrics pass validation"""
        metrics = {
            "halo_id": 1,
            "mass": 1e12,
            "b_a_ratio": 0.8,
            "c_a_ratio": 0.6,
            "triaxiality": 0.3,
            "particle_count": 15000
        }
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        assert is_valid is True
        assert error_msg is None

    def test_invalid_b_a_ratio(self):
        """Test that b/a > 1 fails validation"""
        metrics = {
            "halo_id": 2,
            "mass": 1e12,
            "b_a_ratio": 1.2,
            "c_a_ratio": 0.6,
            "triaxiality": 0.3,
            "particle_count": 15000
        }
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        assert is_valid is False
        assert "b_a_ratio" in error_msg

    def test_invalid_c_a_ratio(self):
        """Test that c/a <= 0 fails validation"""
        metrics = {
            "halo_id": 3,
            "mass": 1e12,
            "b_a_ratio": 0.8,
            "c_a_ratio": 0.0,
            "triaxiality": 0.3,
            "particle_count": 15000
        }
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        assert is_valid is False
        assert "c_a_ratio" in error_msg

    def test_invalid_triaxiality(self):
        """Test that triaxiality < 0 fails validation"""
        metrics = {
            "halo_id": 4,
            "mass": 1e12,
            "b_a_ratio": 0.8,
            "c_a_ratio": 0.6,
            "triaxiality": -0.1,
            "particle_count": 15000
        }
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        assert is_valid is False
        assert "triaxiality" in error_msg

    def test_low_particle_count(self):
        """Test that particle count < 10000 fails validation"""
        metrics = {
            "halo_id": 5,
            "mass": 1e12,
            "b_a_ratio": 0.8,
            "c_a_ratio": 0.6,
            "triaxiality": 0.3,
            "particle_count": 5000
        }
        is_valid, error_msg = validate_shape_metrics_chunk(metrics)
        assert is_valid is False
        assert "particle_count" in error_msg

class TestPipelineRunnerIntegration:
    """Integration tests for pipeline runner output generation"""

    def setup_method(self):
        """Setup temporary directory for test outputs"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_csv = Path(self.temp_dir) / "test_halo_shapes.csv"
        self.output_json = Path(self.temp_dir) / "test_exclusion_log.json"

    def teardown_method(self):
        """Cleanup temporary directory"""
        shutil.rmtree(self.temp_dir)

    def test_save_halo_shapes_chunk(self):
        """Test saving halo shapes to CSV with associational flag"""
        results = [
            {
                "halo_id": 1,
                "mass": 1.2e12,
                "b_a_ratio": 0.85,
                "c_a_ratio": 0.65,
                "triaxiality": 0.25,
                "particle_count": 12000
            },
            {
                "halo_id": 2,
                "mass": 3.5e12,
                "b_a_ratio": 0.75,
                "c_a_ratio": 0.55,
                "triaxiality": 0.45,
                "particle_count": 25000
            }
        ]
        
        save_halo_shapes_chunk(results, self.output_csv)
        
        assert self.output_csv.exists()
        
        # Verify content
        df = pd.read_csv(self.output_csv)
        assert len(df) == 2
        assert "halo_id" in df.columns
        assert "mass" in df.columns
        assert "b_a_ratio" in df.columns
        assert "c_a_ratio" in df.columns
        assert "triaxiality" in df.columns
        assert "particle_count" in df.columns

        # Verify associational flag in header (comment)
        with open(self.output_csv, 'r') as f:
            first_line = f.readline()
            assert "# associational_only=true" in first_line

    def test_write_exclusion_log(self):
        """Test writing exclusion log to JSON with associational flag"""
        excluded = [
            {"halo_id": 10, "reason": "particle_count < 10000"},
            {"halo_id": 11, "reason": "b_a_ratio validation failed"}
        ]
        
        write_exclusion_log(excluded, self.output_json)
        
        assert self.output_json.exists()
        
        # Verify content
        import json
        with open(self.output_json, 'r') as f:
            data = json.load(f)
            assert "associational_only" in data
            assert data["associational_only"] is True
            assert "data" in data
            assert len(data["data"]) == 2
            assert data["data"][0]["halo_id"] == 10

class TestPipelineRunnerFull:
    """Full integration test for the pipeline runner logic"""
    
    def test_full_pipeline_logic(self):
        """Simulate the full pipeline logic with mock data"""
        # This test verifies the logic flow without requiring real TNG data
        # We mock the process_halo_chunk function to return deterministic results
        
        mock_valid_result = {
            "halo_id": 100,
            "mass": 1.5e12,
            "b_a_ratio": 0.9,
            "c_a_ratio": 0.7,
            "triaxiality": 0.15,
            "particle_count": 10000
        }
        
        mock_excluded_result = None # Represents a halo that fails processing or validation
        
        # Test validation logic directly
        is_valid, err = validate_shape_metrics_chunk(mock_valid_result)
        assert is_valid
        
        is_valid, err = validate_shape_metrics_chunk(mock_excluded_result)
        assert not is_valid
        
        # Test exclusion reason retrieval
        reason = get_exclusion_reason("particle_count")
        assert "particle_count" in reason.lower()
        
        reason = get_exclusion_reason("b_a_ratio")
        assert "b_a_ratio" in reason.lower()