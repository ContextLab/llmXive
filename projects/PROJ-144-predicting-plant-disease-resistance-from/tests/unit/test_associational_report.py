import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from modeling.generate_associational_report import generate_associational_report, main, load_json_file

@pytest.fixture
def mock_metrics_data():
    return {
        "balanced_accuracy": 0.82,
        "roc_auc": 0.89,
        "permutation_p_value": 0.001,
        "fdr_threshold": 0.05
    }

@pytest.fixture
def mock_correlations_data():
    return {
        "correlations": [
            {
                "metabolite": "Indole-3-acetic acid",
                "correlation": 0.75,
                "fdr_p_value": 0.003
            },
            {
                "metabolite": "Salicylic acid",
                "correlation": 0.68,
                "fdr_p_value": 0.012
            }
        ]
    }

@pytest.fixture
def mock_vif_data():
    return {
        "high_vif_metabolites": ["Indole-3-acetic acid", "Auxin-like compound"],
        "vif_values": {
            "Indole-3-acetic acid": 6.2,
            "Salicylic acid": 2.1
        }
    }

def test_generate_associational_report_framing(mock_metrics_data, mock_correlations_data, mock_vif_data):
    """Test that the generated report explicitly frames findings as associational."""
    report = generate_associational_report(mock_metrics_data, mock_correlations_data, mock_vif_data)
    
    # Check for critical disclaimer
    assert "CRITICAL NOTE" in report["disclaimer"]
    assert "ASSOCIATIONAL" in report["disclaimer"]
    assert "NO CAUSAL INFERENCES" in report["disclaimer"]
    
    # Check summary interpretation
    assert "associational signal" in report["summary"]["model_performance"]["interpretation"]
    assert "does not imply that these metabolites cause resistance" in report["summary"]["model_performance"]["interpretation"]
    
    # Check collinearity warning
    assert "association strength" in report["summary"]["collinearity_warning"]["interpretation"]
    assert "individual causal contribution" in report["summary"]["collinearity_warning"]["interpretation"]
    
    # Check limitations
    assert any("causal inference" in lim.lower() for lim in report["limitations"])
    assert any("confounders" in lim.lower() for lim in report["limitations"])

def test_report_structure(mock_metrics_data, mock_correlations_data, mock_vif_data):
    """Verify the report contains all required sections."""
    report = generate_associational_report(mock_metrics_data, mock_correlations_data, mock_vif_data)
    
    required_keys = ["report_type", "disclaimer", "summary", "associational_findings", "limitations", "recommendations"]
    for key in required_keys:
        assert key in report, f"Missing key: {key}"
    
    # Verify specific data population
    assert len(report["associational_findings"]["top_associated_metabolites"]) == 2
    assert report["associational_findings"]["top_associated_metabolites"][0]["metabolite"] == "Indole-3-acetic acid"

def test_load_json_file_success(tmp_path):
    """Test loading a valid JSON file."""
    file_path = tmp_path / "test.json"
    data = {"key": "value"}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    result = load_json_file(str(file_path))
    assert result == data

def test_load_json_file_not_found():
    """Test that load_json_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_json_file("/non/existent/path.json")

def test_load_json_file_invalid_json(tmp_path):
    """Test that load_json_file raises ValueError for invalid JSON."""
    file_path = tmp_path / "invalid.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json }")
    
    with pytest.raises(ValueError):
        load_json_file(str(file_path))

@patch('builtins.open', new_callable=mock_open)
@patch('pathlib.Path.exists', return_value=True)
@patch('pathlib.Path.mkdir')
def test_main_execution(mock_mkdir, mock_exists, mock_open_file, mock_metrics_data, mock_correlations_data, mock_vif_data, tmp_path):
    """Test the main function execution flow."""
    # Setup mock file system for inputs
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    metrics_file = results_dir / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(mock_metrics_data, f)
    
    shap_file = results_dir / "shap_analysis.json"
    with open(shap_file, 'w') as f:
        json.dump(mock_correlations_data, f)
    
    vif_file = results_dir / "collinearity.json"
    with open(vif_file, 'w') as f:
        json.dump(mock_vif_data, f)

    # Mock the constants to point to our temp directory
    with patch('modeling.generate_associational_report.RESULTS_DIR', str(results_dir)):
        with patch('sys.exit') as mock_exit:
            main()
            
            # Verify exit code 0
            mock_exit.assert_called_once_with(0)
            
            # Verify output file was created
            output_file = results_dir / "associational_report.json"
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                output_data = json.load(f)
                assert "CRITICAL NOTE" in output_data["disclaimer"]
