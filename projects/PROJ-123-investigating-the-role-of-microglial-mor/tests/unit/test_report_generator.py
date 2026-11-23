import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config to avoid path issues in tests
@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):
    # Create a temporary directory for the test run
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock get_path to return paths inside tmpdir
        def mock_get_path(key):
            paths = {
                "reports": os.path.join(tmpdir, "reports"),
                "data/intermediates/vif_check.json": os.path.join(tmpdir, "data", "intermediates", "vif_check.json"),
                "data/processed/morphological_metrics.csv": os.path.join(tmpdir, "data", "processed", "morphological_metrics.csv")
            }
            return paths.get(key)
        
        monkeypatch.setattr("code.report_generator.get_path", mock_get_path)
        
        # Ensure dirs exist
        os.makedirs(os.path.join(tmpdir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(tmpdir, "data", "intermediates"), exist_ok=True)
        
        yield tmpdir

def test_generate_json_report_structure():
    """Test that the generated JSON report has the correct structure."""
    from code.report_generator import generate_json_report

    mock_regression = {
        "coefficients": {"intercept": 0.5, "branch_points": 0.1},
        "p_values": {"intercept": 0.01, "branch_points": 0.04},
        "interaction_terms": ["Pathology*Region"],
        "r2": 0.45
    }
    mock_vif = {"vif_scores": {"branch_points": 2.1}, "trigger_pca": False}

    report = generate_json_report(mock_regression, mock_vif)

    assert "metadata" in report
    assert "generated_at" in report["metadata"]
    assert "vif_analysis" in report
    assert "regression_results" in report
    assert report["regression_results"]["coefficients"] == mock_regression["coefficients"]
    assert report["vif_analysis"]["trigger_pca"] is False

def test_generate_markdown_report_content():
    """Test that the Markdown report contains expected sections."""
    from code.report_generator import generate_markdown_report

    mock_regression = {
        "coefficients": {"intercept": 0.5, "branch_points": 0.1},
        "p_values": {"intercept": 0.01, "branch_points": 0.04},
        "interaction_terms": ["Pathology*Region"]
    }
    mock_vif = {"vif_scores": {"branch_points": 2.1}, "trigger_pca": False}

    # Test with causality warning
    md_content = generate_markdown_report(mock_regression, mock_vif, causality_warning=True)

    assert "# Regression Analysis Report" in md_content
    assert "## Methodology" in md_content
    assert "## VIF Analysis" in md_content
    assert "## Regression Results" in md_content
    assert "## ⚠️ Causality Warning" in md_content
    assert "Associational findings only" in md_content

    # Test without causality warning
    md_content_no_warning = generate_markdown_report(mock_regression, mock_vif, causality_warning=False)
    assert "## ⚠️ Causality Warning" not in md_content_no_warning

def test_run_report_pipeline_integration(mock_config_paths):
    """Integration test for the full report pipeline."""
    from code.report_generator import run_report_pipeline
    from code.config import get_path
    
    # Mock the regression loading function to return deterministic data
    mock_regression_data = {
        "coefficients": {"intercept": 1.2, "soma_area": 0.05, "total_length": -0.02},
        "p_values": {"intercept": 0.001, "soma_area": 0.03, "total_length": 0.08},
        "interaction_terms": ["PathologyStatus:BrainRegion"],
        "r2": 0.32,
        "model_summary": "Dummy summary"
    }
    
    mock_vif_data = {
        "vif_scores": {"soma_area": 1.5, "total_length": 1.6},
        "trigger_pca": False
    }

    with patch('code.report_generator.load_regression_results', return_value=mock_regression_data), \
         patch('code.report_generator.load_vif_check', return_value=mock_vif_data):
        
        success = run_report_pipeline()
        assert success is True

        # Verify files exist
        json_path = get_path("reports") + "/regression_results.json"
        md_path = get_path("reports") + "/regression_results.md"
        
        assert os.path.exists(json_path), f"JSON report not found at {json_path}"
        assert os.path.exists(md_path), f"Markdown report not found at {md_path}"

        # Verify JSON content
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert data["regression_results"]["coefficients"]["soma_area"] == 0.05
            assert data["vif_analysis"]["trigger_pca"] is False

        # Verify Markdown content
        with open(md_path, 'r') as f:
            content = f.read()
            assert "soma_area" in content
            assert "PathologyStatus:BrainRegion" in content
            assert "Associational findings only" in content  # Default warning