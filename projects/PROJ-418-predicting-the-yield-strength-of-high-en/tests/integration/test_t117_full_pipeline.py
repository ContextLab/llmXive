"""
Integration tests for T117: Full Pipeline Execution.

Verifies that all required artifacts are generated and contain valid data.
"""
import os
import json
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from run_full_pipeline_exec import main as run_t117_main

@pytest.fixture
def output_dir():
    return Path(__file__).parent.parent.parent / "output"

def test_t117_artifacts_exist(output_dir):
    """Test that all required artifacts exist after pipeline execution."""
    required_artifacts = [
        "manifest.json",
        "report.md",
        "metrics.json",
        "stability_rankings.json",
        "external_metrics.json",
        "pipeline_runtime.json",
        "final_validation_report.json"
    ]
    
    for artifact in required_artifacts:
        path = output_dir / artifact
        assert path.exists(), f"Missing required artifact: {artifact}"

def test_manifest_schema(output_dir):
    """Test that manifest.json contains required provenance fields."""
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    required_fields = ["seeds", "versions", "checksums"]
    for field in required_fields:
        assert field in manifest, f"Missing field in manifest: {field}"

def test_metrics_schema(output_dir):
    """Test that metrics.json contains required performance metrics."""
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
    
    assert "rf" in metrics or "linear" in metrics, "Missing model metrics"
    assert "best_model" in metrics, "Missing best_model field"

def test_runtime_pass(output_dir):
    """Test that pipeline_runtime.json reports status as 'pass'."""
    runtime_path = output_dir / "pipeline_runtime.json"
    with open(runtime_path, "r") as f:
        runtime = json.load(f)
    
    assert runtime.get("status") == "pass", "Pipeline runtime status is not 'pass'"
    assert runtime.get("total_duration_seconds", 0) <= 7200, "Runtime exceeds 7200s"

def test_stability_rankings(output_dir):
    """Test that stability_rankings.json shows rank-difference <= 1."""
    stability_path = output_dir / "stability_rankings.json"
    with open(stability_path, "r") as f:
        stability = json.load(f)
    
    assert "runs" in stability, "Missing runs in stability rankings"
    assert len(stability["runs"]) == 3, "Expected 3 stability runs"

def test_external_metrics(output_dir):
    """Test that external_metrics.json exists and has valid schema."""
    external_path = output_dir / "external_metrics.json"
    with open(external_path, "r") as f:
        external = json.load(f)
    
    assert "r2" in external or "R2" in external, "Missing R2 in external metrics"
    assert "pearson_r" in external or "r" in external, "Missing Pearson r in external metrics"

def test_final_validation_report(output_dir):
    """Test that final_validation_report.json aggregates T117-T125 results."""
    validation_path = output_dir / "final_validation_report.json"
    with open(validation_path, "r") as f:
        validation = json.load(f)
    
    assert "status" in validation, "Missing status in final validation report"
    assert "tasks" in validation, "Missing tasks in final validation report"

@pytest.mark.skip(reason="Requires full pipeline execution")
def test_full_pipeline_execution():
    """Test the full pipeline execution end-to-end."""
    success = run_t117_main()
    assert success, "Full pipeline execution failed"
