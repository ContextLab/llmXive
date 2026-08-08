"""
Unit tests for Task T029: Stability Verification and Significance Logging.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.stability_analysis import (
    load_stability_report,
    load_corrected_p_values,
    verify_statistical_significance,
    save_verification_report,
    StabilityResult
)
from config import get_paths

@pytest.fixture
def mock_paths(tmp_path):
    """Create a temporary directory structure mimicking the project."""
    reports_dir = tmp_path / "docs" / "reports"
    reports_dir.mkdir(parents=True)
    
    # Mock get_paths to return our temp directory
    with patch('models.stability_analysis.get_paths') as mock_get:
        mock_get.return_value = {
            "reports_dir": reports_dir,
            "data_dir": tmp_path / "data",
            "models_dir": tmp_path / "models"
        }
        yield reports_dir

def test_load_stability_report_missing(mock_paths):
    """Test that load_stability_report raises FileNotFoundError if file is missing."""
    with pytest.raises(FileNotFoundError, match="stability_report.json not found"):
        load_stability_report()

def test_load_stability_report_success(mock_paths):
    """Test successful loading of stability report."""
    report_path = mock_paths / "stability_report.json"
    data = [
        {"feature": "rdf_peak", "family": "oxide", "mean_rank": 1.5, "ci_lower": 1.0, "ci_upper": 2.0},
        {"feature": "bond_angle", "family": "sulfide", "mean_rank": 2.1, "ci_lower": 1.5, "ci_upper": 2.5}
    ]
    with open(report_path, 'w') as f:
        json.dump(data, f)
    
    result = load_stability_report()
    assert len(result) == 2
    assert result[0]['feature'] == 'rdf_peak'

def test_load_corrected_p_values_missing(mock_paths):
    """Test that load_corrected_p_values raises FileNotFoundError if file is missing."""
    with pytest.raises(FileNotFoundError, match="corrected_p_values.json not found"):
        load_corrected_p_values()

def test_verify_statistical_significance(mock_paths):
    """Test the core verification logic."""
    # Setup stability data
    stability_data = [
        {"feature": "rdf_peak", "family": "oxide", "mean_rank": 1.2, "ci_lower": 0.8, "ci_upper": 1.6},
        {"feature": "coordination", "family": "sulfide", "mean_rank": 3.5, "ci_lower": 3.0, "ci_upper": 4.0}
    ]
    
    # Setup p-values (direct key match)
    p_values_data = {
        "rdf_peak_oxide": 0.03,  # Significant
        "coordination_sulfide": 0.15 # Not significant
    }
    
    results = verify_statistical_significance(stability_data, p_values_data)
    
    assert len(results) == 2
    
    # Check first result (significant)
    res1 = next(r for r in results if r.feature == "rdf_peak")
    assert res1.is_significant is True
    assert res1.mean_rank == 1.2
    
    # Check second result (not significant)
    res2 = next(r for r in results if r.feature == "coordination")
    assert res2.is_significant is False

def test_save_verification_report(mock_paths):
    """Test saving the verification report."""
    results = [
        StabilityResult("feature_a", "oxide", 1.0, 0.5, 1.5, True),
        StabilityResult("feature_b", "sulfide", 2.0, 1.5, 2.5, False)
    ]
    
    output_path = save_verification_report(results)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['feature'] == 'feature_a'
    assert data[0]['is_significant'] is True