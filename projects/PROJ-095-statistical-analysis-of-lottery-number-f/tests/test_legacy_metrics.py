"""
Tests for T011b: Legacy Metrics Generation.

Verifies that the legacy_metrics.json file is created with the correct static content
documenting the rejection of the invalid Chi-Square metric.
"""
import json
import os
import subprocess
import pytest

LEGACY_FILE_PATH = "data/processed/legacy_metrics.json"

def test_legacy_metrics_file_exists():
    """Test that the legacy_metrics.json file is created."""
    # Run the generation script first to ensure the file exists
    result = subprocess.run(
        ["python", "code/generate_legacy_metrics.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert os.path.exists(LEGACY_FILE_PATH), f"File {LEGACY_FILE_PATH} does not exist"

def test_legacy_metrics_content():
    """Test that the legacy_metrics.json file contains the correct static content."""
    # Ensure the file exists
    if not os.path.exists(LEGACY_FILE_PATH):
        subprocess.run(
            ["python", "code/generate_legacy_metrics.py"],
            capture_output=True,
            check=True
        )
    
    with open(LEGACY_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Verify the exact static content required by T011b
    assert data["is_legacy"] is True
    assert data["reason"] == "Chi-Square invalid for n=6; replaced by per-draw metrics"
    assert data["metric_replaced"] == "draw_uniformity_deviation"
    assert data["replacement"] == "birthday_cluster_ratio, consecutive_pattern_count"

def test_legacy_metrics_json_valid():
    """Test that the output is valid JSON."""
    if not os.path.exists(LEGACY_FILE_PATH):
        subprocess.run(
            ["python", "code/generate_legacy_metrics.py"],
            capture_output=True,
            check=True
        )
    
    try:
        with open(LEGACY_FILE_PATH, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"File {LEGACY_FILE_PATH} is not valid JSON: {e}")