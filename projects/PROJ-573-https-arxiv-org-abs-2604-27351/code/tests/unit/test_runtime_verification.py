import os
import time
import tempfile
import yaml
from pathlib import Path
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# We need to temporarily override the DATA_DIR constant in the module under test
# or mock the file system interactions.

from src.evaluation.runtime_verification import (
    load_runtime_metrics,
    save_runtime_metrics,
    verify_per_task_inference,
    record_task_verification,
    generate_runtime_summary,
    PER_TASK_TIMEOUT_SECONDS
)

class TestRuntimeVerification:
    
    @pytest.fixture
    def temp_metrics_file(self, tmp_path):
        """Create a temporary file path for metrics."""
        metrics_file = tmp_path / "runtime_metrics.yaml"
        initial_data = {
            "per_task_verification": [],
            "metadata": {
                "threshold_per_task_seconds": PER_TASK_TIMEOUT_SECONDS,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        with open(metrics_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(initial_data, f)
        return metrics_file

    @patch("src.evaluation.runtime_verification.RUNTIME_METRICS_PATH")
    @patch("src.evaluation.runtime_verification.DATA_DIR")
    def test_load_runtime_metrics_existing(self, mock_data_dir, mock_metrics_path, temp_metrics_file):
        """Test loading metrics from an existing file."""
        mock_metrics_path.__truediv__.return_value = temp_metrics_file
        mock_metrics_path.exists.return_value = True
        
        metrics = load_runtime_metrics()
        
        assert "per_task_verification" in metrics
        assert metrics["per_task_verification"] == []
        
    @patch("src.evaluation.runtime_verification.RUNTIME_METRICS_PATH")
    @patch("src.evaluation.runtime_verification.DATA_DIR")
    def test_load_runtime_metrics_missing(self, mock_data_dir, mock_metrics_path):
        """Test loading metrics when file does not exist."""
        mock_metrics_path.exists.return_value = False
        
        metrics = load_runtime_metrics()
        
        assert "per_task_verification" in metrics
        assert metrics["per_task_verification"] == []
        assert metrics["metadata"]["threshold_per_task_seconds"] == PER_TASK_TIMEOUT_SECONDS

    def test_verify_per_task_inference_pass(self):
        """Test verification when time is within limit."""
        result = verify_per_task_inference("T001", 200.0)
        
        assert result["status"] == "PASS"
        assert result["task_id"] == "T001"
        assert result["actual_seconds"] == 200.0
        assert result["threshold_seconds"] == PER_TASK_TIMEOUT_SECONDS

    def test_verify_per_task_inference_fail(self):
        """Test verification when time exceeds limit."""
        result = verify_per_task_inference("T002", 400.0)
        
        assert result["status"] == "FAIL"
        assert result["task_id"] == "T002"
        assert result["actual_seconds"] == 400.0

    @patch("src.evaluation.runtime_verification.save_runtime_metrics")
    @patch("src.evaluation.runtime_verification.load_runtime_metrics")
    def test_record_task_verification_integration(self, mock_load, mock_save, temp_metrics_file):
        """Test the full record_task_verification flow."""
        initial_metrics = {
            "per_task_verification": [
                {"task_id": "T000", "status": "PASS", "actual_seconds": 100.0}
            ]
        }
        mock_load.return_value = initial_metrics
        
        result = record_task_verification("T055c", 250.0)
        
        # Verify the result is correct
        assert result["status"] == "PASS"
        assert result["task_id"] == "T055c"
        
        # Verify save was called with updated data
        assert mock_save.called
        saved_data = mock_save.call_args[0][0]
        assert len(saved_data["per_task_verification"]) == 2
        assert saved_data["per_task_verification"][1]["task_id"] == "T055c"

    @patch("src.evaluation.runtime_verification.load_runtime_metrics")
    def test_generate_runtime_summary(self, mock_load):
        """Test summary generation."""
        mock_load.return_value = {
            "per_task_verification": [
                {"task_id": "T001", "status": "PASS", "actual_seconds": 100.0},
                {"task_id": "T002", "status": "FAIL", "actual_seconds": 400.0},
                {"task_id": "T003", "status": "PASS", "actual_seconds": 200.0}
            ]
        }
        
        summary = generate_runtime_summary()
        
        assert summary["total_tasks_checked"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert abs(summary["pass_rate"] - (2/3)) < 0.01

    @patch("src.evaluation.runtime_verification.load_runtime_metrics")
    def test_generate_runtime_summary_empty(self, mock_load):
        """Test summary generation with no data."""
        mock_load.return_value = {"per_task_verification": []}
        
        summary = generate_runtime_summary()
        
        assert summary["total_tasks_checked"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["pass_rate"] == 0.0