"""
Unit tests for T123: Document Power Analysis Sample Size Limitations.
Verifies that power_report.md contains required strings regarding N=30 and statistical power.
"""
import pytest
import json
import pandas as pd
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_power_report import generate_power_report_md

def test_below_threshold_includes_limitation_text(tmp_path):
    """Test that report includes limitation text when N < 30."""
    output_file = tmp_path / "power_report.md"
    
    power_data = {
        "power": 0.45,
        "required_N": 45,
        "effect_size": 0.15,
        "current_n": 15,  # Below 30
        "flag": "low_power"
    }
    
    metrics_summary = pd.DataFrame({
        "metric": ["completion_time"],
        "F_stat": [2.5],
        "p_val": [0.04],
        "corrected_p": [0.04]
    })
    
    generate_power_report_md(power_data, metrics_summary, str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text()
    
    # Verification requirements from T123
    assert "N=30" in content, "Report must mention the constitutional threshold N=30"
    assert "statistical power" in content.lower(), "Report must discuss statistical power"
    assert "below" in content.lower(), "Report must indicate sample size is below threshold"
    assert "implications" in content.lower(), "Report must explain implications"
    assert "Type II Error" in content, "Report must mention Type II error risk"

def test_above_threshold_includes_met_text(tmp_path):
    """Test that report indicates threshold met when N >= 30."""
    output_file = tmp_path / "power_report.md"
    
    power_data = {
        "power": 0.85,
        "required_N": 25,
        "effect_size": 0.25,
        "current_n": 35,  # Above 30
        "flag": "sufficient"
    }
    
    metrics_summary = pd.DataFrame({
        "metric": ["completion_time"],
        "F_stat": [5.2],
        "p_val": [0.01],
        "corrected_p": [0.01]
    })
    
    generate_power_report_md(power_data, metrics_summary, str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text()
    
    assert "N=30" in content
    assert "statistical power" in content.lower()
    assert "meets" in content.lower() or "exceeds" in content.lower()

def test_report_structure(tmp_path):
    """Verify the report structure is consistent."""
    output_file = tmp_path / "power_report.md"
    
    power_data = {
        "power": 0.50,
        "required_N": 40,
        "effect_size": 0.20,
        "current_n": 20,
        "flag": "low_power"
    }
    
    metrics_summary = pd.DataFrame({
        "metric": ["error_count"],
        "F_stat": [1.2],
        "p_val": [0.25],
        "corrected_p": [0.25]
    })
    
    generate_power_report_md(power_data, metrics_summary, str(output_file))
    
    content = output_file.read_text()
    
    # Check for standard sections
    assert "# Power Analysis Report" in content
    assert "## Statistical Power Results" in content
    assert "## Sample Size Limitation Analysis" in content
    assert "## Methodology" in content
    assert "Constitution Principle VII" in content