"""
Tests for T011b: Legacy metrics generation.
"""
import json
import os
import sys
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.generate_legacy_metrics import main

@pytest.fixture
def legacy_metrics_path():
    return os.path.join(project_root, "data", "processed", "legacy_metrics.json")

def test_legacy_metrics_file_exists(legacy_metrics_path):
    """Test that the legacy metrics file is created."""
    assert os.path.exists(legacy_metrics_path), f"File not found: {legacy_metrics_path}"

def test_legacy_metrics_content(legacy_metrics_path):
    """Test that the legacy metrics file contains the correct static content."""
    with open(legacy_metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert data["is_legacy"] is True
    assert data["reason"] == "Chi-Square invalid for n=6; replaced by per-draw metrics"
    assert data["metric_replaced"] == "draw_uniformity_deviation"
    assert data["replacement"] == "birthday_cluster_ratio, consecutive_pattern_count"

def test_legacy_metrics_json_validity(legacy_metrics_path):
    """Test that the file is valid JSON."""
    try:
        with open(legacy_metrics_path, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in legacy_metrics.json: {e}")
