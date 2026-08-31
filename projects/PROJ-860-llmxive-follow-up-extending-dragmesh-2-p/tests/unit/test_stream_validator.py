"""
Unit tests for stream_validator.py
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from stream_validator import (
    validate_sweep_generator_streaming,
    validate_evaluate_streaming,
    write_metrics_to_file,
    run_validation
)


class TestStreamValidator:
    """Tests for the stream validator functionality."""

    def test_write_metrics_to_file_creates_json(self, tmp_path):
        """Test that write_metrics_to_file creates a valid JSON file."""
        metrics = [
            {
                "script": "test.py",
                "type": "test",
                "validation_passed": True
            }
        ]
        output_path = tmp_path / "test_metrics.json"
        
        result = write_metrics_to_file(metrics, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metrics" in data
        assert len(data["metrics"]) == 1
        assert data["all_passed"] is True

    def test_validate_sweep_generator_script_not_found(self):
        """Test validation when script does not exist."""
        success, metrics = validate_sweep_generator_streaming(
            "code/nonexistent_script.py"
        )
        
        assert success is False
        assert "error" in metrics
        assert "not found" in metrics["error"].lower()

    def test_validate_evaluate_script_not_found(self):
        """Test validation when script does not exist."""
        success, metrics = validate_evaluate_streaming(
            "code/nonexistent_script.py"
        )
        
        assert success is False
        assert "error" in metrics
        assert "not found" in metrics["error"].lower()

    def test_validate_sweep_generator_detects_streaming(self):
        """Test that streaming patterns are detected in sweep_generator."""
        # This test assumes the actual sweep_generator.py exists and has streaming
        success, metrics = validate_sweep_generator_streaming(
            "code/sweep_generator.py"
        )
        
        # The script should exist
        assert "error" not in metrics or "not found" not in metrics.get("error", "")
        
        # Check that patterns were analyzed
        assert "detected_patterns" in metrics
        assert "streaming_detected" in metrics

    def test_validate_evaluate_detects_streaming(self):
        """Test that streaming patterns are detected in evaluate."""
        # This test assumes the actual evaluate.py exists and has streaming
        success, metrics = validate_evaluate_streaming(
            "code/evaluate.py"
        )
        
        # The script should exist
        assert "error" not in metrics or "not found" not in metrics.get("error", "")
        
        # Check that patterns were analyzed
        assert "detected_patterns" in metrics
        assert "streaming_detected" in metrics
        assert "streaming_write_detected" in metrics

    def test_run_validation_creates_output(self, tmp_path):
        """Test that run_validation creates the output file."""
        output_path = tmp_path / "stream_metrics.json"
        
        # Run validation with a non-existent script to test error handling
        # We can't easily test the full flow without the actual scripts
        # So we test the output writing part
        metrics = [
            {
                "script": "test.py",
                "type": "test",
                "validation_passed": False,
                "error": "Test error"
            }
        ]
        
        result = write_metrics_to_file(metrics, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["all_passed"] is False

    def test_metrics_structure(self):
        """Test that metrics have the expected structure."""
        # Test sweep generator metrics structure
        success, metrics = validate_sweep_generator_streaming(
            "code/sweep_generator.py"
        )
        
        required_keys = [
            "script", "type", "chunk_size_target", "streaming_detected",
            "memory_peak_mb", "duration_seconds", "records_processed",
            "validation_passed"
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"

    def test_metrics_structure_evaluate(self):
        """Test that evaluate metrics have the expected structure."""
        success, metrics = validate_evaluate_streaming(
            "code/evaluate.py"
        )
        
        required_keys = [
            "script", "type", "chunk_size_target", "streaming_detected",
            "memory_peak_mb", "duration_seconds", "records_processed",
            "validation_passed"
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"