"""
Unit tests for flat object sensitivity analysis in T058.

Tests the new functionality added to code/stats/sensitivity.py
for handling flat object edge cases.
"""

import pytest
import os
import json
import tempfile
import csv
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats.sensitivity import (
    is_flat_object,
    classify_failure,
    run_flat_object_sensitivity_analysis,
    write_flat_object_sensitivity_csv,
    FLAT_OBJECT_EPSILON_VALUES,
    DEFAULT_FLAT_OBJECT_SENSITIVITY_PATH
)

# Sample test data
SAMPLE_TASK_INSTANCE_FLAT = {
    "task_id": "test_flat_001",
    "ground_truth_3d_params": {
        "dimensions": {"x": 1.0, "y": 1.0, "z": 0.0},
        "depth_variance": 0.0,
        "task_type": "occlusion"
    }
}

SAMPLE_TASK_INSTANCE_NON_FLAT = {
    "task_id": "test_nonflat_001",
    "ground_truth_3d_params": {
        "dimensions": {"x": 1.0, "y": 1.0, "z": 2.0},
        "depth_variance": 2.0,
        "task_type": "occlusion"
    }
}

SAMPLE_COMPARISON_RESULT_SUCCESS = {
    "task_id": "test_flat_001",
    "success_flag": True,
    "task_type": "occlusion",
    "wall_clock_time_ms": 100.0
}

SAMPLE_COMPARISON_RESULT_FAILURE = {
    "task_id": "test_flat_001",
    "success_flag": False,
    "task_type": "occlusion",
    "wall_clock_time_ms": 150.0
}

class TestIsFlatObject:
    """Tests for the is_flat_object function."""
    
    def test_flat_object_zero_variance(self):
        """Test that an object with zero depth variance is identified as flat."""
        task = SAMPLE_TASK_INSTANCE_FLAT
        assert is_flat_object(task, epsilon=0.0) is True
        assert is_flat_object(task, epsilon=0.01) is True
        assert is_flat_object(task, epsilon=0.1) is True
    
    def test_non_flat_object_high_variance(self):
        """Test that an object with high depth variance is not identified as flat."""
        task = SAMPLE_TASK_INSTANCE_NON_FLAT
        assert is_flat_object(task, epsilon=0.0) is False
        assert is_flat_object(task, epsilon=0.01) is False
        assert is_flat_object(task, epsilon=0.1) is False
        assert is_flat_object(task, epsilon=2.0) is True  # At the boundary
    
    def test_edge_case_epsilon_match(self):
        """Test behavior when depth variance exactly matches epsilon."""
        task = SAMPLE_TASK_INSTANCE_NON_FLAT.copy()
        task["ground_truth_3d_params"]["depth_variance"] = 0.05
        
        assert is_flat_object(task, epsilon=0.05) is True
        assert is_flat_object(task, epsilon=0.04) is False
        assert is_flat_object(task, epsilon=0.06) is True
    
    def test_missing_depth_variance_uses_dimensions(self):
        """Test fallback to dimensions when depth_variance is missing."""
        task = {
            "task_id": "test_missing",
            "ground_truth_3d_params": {
                "dimensions": {"x": 1.0, "y": 1.0, "z": 0.0}
            }
        }
        assert is_flat_object(task, epsilon=0.0) is True
    
    def test_missing_dimensions_defaults_to_zero(self):
        """Test that missing dimensions defaults to zero depth variance."""
        task = {
            "task_id": "test_missing_dims",
            "ground_truth_3d_params": {}
        }
        assert is_flat_object(task, epsilon=0.0) is True

class TestClassifyFailure:
    """Tests for the classify_failure function."""
    
    def test_success_not_classified_as_failure(self):
        """Test that successful tasks return 'success'."""
        result = SAMPLE_COMPARISON_RESULT_SUCCESS.copy()
        gt = SAMPLE_TASK_INSTANCE_FLAT["ground_truth_3d_params"]
        
        assert classify_failure("test_001", result, gt, epsilon=0.01) == "success"
    
    def test_flat_object_failure_classified_as_projection_loss(self):
        """Test that flat object failures are classified as projection_loss."""
        result = SAMPLE_COMPARISON_RESULT_FAILURE.copy()
        gt = SAMPLE_TASK_INSTANCE_FLAT["ground_truth_3d_params"]
        
        assert classify_failure("test_001", result, gt, epsilon=0.01) == "projection_loss"
    
    def test_non_flat_occlusion_failure_classified_as_projection_loss(self):
        """Test that non-flat occlusion failures are classified as projection_loss."""
        result = SAMPLE_COMPARISON_RESULT_FAILURE.copy()
        gt = SAMPLE_TASK_INSTANCE_NON_FLAT["ground_truth_3d_params"]
        
        assert classify_failure("test_001", result, gt, epsilon=0.01) == "projection_loss"
    
    def test_relative_task_failure_classified_as_action_restriction(self):
        """Test that relative task failures are classified as action_restriction."""
        result = SAMPLE_COMPARISON_RESULT_FAILURE.copy()
        gt = SAMPLE_TASK_INSTANCE_NON_FLAT["ground_truth_3d_params"].copy()
        gt["task_type"] = "relative"
        
        assert classify_failure("test_001", result, gt, epsilon=0.01) == "action_restriction"
    
    def test_unknown_task_type_classified_as_other(self):
        """Test that unknown task types are classified as 'other'."""
        result = SAMPLE_COMPARISON_RESULT_FAILURE.copy()
        gt = SAMPLE_TASK_INSTANCE_NON_FLAT["ground_truth_3d_params"].copy()
        gt["task_type"] = "unknown_type"
        
        assert classify_failure("test_001", result, gt, epsilon=0.01) == "other"

class TestRunFlatObjectSensitivityAnalysis:
    """Tests for the run_flat_object_sensitivity_analysis function."""
    
    def test_empty_dataset(self):
        """Test behavior with an empty dataset."""
        dataset = []
        comparison_results = []
        
        results = run_flat_object_sensitivity_analysis(
            dataset, comparison_results, epsilon_values=[0.0, 0.01]
        )
        
        assert len(results) == 2
        for r in results:
            assert r["flat_object_count"] == 0
            assert r["flat_failure_rate"] == 0.0
            assert r["non_flat_failure_rate"] == 0.0
    
    def test_all_flat_objects(self):
        """Test dataset where all objects are flat."""
        dataset = [SAMPLE_TASK_INSTANCE_FLAT]
        comparison_results = [SAMPLE_COMPARISON_RESULT_FAILURE]
        
        results = run_flat_object_sensitivity_analysis(
            dataset, comparison_results, epsilon_values=[0.0]
        )
        
        assert len(results) == 1
        assert results[0]["flat_object_count"] == 1
        assert results[0]["flat_object_failures"] == 1
        assert results[0]["flat_failure_rate"] == 1.0
        assert results[0]["non_flat_count"] == 0
    
    def test_mixed_flat_and_non_flat(self):
        """Test dataset with both flat and non-flat objects."""
        dataset = [SAMPLE_TASK_INSTANCE_FLAT, SAMPLE_TASK_INSTANCE_NON_FLAT]
        comparison_results = [
            SAMPLE_COMPARISON_RESULT_FAILURE.copy(),
            SAMPLE_COMPARISON_RESULT_SUCCESS.copy()
        ]
        comparison_results[1]["task_id"] = "test_nonflat_001"
        
        results = run_flat_object_sensitivity_analysis(
            dataset, comparison_results, epsilon_values=[0.0]
        )
        
        assert len(results) == 1
        assert results[0]["flat_object_count"] == 1
        assert results[0]["non_flat_count"] == 1
        assert results[0]["flat_failure_rate"] == 1.0
        assert results[0]["non_flat_failure_rate"] == 0.0
        assert results[0]["failure_rate_difference"] == 1.0

class TestWriteFlatObjectSensitivityCsv:
    """Tests for the write_flat_object_sensitivity_csv function."""
    
    def test_writes_correct_format(self):
        """Test that the CSV is written with correct headers and data."""
        sensitivity_results = [
            {
                "epsilon": 0.0,
                "flat_object_count": 10,
                "flat_object_successes": 5,
                "flat_object_failures": 5,
                "flat_failure_rate": 0.5,
                "non_flat_count": 20,
                "non_flat_successes": 15,
                "non_flat_failures": 5,
                "non_flat_failure_rate": 0.25,
                "failure_rate_difference": 0.25
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_flat_sensitivity.csv")
            
            write_flat_object_sensitivity_csv(sensitivity_results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 1
                row = rows[0]
                
                assert row["epsilon"] == "0.0"
                assert row["flat_object_count"] == "10"
                assert row["flat_failure_rate"] == "0.5"
                assert row["failure_rate_difference"] == "0.25"
    
    def test_creates_output_directory(self):
        """Test that the output directory is created if it doesn't exist."""
        sensitivity_results = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test_flat_sensitivity.csv")
            
            write_flat_object_sensitivity_csv(sensitivity_results, output_path)
            
            assert os.path.exists(output_path)

class TestIntegration:
    """Integration tests for the flat object sensitivity analysis."""
    
    def test_full_sensitivity_workflow(self):
        """Test the complete workflow from data to CSV output."""
        # Create sample dataset
        dataset = [
            SAMPLE_TASK_INSTANCE_FLAT,
            SAMPLE_TASK_INSTANCE_NON_FLAT
        ]
        
        # Create sample comparison results
        comparison_results = [
            SAMPLE_COMPARISON_RESULT_FAILURE.copy(),
            SAMPLE_COMPARISON_RESULT_SUCCESS.copy()
        ]
        comparison_results[1]["task_id"] = "test_nonflat_001"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "flat_object_sensitivity.csv")
            
            results = run_flat_object_sensitivity_analysis(
                dataset, comparison_results, epsilon_values=[0.0, 0.01, 0.05]
            )
            
            write_flat_object_sensitivity_csv(results, output_path)
            
            # Verify the output file
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 3  # Three epsilon values
                
                # Check that epsilon values are in the output
                epsilons = [float(row["epsilon"]) for row in rows]
                assert 0.0 in epsilons
                assert 0.01 in epsilons
                assert 0.05 in epsilons