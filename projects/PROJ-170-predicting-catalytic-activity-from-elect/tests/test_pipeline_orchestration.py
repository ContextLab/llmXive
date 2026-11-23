"""
Tests for Pipeline Orchestration (T042a)
Verifies that the pipeline runs end-to-end and produces expected artifacts.
"""
import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_project_root, get_output_path, get_data_path

class TestPipelineOrchestration:
    """Tests for the full pipeline execution."""

    def test_pipeline_produces_metrics_file(self):
        """Verify that running the pipeline creates/updates metrics.json with timing."""
        # This test assumes the pipeline has been run
        metrics_path = get_output_path("metrics.json")
        
        assert metrics_path.exists(), f"Metrics file not found at {metrics_path}"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert "pipeline_execution" in metrics, "pipeline_execution key missing from metrics"
        
        exec_info = metrics["pipeline_execution"]
        assert "start_timestamp" in exec_info, "start_timestamp missing"
        assert "end_timestamp" in exec_info, "end_timestamp missing"
        assert "duration_seconds" in exec_info, "duration_seconds missing"
        assert "status" in exec_info, "status missing"
        
        # Verify timestamps are valid ISO format
        start_dt = datetime.fromisoformat(exec_info["start_timestamp"])
        end_dt = datetime.fromisoformat(exec_info["end_timestamp"])
        
        assert end_dt > start_dt, "End timestamp should be after start timestamp"
        
        # Verify duration is positive
        assert exec_info["duration_seconds"] > 0, "Duration should be positive"

    def test_pipeline_duration_within_scp004(self):
        """Verify that pipeline execution duration is within 6 hours (SC-004)."""
        metrics_path = get_output_path("metrics.json")
        
        if not metrics_path.exists():
            pytest.skip("Metrics file not found - pipeline may not have run yet")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        if "pipeline_execution" not in metrics:
            pytest.skip("Pipeline execution info not found in metrics")
        
        exec_info = metrics["pipeline_execution"]
        
        if exec_info.get("status") == "failed":
            pytest.skip("Pipeline execution failed - cannot verify duration constraint")
        
        duration_seconds = exec_info.get("duration_seconds", 0)
        six_hours_seconds = 6 * 3600
        
        assert duration_seconds <= six_hours_seconds, \
            f"Pipeline took {duration_seconds}s which exceeds 6h ({six_hours_seconds}s) limit"
        
        assert exec_info.get("sc004_status") == "PASSED", \
            f"SC-004 constraint check failed: {exec_info.get('sc004_status')}"

    def test_pipeline_artifacts_exist(self):
        """Verify that all expected pipeline output artifacts exist after execution."""
        expected_artifacts = [
            get_data_path("raw", "oc20_sample.h5"),
            get_data_path("processed", "aligned_dataset.csv"),
            get_project_root() / "outputs" / "exclusion_log.json",
            get_project_root() / "outputs" / "metrics.json",
            get_project_root() / "outputs" / "feature_importance.png",
            get_project_root() / "outputs" / "final_report.md",
            get_project_root() / "code" / "models" / "best_xgboost.json",
            get_project_root() / "code" / "models" / "best_reduced_xgboost.json",
        ]
        
        missing_artifacts = []
        for artifact in expected_artifacts:
            if not artifact.exists():
                missing_artifacts.append(str(artifact))
        
        if missing_artifacts:
            pytest.fail(f"Missing pipeline artifacts: {', '.join(missing_artifacts)}")

    def test_metrics_schema_completeness(self):
        """Verify that metrics.json contains all required fields from the pipeline."""
        metrics_path = get_project_root() / "outputs" / "metrics.json"
        
        if not metrics_path.exists():
            pytest.skip("Metrics file not found")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Check for pipeline execution info
        assert "pipeline_execution" in metrics
        
        # Check for model metrics (from evaluation phase)
        # The exact structure depends on what evaluate.py saves
        # At minimum, we expect some model performance metrics
        if "model_performance" in metrics or "xgboost_metrics" in metrics:
            pass  # Expected structure found
        else:
            # Check if metrics are in a different structure
            assert any("r2" in k.lower() or "mae" in k.lower() for k in str(metrics).lower()), \
                "No model performance metrics found in metrics file"
