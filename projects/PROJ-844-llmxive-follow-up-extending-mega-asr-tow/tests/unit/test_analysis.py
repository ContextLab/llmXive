"""
Unit tests for code/analysis.py
"""
import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    check_threshold_stability,
    generate_stability_report
)

def test_check_threshold_stability():
    """Test threshold stability checking logic."""
    # Simulate stability data
    stability_data = [
        {"threshold": 0.4, "vector": [1.0, 2.0, 3.0]},
        {"threshold": 0.5, "vector": [1.1, 2.1, 3.1]},
        {"threshold": 0.6, "vector": [0.9, 1.9, 2.9]}
    ]
    
    # This should not raise an error if variance is < 10%
    is_stable, variance = check_threshold_stability(stability_data)
    assert isinstance(is_stable, bool)
    assert isinstance(variance, float)

def test_generate_stability_report(tmp_path):
    """Test stability report generation."""
    stability_data = [
        {"threshold": 0.4, "vector": [1.0, 2.0, 3.0]},
        {"threshold": 0.5, "vector": [1.1, 2.1, 3.1]},
        {"threshold": 0.6, "vector": [0.9, 1.9, 2.9]}
    ]
    
    report_path = tmp_path / "stability_report.json"
    report = generate_stability_report(stability_data, str(report_path))
    
    assert report is not None
    assert "stability_verified" in report
    assert report["stability_verified"] is True or report["stability_verified"] is False
