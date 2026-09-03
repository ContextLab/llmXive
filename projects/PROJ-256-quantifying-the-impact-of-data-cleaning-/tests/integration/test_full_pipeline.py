import pytest
import subprocess
import sys
from pathlib import Path
import json

def test_full_pipeline_execution():
    """Test that the full pipeline runs and produces artifacts."""
    # Run the pipeline
    result = subprocess.run(
        [sys.executable, "-m", "code.main", "all"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    # Check exit code
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    
    # Check artifacts exist
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    
    baseline_file = processed_dir / "baseline_metrics.json"
    cleaned_file = processed_dir / "cleaned_metrics.json"
    
    assert baseline_file.exists(), "baseline_metrics.json not found"
    assert cleaned_file.exists(), "cleaned_metrics.json not found"
    
    # Check files are not empty
    with open(baseline_file) as f:
        baseline_data = json.load(f)
        assert baseline_data, "baseline_metrics.json is empty"
    
    with open(cleaned_file) as f:
        cleaned_data = json.load(f)
        assert cleaned_data, "cleaned_metrics.json is empty"
