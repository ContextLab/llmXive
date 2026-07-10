"""
Unit tests for the sensitivity report generator (T033).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from models.sensitivity_report_generator import (
    generate_report_content,
    load_sensitivity_results,
    load_model_info
)
from config import get_data_dir, get_output_dir

@pytest.fixture
def sample_sensitivity_results():
    """Sample sensitivity analysis results for testing."""
    return {
        "thresholds": [0.45, 0.50, 0.55],
        "metrics": [
            {"r2": 0.85, "mae": 0.12},
            {"r2": 0.83, "mae": 0.14},
            {"r2": 0.84, "mae": 0.13}
        ],
        "top_features": [
            ["HOMO_energy", "LUMO_energy", "band_gap"],
            ["HOMO_energy", "band_gap", "LUMO_energy"],
            ["HOMO_energy", "LUMO_energy", "band_gap"]
        ],
        "rank_stability": {
            "max_rank_change": 1,
            "is_stable": True
        }
    }

@pytest.fixture
def sample_model_info():
    """Sample model information for testing."""
    return {
        "model_type": "RandomForest",
        "best_params": {
            "n_estimators": 100,
            "max_depth": 20
        },
        "r2_scores": {"train": 0.92, "val": 0.85},
        "mae_scores": {"train": 0.08, "val": 0.12}
    }

def test_generate_report_content_basic(sample_sensitivity_results, sample_model_info):
    """Test that report content is generated with expected sections."""
    content = generate_report_content(sample_sensitivity_results, sample_model_info)
    
    # Check for required sections
    assert "# Sensitivity Analysis Report" in content
    assert "## Overview" in content
    assert "## Configuration" in content
    assert "## Model Summary" in content
    assert "## Sensitivity Analysis Results" in content
    assert "### Performance Metrics by Threshold" in content
    assert "### Rank Stability Analysis" in content
    assert "## Deviation Notes" in content
    assert "## Conclusion" in content
    
    # Check for specific values
    assert "0.45" in content
    assert "0.50" in content
    assert "0.55" in content
    assert "HOMO_energy" in content
    assert "RandomForest" in content

def test_generate_report_content_stable_case(sample_sensitivity_results, sample_model_info):
    """Test report generation for a stable rank change case."""
    sample_sensitivity_results["rank_stability"]["is_stable"] = True
    sample_sensitivity_results["rank_stability"]["max_rank_change"] = 1
    
    content = generate_report_content(sample_sensitivity_results, sample_model_info)
    
    assert "STABLE" in content
    assert "Change ≤ 1 position" in content

def test_generate_report_content_unstable_case(sample_sensitivity_results, sample_model_info):
    """Test report generation for an unstable rank change case."""
    sample_sensitivity_results["rank_stability"]["is_stable"] = False
    sample_sensitivity_results["rank_stability"]["max_rank_change"] = 2
    
    content = generate_report_content(sample_sensitivity_results, sample_model_info)
    
    assert "UNSTABLE" in content
    assert "Change > 1 position" in content

def test_generate_report_content_no_results(sample_model_info):
    """Test report generation when no sensitivity results are available."""
    content = generate_report_content(None, sample_model_info)
    
    assert "No sensitivity analysis results available" in content
    assert "Please ensure T031 and T032" in content

def test_load_model_info_missing_file():
    """Test loading model info when the file does not exist."""
    # Temporarily change the data directory to a non-existent one
    original_data_dir = get_data_dir()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the get_data_dir function to return a temp directory
        import config
        original_func = config.get_data_dir
        config.get_data_dir = lambda: Path(tmpdir)
        
        try:
            model_info = load_model_info()
            
            # Should return placeholder info
            assert model_info["model_type"] == "RandomForest"
            assert model_info["best_params"] == {}
        finally:
            config.get_data_dir = original_func

def test_report_contains_deviation_warning(sample_sensitivity_results, sample_model_info):
    """Test that the report contains the required deviation warning."""
    content = generate_report_content(sample_sensitivity_results, sample_model_info)
    
    assert "FR-006 and SC-003" in content
    assert "External Validation" in content
    assert "experimental onset potential datasets" in content
    assert "Internal DFT validation" in content
    assert "fallback" in content

def test_report_format_valid_markdown(sample_sensitivity_results, sample_model_info):
    """Test that the generated report is valid markdown structure."""
    content = generate_report_content(sample_sensitivity_results, sample_model_info)
    
    # Check for basic markdown structure
    lines = content.split('\n')
    headers = [line for line in lines if line.startswith('#')]
    
    # Should have at least one H1 header
    assert len(headers) >= 1
    
    # Check for table structure
    table_headers = [line for line in lines if '|' in line and line.strip().startswith('|')]
    assert len(table_headers) > 0  # Should have at least the performance metrics table