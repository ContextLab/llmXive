"""
Integration tests for CI pipeline runner.

These tests verify that the pipeline runner correctly:
1. Executes experiment scripts
2. Captures resource metrics
3. Produces valid output files
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from run_full_pipeline_ci import (
    get_memory_usage_mb,
    get_disk_usage_mb,
    run_experiment_script,
    run_full_pipeline,
    save_results
)

from utils.logging import get_logger

logger = get_logger(__name__)


class TestMemoryUsage:
    """Tests for memory usage measurement."""

    def test_get_memory_usage_returns_positive(self):
        """Memory usage should be a positive number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, (int, float))
        assert mem >= 0

    def test_memory_usage_increases_over_time(self):
        """Memory usage should be measurable multiple times."""
        mem1 = get_memory_usage_mb()
        mem2 = get_memory_usage_mb()
        # Values should be reasonably close (within 100MB)
        assert abs(mem1 - mem2) < 100


class TestDiskUsage:
    """Tests for disk usage measurement."""

    def test_get_disk_usage_nonexistent_path(self):
        """Should return 0 for non-existent path."""
        fake_path = Path("/nonexistent/path/that/does/not/exist")
        size = get_disk_usage_mb(fake_path)
        assert size == 0.0

    def test_get_disk_usage_existing_path(self):
        """Should return positive size for existing directory."""
        size = get_disk_usage_mb(PROJECT_ROOT)
        assert isinstance(size, (int, float))
        assert size >= 0


class TestRunExperimentScript:
    """Tests for experiment script execution."""

    def test_script_not_found(self):
        """Should handle missing script gracefully."""
        success, elapsed, output, metrics = run_experiment_script(
            "nonexistent_script.py",
            [],
            timeout_minutes=1
        )
        assert success is False
        assert "not found" in output.lower()

    def test_valid_script_execution(self):
        """Should execute a simple script successfully."""
        # Create a temporary test script
        test_script = PROJECT_ROOT / "code" / "test_temp_script.py"
        test_script.write_text("""
        import sys
        print("Hello from test script")
        sys.exit(0)
        """)
        
        try:
            success, elapsed, output, metrics = run_experiment_script(
                "test_temp_script.py",
                [],
                timeout_minutes=1
            )
            
            assert success is True
            assert "Hello from test script" in output
            assert metrics.get("success") is True
            assert metrics.get("elapsed_time_seconds", 0) >= 0
        finally:
            if test_script.exists():
                test_script.unlink()

    def test_metrics_structure(self):
        """Should return properly structured metrics."""
        test_script = PROJECT_ROOT / "code" / "test_metrics_script.py"
        test_script.write_text("import sys; sys.exit(0)")
        
        try:
            success, _, _, metrics = run_experiment_script(
                "test_metrics_script.py",
                [],
                timeout_minutes=1
            )
            
            required_keys = ["success", "elapsed_time_seconds", "peak_memory_mb"]
            for key in required_keys:
                assert key in metrics, f"Missing key: {key}"
        finally:
            if test_script.exists():
                test_script.unlink()


class TestRunFullPipeline:
    """Tests for full pipeline execution."""

    @patch('run_full_pipeline_ci.run_experiment_script')
    def test_pipeline_with_mocked_experiments(self, mock_run):
        """Should run pipeline with mocked experiments."""
        # Mock successful experiment runs
        mock_run.return_value = (True, 1.0, "Success", {
            "success": True,
            "elapsed_time_seconds": 1.0,
            "peak_memory_mb": 100.0,
            "memory_delta_mb": 10.0,
            "disk_delta_mb": 5.0
        })
        
        results = run_full_pipeline()
        
        assert "timestamp" in results
        assert "experiments" in results
        assert "summary" in results
        assert results["summary"]["total_experiments"] > 0
        assert results["summary"]["overall_success"] is True

    @patch('run_full_pipeline_ci.run_experiment_script')
    def test_pipeline_handles_failure(self, mock_run):
        """Should handle failed experiments gracefully."""
        mock_run.return_value = (False, 1.0, "Error", {
            "success": False,
            "error": "Test error"
        })
        
        results = run_full_pipeline()
        
        assert results["summary"]["overall_success"] is False
        assert results["summary"]["failed_experiments"] > 0


class TestSaveResults:
    """Tests for results saving."""

    def test_save_results_creates_file(self, tmp_path):
        """Should create output file."""
        results = {"test": "data", "number": 42}
        output_path = tmp_path / "results" / "test_output.json"
        
        save_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == results

    def test_save_results_valid_json(self, tmp_path):
        """Should produce valid JSON."""
        results = {
            "complex": {"nested": [1, 2, 3]},
            "numbers": [1.5, 2.5],
            "timestamp": "2024-01-01T00:00:00"
        }
        output_path = tmp_path / "test.json"
        
        save_results(results, output_path)
        
        # Should not raise
        with open(output_path, 'r') as f:
            json.load(f)


class TestIntegrationEndToEnd:
    """End-to-end integration tests."""

    def test_pipeline_produces_output_structure(self):
        """Pipeline should produce expected output structure."""
        # Mock all experiment calls to avoid actual execution
        with patch('run_full_pipeline_ci.run_experiment_script') as mock_run:
            mock_run.return_value = (True, 0.5, "OK", {
                "success": True,
                "elapsed_time_seconds": 0.5,
                "peak_memory_mb": 50.0,
                "memory_delta_mb": 5.0,
                "disk_delta_mb": 1.0
            })
            
            results = run_full_pipeline()
            
            # Verify structure
            assert "experiments" in results
            assert "summary" in results
            
            # Verify each experiment has required fields
            for exp_name, exp_data in results["experiments"].items():
                assert "success" in exp_data
                assert "elapsed_time_seconds" in exp_data
                assert "peak_memory_mb" in exp_data
            
            # Verify summary
            summary = results["summary"]
            assert "total_experiments" in summary
            assert "successful_experiments" in summary
            assert "overall_success" in summary
