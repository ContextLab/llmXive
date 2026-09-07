"""
Integration test for the full pipeline.
"""
import pytest
import os
from pathlib import Path
import subprocess
import sys

def test_full_pipeline_execution():
    """Test that the full pipeline runs and produces artifacts."""
    # Run the main pipeline
    result = subprocess.run(
        [sys.executable, "-m", "code.main"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    # Check exit code
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    
    # Check artifacts
    artifacts = [
        "data/processed/baseline_metrics.json",
        "data/processed/cleaned_metrics.json",
        "data/processed/null_fpr_metrics.json",
        "data/processed/comparison_report.json"
    ]
    
    for artifact in artifacts:
        path = Path(__file__).parent.parent.parent / artifact
        assert path.exists(), f"Artifact missing: {artifact}"
        assert path.stat().st_size > 0, f"Artifact empty: {artifact}"
