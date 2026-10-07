"""
Unit tests for failure handling logic in inference pipeline.

Tests that inference failures are properly recorded in the results CSV
with status='failed', error_msg column, and NaN scores.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from inference.failure_handler import (
    append_failure_record,
    handle_inference_failure,
    RESULTS_CSV_PATH
)
from utils.errors import ResourceLimitError


class TestFailureHandler:
    """Test cases for failure handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Ensure the results directory exists
        RESULTS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing results file if it exists
        if RESULTS_CSV_PATH.exists():
            RESULTS_CSV_PATH.unlink()

    def teardown_method(self):
        """Clean up after tests."""
        # Remove test results file if it exists
        if RESULTS_CSV_PATH.exists():
            RESULTS_CSV_PATH.unlink()

    def test_append_failure_record_creates_file(self):
        """Test that append_failure_record creates the CSV file if it doesn't exist."""
        append_failure_record(
            case_id="test_001",
            variant_type="low",
            model_id="model_v1",
            error_msg="Test error message"
        )
        
        assert RESULTS_CSV_PATH.exists(), "Results CSV file should be created"
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 1, "Should have one record"
        assert df.iloc[0]['case_id'] == "test_001"
        assert df.iloc[0]['variant_type'] == "low"
        assert df.iloc[0]['model_id'] == "model_v1"
        assert df.iloc[0]['status'] == 'failed'
        assert df.iloc[0]['error_msg'] == "Test error message"
        assert pd.isna(df.iloc[0]['physics_score'])
        assert pd.isna(df.iloc[0]['consistency_score'])

    def test_append_failure_record_appends_to_existing(self):
        """Test that append_failure_record appends to existing CSV."""
        # Create initial file with one record
        append_failure_record(
            case_id="test_001",
            variant_type="low",
            model_id="model_v1",
            error_msg="First error"
        )
        
        # Append another record
        append_failure_record(
            case_id="test_002",
            variant_type="high",
            model_id="model_v2",
            error_msg="Second error"
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 2, "Should have two records"
        
        # Verify first record
        assert df.iloc[0]['case_id'] == "test_001"
        assert df.iloc[0]['status'] == 'failed'
        
        # Verify second record
        assert df.iloc[1]['case_id'] == "test_002"
        assert df.iloc[1]['status'] == 'failed'

    def test_handle_inference_failure_with_oom_error(self):
        """Test that OOM errors are properly handled and recorded."""
        oom_error = MemoryError("CUDA out of memory")
        
        handle_inference_failure(
            case_id="test_003",
            variant_type="medium",
            model_id="model_v3",
            exception=oom_error
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 1
        assert df.iloc[0]['status'] == 'failed'
        assert "MemoryError" in df.iloc[0]['error_msg']
        assert df.iloc[0]['case_id'] == "test_003"

    def test_handle_inference_failure_with_resource_limit_error(self):
        """Test that ResourceLimitError is properly handled."""
        resource_error = ResourceLimitError("RAM limit exceeded: 8.5GB > 6.5GB limit")
        
        handle_inference_failure(
            case_id="test_004",
            variant_type="high",
            model_id="model_v4",
            exception=resource_error
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 1
        assert df.iloc[0]['status'] == 'failed'
        assert "Resource limit exceeded" in df.iloc[0]['error_msg']

    def test_handle_inference_failure_with_runtime_error(self):
        """Test that RuntimeError is properly handled."""
        runtime_error = RuntimeError("Model loading failed: file not found")
        
        handle_inference_failure(
            case_id="test_005",
            variant_type="low",
            model_id="model_v5",
            exception=runtime_error
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 1
        assert df.iloc[0]['status'] == 'failed'
        assert "RuntimeError" in df.iloc[0]['error_msg']

    def test_all_score_columns_are_nan_for_failures(self):
        """Test that all score columns are NaN for failed inferences."""
        append_failure_record(
            case_id="test_006",
            variant_type="medium",
            model_id="model_v6",
            error_msg="Test error"
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        record = df.iloc[0]
        
        assert pd.isna(record['physics_score'])
        assert pd.isna(record['consistency_score'])
        assert pd.isna(record['motion_artifact_score'])
        assert pd.isna(record['ram_usage_gb'])
        assert pd.isna(record['duration_seconds'])

    def test_output_path_is_recorded_when_provided(self):
        """Test that output_path is recorded when provided."""
        partial_output = "/tmp/partial_output.mp4"
        
        append_failure_record(
            case_id="test_007",
            variant_type="high",
            model_id="model_v7",
            error_msg="Test error",
            output_path=partial_output
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert df.iloc[0]['output_path'] == partial_output

    def test_csv_columns_match_expected_schema(self):
        """Test that the CSV has all expected columns."""
        append_failure_record(
            case_id="test_008",
            variant_type="low",
            model_id="model_v8",
            error_msg="Test error"
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        expected_columns = [
            'case_id', 'variant_type', 'model_id', 'status', 'error_msg',
            'output_path', 'physics_score', 'consistency_score',
            'motion_artifact_score', 'ram_usage_gb', 'duration_seconds'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
        assert list(df.columns) == expected_columns, "Column order should match expected"

    def test_multiple_failures_same_case_different_models(self):
        """Test recording multiple failures for same case with different models."""
        for i, model_id in enumerate(['model_a', 'model_b', 'model_c']):
            append_failure_record(
                case_id=f"test_same_case",
                variant_type="medium",
                model_id=model_id,
                error_msg=f"Error for model {model_id}"
            )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 3
        
        # All should have same case_id but different model_ids
        assert all(df['case_id'] == "test_same_case")
        assert len(df['model_id'].unique()) == 3

    def test_large_error_message_handling(self):
        """Test that large error messages are handled correctly."""
        large_error = "Error: " + "x" * 10000  # 10KB error message
        
        append_failure_record(
            case_id="test_large",
            variant_type="high",
            model_id="model_large",
            error_msg=large_error
        )
        
        df = pd.read_csv(RESULTS_CSV_PATH)
        assert len(df) == 1
        assert len(df.iloc[0]['error_msg']) == len(large_error)
        assert df.iloc[0]['status'] == 'failed'
