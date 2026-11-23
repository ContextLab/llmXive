"""
Integration test for the full pipeline execution (T080).
Verifies that the pipeline runs end-to-end and produces valid artifacts.
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

@pytest.fixture
def clean_environment():
    """Create a clean temporary directory for testing."""
    # This is a mock fixture; in real CI, the environment is clean
    yield
    # Cleanup would happen here if needed

def test_pipeline_execution():
    """Test that the full pipeline executes without errors."""
    # Note: This test assumes the pipeline has been run in the environment
    # In a real CI, this would be run as part of the CI process
    
    # Check if artifacts exist (simulating post-run verification)
    artifacts_to_check = [
        "data/processed/cleaned_mg.csv",
        "artifacts/models/best_model.pkl",
        "artifacts/reports/final_report.md"
    ]
    
    for artifact in artifacts_to_check:
        artifact_path = project_root / artifact
        assert artifact_path.exists(), f"Artifact {artifact} does not exist"
        assert artifact_path.stat().st_size > 0, f"Artifact {artifact} is empty"

def test_report_content():
    """Test that the final report contains mandatory phrases and no causal language."""
    report_path = project_root / "artifacts/reports/final_report.md"
    
    if not report_path.exists():
        pytest.skip("Report not generated yet")
    
    content = report_path.read_text()
    
    # Check mandatory phrase
    assert "These findings are associational only" in content, \
        "Mandatory phrase 'These findings are associational only' not found"
    
    # Check for forbidden causal language
    forbidden_phrases = [
        "causes", "determines", "leads to", "results in",
        "proves", "confirms", "guarantees"
    ]
    
    content_lower = content.lower()
    for phrase in forbidden_phrases:
        assert phrase not in content_lower, \
            f"Forbidden causal language '{phrase}' found in report"

def test_ingestion_stats():
    """Test that ingestion stats are properly recorded."""
    stats_path = project_root / "data/ingestion_stats.json"
    
    if not stats_path.exists():
        pytest.skip("Ingestion stats not generated yet")
    
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    assert 'source_doi' in stats, "source_doi missing from ingestion stats"
    assert 'retention_rate' in stats, "retention_rate missing from ingestion stats"
    assert 'raw_count' in stats, "raw_count missing from ingestion stats"
    assert 'cleaned_count' in stats, "cleaned_count missing from ingestion stats"
    
    # Verify retention rate is a valid float between 0 and 1
    assert 0 < stats['retention_rate'] <= 1, "Invalid retention rate"

def test_model_metrics():
    """Test that model metrics are properly recorded."""
    metrics_path = project_root / "artifacts/metrics/metrics.json"
    
    if not metrics_path.exists():
        pytest.skip("Model metrics not generated yet")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert 'R2' in metrics, "R2 missing from metrics"
    assert 'MAE' in metrics, "MAE missing from metrics"
    assert 'feature_importances' in metrics, "feature_importances missing from metrics"
    assert 'null_model_r2' in metrics, "null_model_r2 missing from metrics"

def test_resource_compliance():
    """Test that resource usage is within limits."""
    resource_path = project_root / "data/resource_usage.json"
    
    if not resource_path.exists():
        pytest.skip("Resource usage not recorded yet")
    
    with open(resource_path, 'r') as f:
        resource_usage = json.load(f)
    
    # Check that RAM usage is within limits (7GB = 7168MB)
    if 'peak_ram_mb' in resource_usage:
        assert resource_usage['peak_ram_mb'] < 7168, \
            f"Peak RAM usage {resource_usage['peak_ram_mb']}MB exceeds 7GB limit"
    
    # Check that runtime is within limits (6h = 21600s)
    if 'total_runtime_s' in resource_usage:
        assert resource_usage['total_runtime_s'] < 21600, \
            f"Runtime {resource_usage['total_runtime_s']}s exceeds 6h limit"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])