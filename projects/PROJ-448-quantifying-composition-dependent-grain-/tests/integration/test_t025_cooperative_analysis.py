import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Adjust import paths for testing context
sys_path_backup = list(__import__('sys').path)
try:
    project_root = Path(__file__).parent.parent.parent
    __import__('sys').path.insert(0, str(project_root))
    
    from code.us2.write_cooperative_analysis import (
        load_regression_results,
        load_statistical_validation_report,
        load_mse_reduction_results,
        compile_cooperative_analysis,
        main
    )
    from code.config import PROCESSED_PATH
finally:
    __import__('sys').path[:] = sys_path_backup


@pytest.fixture
def mock_regression_results():
    return {
        "systems": [
            {
                "system_name": "Fe-Cr-Mo",
                "coefficients": {
                    "Cr": 0.5,
                    "Mo": 0.3,
                    "Cr_Mo": 0.15,
                    "Cr_V": 0.02,
                    "Mo_V": 0.01
                },
                "p_values": {
                    "Cr": 0.001,
                    "Mo": 0.002,
                    "Cr_Mo": 0.03,
                    "Cr_V": 0.08,
                    "Mo_V": 0.12
                }
            },
            {
                "system_name": "Fe-Cr-V",
                "coefficients": {
                    "Cr": 0.4,
                    "V": 0.2,
                    "Cr_V": 0.005,
                    "Cr_Mo": 0.01
                },
                "p_values": {
                    "Cr": 0.001,
                    "V": 0.005,
                    "Cr_V": 0.45,
                    "Cr_Mo": 0.55
                }
            }
        ]
    }

@pytest.fixture
def mock_validation_report():
    return {
        "status": "Cooperative Effects Detected",
        "interaction_significance": True,
        "cv_stability": True
    }

@pytest.fixture
def mock_mse_results():
    return {
        "systems": [
            {
                "system_name": "Fe-Cr-Mo",
                "mse_reduction_percent": 15.5,
                "threshold_met": True
            },
            {
                "system_name": "Fe-Cr-V",
                "mse_reduction_percent": 5.2,
                "threshold_met": False
            }
        ]
    }

def test_compile_cooperative_analysis(mock_regression_results, mock_validation_report, mock_mse_results):
    """Test the core compilation logic of T025."""
    result = compile_cooperative_analysis(
        mock_regression_results, 
        mock_validation_report, 
        mock_mse_results
    )
    
    assert result["status"] == "complete"
    assert result["summary"]["cooperative_effects_detected"] == "Cooperative Effects Detected"
    assert result["summary"]["total_systems_analyzed"] == 2
    
    # Fe-Cr-Mo should have 1 significant term (Cr_Mo: p=0.03 < 0.05, coef=0.15 > 0.01)
    # Fe-Cr-V should have 0 significant terms
    assert result["summary"]["significant_interaction_terms"] == 1
    
    # Only Fe-Cr-Mo should be in the cooperative effects list
    assert len(result["summary"]["systems_with_cooperative_effects"]) == 1
    assert "Fe-Cr-Mo" in result["summary"]["systems_with_cooperative_effects"]
    
    # Check Fe-Cr-Mo details
    fe_cr_mo = next(s for s in result["systems"] if s["system_name"] == "Fe-Cr-Mo")
    assert fe_cr_mo["cooperative_effects_detected"] is True
    assert fe_cr_mo["mse_reduction"] == 15.5
    assert fe_cr_mo["mse_reduction_threshold_met"] is True
    
    # Check Cr_Mo term significance
    cr_mo_term = next(t for t in fe_cr_mo["interaction_terms"] if t["term"] == "Cr_Mo")
    assert cr_mo_term["significance"] == "significant"
    assert cr_mo_term["coefficient_eV"] == 0.15
    assert cr_mo_term["p_value"] == 0.03
    
    # Check Fe-Cr-V details
    fe_cr_v = next(s for s in result["systems"] if s["system_name"] == "Fe-Cr-V")
    assert fe_cr_v["cooperative_effects_detected"] is False
    assert fe_cr_v["mse_reduction"] == 5.2
    assert fe_cr_v["mse_reduction_threshold_met"] is False

def test_compile_cooperative_analysis_no_significant_terms(mock_regression_results, mock_validation_report, mock_mse_results):
    """Test behavior when no significant interaction terms exist."""
    # Modify mock to have no significant terms
    mock_regression_results["systems"][0]["p_values"]["Cr_Mo"] = 0.08
    mock_regression_results["systems"][0]["coefficients"]["Cr_Mo"] = 0.005
    
    result = compile_cooperative_analysis(
        mock_regression_results, 
        mock_validation_report, 
        mock_mse_results
    )
    
    assert result["summary"]["significant_interaction_terms"] == 0
    assert len(result["summary"]["systems_with_cooperative_effects"]) == 0

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary directory structure mimicking PROCESSED_PATH."""
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    
    # Create mock input files
    regression_data = {
        "systems": [
            {
                "system_name": "Fe-Cr-Mo",
                "coefficients": {"Cr": 0.5, "Mo": 0.3, "Cr_Mo": 0.15},
                "p_values": {"Cr": 0.001, "Mo": 0.002, "Cr_Mo": 0.03}
            }
        ]
    }
    with open(processed / "regression_results.json", 'w') as f:
        json.dump(regression_data, f)
    
    validation_data = {"status": "Cooperative Effects Detected"}
    with open(processed / "statistical_validation_report.json", 'w') as f:
        json.dump(validation_data, f)
    
    mse_data = {
        "systems": [
            {"system_name": "Fe-Cr-Mo", "mse_reduction_percent": 12.0, "threshold_met": True}
        ]
    }
    with open(processed / "mse_reduction_results.json", 'w') as f:
        json.dump(mse_data, f)
        
    return processed

@patch('code.us2.write_cooperative_analysis.PROCESSED_PATH')
def test_main_success(mock_processed_path, temp_processed_dir, caplog):
    """Test the main function execution with valid inputs."""
    mock_processed_path.__truediv__ = lambda self, key: temp_processed_dir / key
    mock_processed_path.__fspath__ = lambda self: str(temp_processed_dir)
    
    # Run main
    main()
    
    # Verify output file was created
    output_path = temp_processed_dir / "cooperative_effects_analysis.json"
    assert output_path.exists()
    
    # Verify content
    with open(output_path, 'r') as f:
        result = json.load(f)
    
    assert result["status"] == "complete"
    assert len(result["systems"]) == 1

@patch('code.us2.write_cooperative_analysis.PROCESSED_PATH')
def test_main_missing_file(mock_processed_path, tmp_path):
    """Test that main raises error when input file is missing."""
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    
    mock_processed_path.__truediv__ = lambda self, key: processed / key
    mock_processed_path.__fspath__ = lambda self: str(processed)
    
    # Only create one input file
    with open(processed / "regression_results.json", 'w') as f:
        json.dump({"systems": []}, f)
    
    # Should raise FileNotFoundError for missing validation report
    with pytest.raises(FileNotFoundError):
        main()