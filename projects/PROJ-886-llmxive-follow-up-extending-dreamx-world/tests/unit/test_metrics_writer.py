"""
Unit tests for the metrics writer module (T026).

These tests verify:
1. Correct CSV schema generation
2. Proper handling of null values (empty strings in CSV)
3. Round-trip consistency (write -> load)
4. Error handling for missing keys
"""

import pytest
import os
import csv
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import the module under test
from code.analysis.metrics_writer import (
    write_metrics_csv,
    load_metrics_csv,
    METRICS_CSV_COLUMNS
)

class TestMetricsWriterSchema:
    """Test the CSV schema definition and structure."""

    def test_schema_columns_defined(self):
        """Verify that the schema columns are correctly defined."""
        expected_columns = [
            "trajectory_id", "model_type", "convergence", 
            "sfm_failure_reason", "mae_position", "mae_rotation",
            "scale_drift", "generation_time_sec", "sfm_time_sec"
        ]
        assert METRICS_CSV_COLUMNS == expected_columns
        assert len(METRICS_CSV_COLUMNS) == 9

    def test_csv_header_written(self, tmp_path):
        """Verify that the CSV file is written with the correct header."""
        output_path = tmp_path / "test_metrics.csv"
        results = [
            {
                "trajectory_id": "traj_001",
                "model_type": "DreamX-Lite",
                "convergence": True,
                "sfm_failure_reason": None,
                "mae_position": 0.1234,
                "mae_rotation": 0.0567,
                "scale_drift": 0.0001,
                "generation_time_sec": 15.5,
                "sfm_time_sec": 8.2
            }
        ]
        
        write_metrics_csv(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == METRICS_CSV_COLUMNS

class TestNullHandling:
    """Test handling of null values (SfM failures) as per T025."""

    def test_null_values_become_empty_strings(self, tmp_path):
        """Verify that None values are written as empty strings in CSV."""
        output_path = tmp_path / "null_test.csv"
        results = [
            {
                "trajectory_id": "traj_fail",
                "model_type": "Baseline",
                "convergence": False,
                "sfm_failure_reason": "insufficient features",
                "mae_position": None,
                "mae_rotation": None,
                "scale_drift": None,
                "generation_time_sec": 12.0,
                "sfm_time_sec": 5.0
            }
        ]
        
        write_metrics_csv(results, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
            # Verify that null metrics are empty strings
            assert row["mae_position"] == ""
            assert row["mae_rotation"] == ""
            assert row["scale_drift"] == ""
            # Non-null values should be preserved
            assert row["sfm_failure_reason"] == "insufficient features"
            assert row["convergence"] == "False"

    def test_load_restores_none_values(self, tmp_path):
        """Verify that loading a CSV restores None for empty cells."""
        output_path = tmp_path / "roundtrip.csv"
        original_results = [
            {
                "trajectory_id": "traj_001",
                "model_type": "DreamX-Lite",
                "convergence": True,
                "sfm_failure_reason": None,
                "mae_position": 0.5,
                "mae_rotation": 0.1,
                "scale_drift": 0.0,
                "generation_time_sec": 10.0,
                "sfm_time_sec": 5.0
            },
            {
                "trajectory_id": "traj_002",
                "model_type": "Baseline",
                "convergence": False,
                "sfm_failure_reason": "out of memory",
                "mae_position": None,
                "mae_rotation": None,
                "scale_drift": None,
                "generation_time_sec": 20.0,
                "sfm_time_sec": 10.0
            }
        ]
        
        write_metrics_csv(original_results, output_path)
        loaded_results = load_metrics_csv(output_path)
        
        assert len(loaded_results) == 2
        
        # Check first row (success)
        assert loaded_results[0]["mae_position"] == 0.5
        assert loaded_results[0]["sfm_failure_reason"] is None
        
        # Check second row (failure)
        assert loaded_results[1]["mae_position"] is None
        assert loaded_results[1]["sfm_failure_reason"] == "out of memory"
        assert loaded_results[1]["convergence"] is False

class TestValidation:
    """Test input validation and error handling."""

    def test_missing_keys_raise_error(self, tmp_path):
        """Verify that missing keys in results raise ValueError."""
        output_path = tmp_path / "invalid.csv"
        results = [
            {
                "trajectory_id": "traj_001",
                # Missing other required keys
            }
        ]
        
        with pytest.raises(ValueError) as exc_info:
            write_metrics_csv(results, output_path)
        
        assert "missing keys" in str(exc_info.value)

    def test_empty_results_creates_empty_file(self, tmp_path):
        """Verify that empty results list creates a file with only header."""
        output_path = tmp_path / "empty.csv"
        write_metrics_csv([], output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1  # Only header
            assert "trajectory_id" in lines[0]

class TestAppendMode:
    """Test append functionality."""

    def test_append_adds_rows(self, tmp_path):
        """Verify that append mode adds rows without overwriting."""
        output_path = tmp_path / "append.csv"
        
        # Write initial data
        results1 = [
            {
                "trajectory_id": "traj_001",
                "model_type": "DreamX-Lite",
                "convergence": True,
                "sfm_failure_reason": None,
                "mae_position": 0.1,
                "mae_rotation": 0.01,
                "scale_drift": 0.0001,
                "generation_time_sec": 10.0,
                "sfm_time_sec": 5.0
            }
        ]
        write_metrics_csv(results1, output_path, append=False)
        
        # Append more data
        results2 = [
            {
                "trajectory_id": "traj_002",
                "model_type": "Baseline",
                "convergence": True,
                "sfm_failure_reason": None,
                "mae_position": 0.2,
                "mae_rotation": 0.02,
                "scale_drift": 0.0002,
                "generation_time_sec": 12.0,
                "sfm_time_sec": 6.0
            }
        ]
        write_metrics_csv(results2, output_path, append=True)
        
        loaded = load_metrics_csv(output_path)
        assert len(loaded) == 2
        assert loaded[0]["trajectory_id"] == "traj_001"
        assert loaded[1]["trajectory_id"] == "traj_002"

class TestIntegration:
    """Integration test for 50 trajectories as per T026 requirements."""

    def test_50_trajectory_write_load(self, tmp_path):
        """Write and load 50 trajectories to verify schema and null handling."""
        output_path = tmp_path / "metrics_50.csv"
        
        # Generate 50 trajectories with mixed success/failure
        results = []
        for i in range(50):
            is_fail = i % 5 == 0  # 20% failure rate
            results.append({
                "trajectory_id": f"traj_{i:04d}",
                "model_type": "DreamX-Lite" if i % 2 == 0 else "Baseline",
                "convergence": not is_fail,
                "sfm_failure_reason": "insufficient features" if is_fail else None,
                "mae_position": None if is_fail else round(i * 0.01, 4),
                "mae_rotation": None if is_fail else round(i * 0.001, 4),
                "scale_drift": None if is_fail else round(i * 0.0001, 6),
                "generation_time_sec": 15.0,
                "sfm_time_sec": 8.0
            })
        
        # Write
        write_metrics_csv(results, output_path)
        
        # Verify file exists and has correct structure
        assert output_path.exists()
        loaded = load_metrics_csv(output_path)
        
        # Check count
        assert len(loaded) == 50
        
        # Check null handling
        failure_count = sum(1 for r in loaded if r["convergence"] is False)
        assert failure_count == 10  # 50 / 5 = 10 failures
        
        for r in loaded:
            if r["convergence"] is False:
                assert r["mae_position"] is None
                assert r["mae_rotation"] is None
                assert r["scale_drift"] is None
                assert r["sfm_failure_reason"] is not None
            else:
                assert r["mae_position"] is not None
                assert r["mae_rotation"] is not None
                assert r["scale_drift"] is not None
                assert r["sfm_failure_reason"] is None