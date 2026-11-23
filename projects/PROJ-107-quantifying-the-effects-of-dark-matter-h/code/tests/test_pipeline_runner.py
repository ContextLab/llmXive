"""
Tests for the pipeline_runner module.

This module contains unit and integration tests for T017,
verifying aggregation, validation, and output generation.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import csv

from processing.pipeline_runner import (
    iterate_haloes,
    validate_shape_metrics_chunk,
    run_pipeline,
    write_halo_shapes_csv,
    write_exclusion_log
)
from utils.config import get_project_root, get_data_processed_path


class TestPipelineValidation:
    """Tests for validation logic in pipeline_runner."""

    def test_validate_shape_metrics_valid(self):
        """Test validation with valid shape metrics."""
        records = [
            {
                "halo_id": 1,
                "b_a_ratio": 0.8,
                "c_a_ratio": 0.6,
                "triaxiality": 0.3,
                "excluded": False
            },
            {
                "halo_id": 2,
                "b_a_ratio": 0.5,
                "c_a_ratio": 0.3,
                "triaxiality": 0.7,
                "excluded": False
            }
        ]
        
        valid, excluded = validate_shape_metrics_chunk(records)
        
        assert len(valid) == 2
        assert len(excluded) == 0
    
    def test_validate_shape_metrics_invalid_b_a(self):
        """Test validation with invalid b/a ratio (> 1)."""
        records = [
            {
                "halo_id": 1,
                "b_a_ratio": 1.5,  # Invalid: > 1
                "c_a_ratio": 0.6,
                "triaxiality": 0.3,
                "excluded": False
            }
        ]
        
        valid, excluded = validate_shape_metrics_chunk(records)
        
        assert len(valid) == 0
        assert len(excluded) == 1
        assert "Invalid shape metrics" in excluded[0]["exclusion_reason"]
    
    def test_validate_shape_metrics_invalid_c_a(self):
        """Test validation with invalid c/a ratio (< 0)."""
        records = [
            {
                "halo_id": 1,
                "b_a_ratio": 0.8,
                "c_a_ratio": -0.1,  # Invalid: < 0
                "triaxiality": 0.3,
                "excluded": False
            }
        ]
        
        valid, excluded = validate_shape_metrics_chunk(records)
        
        assert len(valid) == 0
        assert len(excluded) == 1
        assert "Invalid shape metrics" in excluded[0]["exclusion_reason"]
    
    def test_validate_shape_metrics_invalid_triaxiality(self):
        """Test validation with invalid triaxiality (> 1)."""
        records = [
            {
                "halo_id": 1,
                "b_a_ratio": 0.8,
                "c_a_ratio": 0.6,
                "triaxiality": 1.5,  # Invalid: > 1
                "excluded": False
            }
        ]
        
        valid, excluded = validate_shape_metrics_chunk(records)
        
        assert len(valid) == 0
        assert len(excluded) == 1
        assert "Invalid shape metrics" in excluded[0]["exclusion_reason"]
    
    def test_validate_shape_metrics_already_excluded(self):
        """Test that already excluded records are not re-validated."""
        records = [
            {
                "halo_id": 1,
                "excluded": True,
                "exclusion_reason": "Low particle count"
            }
        ]
        
        valid, excluded = validate_shape_metrics_chunk(records)
        
        assert len(valid) == 0
        assert len(excluded) == 1
        assert excluded[0]["exclusion_reason"] == "Low particle count"

class TestPipelineRunnerIntegration:
    """Integration tests for pipeline_runner."""

    def test_write_halo_shapes_csv(self):
        """Test writing halo shapes to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_halo_shapes.csv"
            
            records = [
                {
                    "halo_id": 1,
                    "mass": 1.0e12,
                    "b_a_ratio": 0.8,
                    "c_a_ratio": 0.6,
                    "triaxiality": 0.3,
                    "particle_count": 15000
                },
                {
                    "halo_id": 2,
                    "mass": 2.0e12,
                    "b_a_ratio": 0.5,
                    "c_a_ratio": 0.3,
                    "triaxiality": 0.7,
                    "particle_count": 20000
                }
            ]
            
            write_halo_shapes_csv(records, output_path)
            
            assert output_path.exists()
            
            # Read back and verify
            df = pd.read_csv(output_path)
            
            assert len(df) == 2
            assert list(df.columns) == ["halo_id", "mass", "b_a_ratio", "c_a_ratio", "triaxiality", "particle_count"]
            assert df["halo_id"].tolist() == [1, 2]
            assert df["b_a_ratio"].tolist() == [0.8, 0.5]
            assert df["c_a_ratio"].tolist() == [0.6, 0.3]
    
    def test_write_halo_shapes_csv_empty(self):
        """Test writing empty halo shapes CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_halo_shapes.csv"
            
            write_halo_shapes_csv([], output_path)
            
            assert output_path.exists()
            
            # Read back and verify headers exist
            df = pd.read_csv(output_path)
            
            assert len(df) == 0
            assert list(df.columns) == ["halo_id", "mass", "b_a_ratio", "c_a_ratio", "triaxiality", "particle_count"]
    
    def test_write_exclusion_log(self):
        """Test writing exclusion log to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_exclusion_log.json"
            
            records = [
                {
                    "halo_id": 1,
                    "excluded": True,
                    "exclusion_reason": "Low particle count",
                    "particle_count": 5000
                },
                {
                    "halo_id": 2,
                    "excluded": True,
                    "exclusion_reason": "Invalid shape metrics",
                    "b_a_ratio": 1.5
                }
            ]
            
            write_exclusion_log(records, output_path)
            
            assert output_path.exists()
            
            # Read back and verify
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_excluded"] == 2
            assert len(data["excluded_haloes"]) == 2
            assert data["excluded_haloes"][0]["halo_id"] == 1
            assert data["excluded_haloes"][1]["halo_id"] == 2
    
    def test_write_exclusion_log_empty(self):
        """Test writing empty exclusion log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_exclusion_log.json"
            
            write_exclusion_log([], output_path)
            
            assert output_path.exists()
            
            # Read back and verify
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_excluded"] == 0
            assert len(data["excluded_haloes"]) == 0

@pytest.mark.integration
class TestPipelineRunnerFull:
    """Full integration tests for the pipeline."""

    @patch('processing.pipeline_runner.fetch_tng_halo_data')
    def test_run_pipeline_with_mock_data(self, mock_fetch):
        """Test full pipeline run with mocked TNG data."""
        # Mock TNG data
        mock_halo_data = [
            {
                "halo_id": 1,
                "num_particles": 15000,
                "pos": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "mass": 1.0e12,
                "vel": [[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]
            },
            {
                "halo_id": 2,
                "num_particles": 5000,  # Should be excluded
                "pos": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "mass": 2.0e12,
                "vel": [[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0]]
            }
        ]
        
        mock_fetch.return_value = mock_halo_data
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run pipeline
            stats = run_pipeline(
                snapshot_id=0,
                chunk_size=10,
                min_particles=10000,
                output_dir=tmpdir
            )
            
            # Verify results
            assert stats["total_haloes"] == 2
            assert stats["valid_haloes"] == 1
            assert stats["excluded_haloes"] == 1
            
            # Verify output files exist
            csv_path = Path(tmpdir) / "halo_shapes.csv"
            json_path = Path(tmpdir) / "exclusion_log.json"
            
            assert csv_path.exists()
            assert json_path.exists()
            
            # Verify CSV content
            df = pd.read_csv(csv_path)
            assert len(df) == 1
            assert df["halo_id"].iloc[0] == 1
            
            # Verify JSON content
            with open(json_path, 'r') as f:
                exclusion_data = json.load(f)
            
            assert exclusion_data["total_excluded"] == 1
            assert exclusion_data["excluded_haloes"][0]["halo_id"] == 2
            assert "Low particle count" in exclusion_data["excluded_haloes"][0]["exclusion_reason"]