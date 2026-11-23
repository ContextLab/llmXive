"""
Integration test for T025: Write cooperative effects analysis.
Verifies that the script correctly aggregates results from T021c, T022-Exec, T023-Exec, and T021b.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock paths to avoid dependency on actual project structure during test
MOCK_PROCESSED_PATH = Path(tempfile.mkdtemp())

@pytest.fixture(autouse=True)
def setup_mock_paths(monkeypatch):
    """Setup mock paths for testing."""
    monkeypatch.setattr("code.config.PROCESSED_PATH", MOCK_PROCESSED_PATH)
    yield
    # Cleanup
    if MOCK_PROCESSED_PATH.exists():
        import shutil
        shutil.rmtree(MOCK_PROCESSED_PATH, ignore_errors=True)

def create_mock_json_file(path: Path, data: dict):
    """Helper to create mock JSON files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def test_t025_writes_correct_structure():
    """Test that T025 writes the correct JSON structure when all inputs are present."""
    # Create mock input files
    validation_data = {
        "status": "Cooperative Effects Detected",
        "cv_stability": {"passed": True},
        "interaction_significance": {"passed": True}
    }
    mse_data = {
        "overall_reduction_percent": 15.5,
        "threshold_met": True,
        "systems": [
            {"system": "Fe-Cr-Mo", "reduction_percent": 12.3},
            {"system": "Fe-Cr-V", "reduction_percent": 18.7}
        ]
    }
    significance_data = {
        "p_values": {
            "Fe-Cr-Mo_Cr_Mo": 0.03,
            "Fe-Cr-Mo_Cr_V": 0.12,
            "Fe-Cr-V_Cr_V": 0.01
        },
        "systems": ["Fe-Cr-Mo", "Fe-Cr-V"]
    }
    regression_data = {
        "coefficients": {
            "Fe-Cr-Mo_Cr_Mo": 0.05,
            "Fe-Cr-Mo_Cr_V": 0.02,
            "Fe-Cr-V_Cr_V": 0.08
        }
    }

    create_mock_json_file(MOCK_PROCESSED_PATH / "statistical_validation_report.json", validation_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "mse_comparison.json", mse_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "significance_results.json", significance_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "regression_results.json", regression_data)

    # Import and run the main function
    from code.us2.write_cooperative_effects_analysis import main, write_cooperative_analysis

    success = write_cooperative_analysis()
    assert success is True, "write_cooperative_analysis should return True"

    # Verify output file exists and contains correct structure
    output_path = MOCK_PROCESSED_PATH / "cooperative_effects_analysis.json"
    assert output_path.exists(), "Output file should be created"

    with open(output_path, 'r', encoding='utf-8') as f:
        result = json.load(f)

    # Validate structure
    assert "summary" in result
    assert "mse_reduction_stats" in result
    assert "interaction_coefficients" in result
    assert "p_values" in result
    assert "significant_interactions" in result
    assert "system_details" in result

    # Validate specific values
    assert result["summary"]["cooperative_effects_detected"] is True
    assert result["mse_reduction_stats"]["overall_reduction_percent"] == 15.5
    assert result["mse_reduction_stats"]["threshold_met"] is True
    assert "Fe-Cr-Mo_Cr_Mo" in result["significant_interactions"]
    assert "Fe-Cr-V_Cr_V" in result["significant_interactions"]
    assert "Fe-Cr-Mo_Cr_V" not in result["significant_interactions"]  # p=0.12 > 0.05

def test_t025_fails_on_missing_inputs():
    """Test that T025 fails gracefully when required inputs are missing."""
    # Create only some input files
    create_mock_json_file(MOCK_PROCESSED_PATH / "statistical_validation_report.json", {"status": "No Effects"})
    # Intentionally missing mse_comparison.json, significance_results.json, regression_results.json

    from code.us2.write_cooperative_effects_analysis import write_cooperative_analysis

    success = write_cooperative_analysis()
    assert success is False, "write_cooperative_analysis should return False when inputs are missing"

    # Verify no output file was created
    output_path = MOCK_PROCESSED_PATH / "cooperative_effects_analysis.json"
    assert not output_path.exists(), "Output file should not be created when inputs are missing"

def test_t025_handles_empty_systems():
    """Test that T025 handles cases with no systems analyzed."""
    validation_data = {"status": "No Effects", "cv_stability": {"passed": False}}
    mse_data = {"overall_reduction_percent": 0.0, "systems": []}
    significance_data = {"p_values": {}, "systems": []}
    regression_data = {"coefficients": {}}

    create_mock_json_file(MOCK_PROCESSED_PATH / "statistical_validation_report.json", validation_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "mse_comparison.json", mse_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "significance_results.json", significance_data)
    create_mock_json_file(MOCK_PROCESSED_PATH / "regression_results.json", regression_data)

    from code.us2.write_cooperative_effects_analysis import write_cooperative_analysis

    success = write_cooperative_analysis()
    assert success is True

    output_path = MOCK_PROCESSED_PATH / "cooperative_effects_analysis.json"
    with open(output_path, 'r', encoding='utf-8') as f:
        result = json.load(f)

    assert result["summary"]["cooperative_effects_detected"] is False
    assert result["mse_reduction_stats"]["overall_reduction_percent"] == 0.0
    assert result["system_details"] == []
    assert result["significant_interactions"] == []