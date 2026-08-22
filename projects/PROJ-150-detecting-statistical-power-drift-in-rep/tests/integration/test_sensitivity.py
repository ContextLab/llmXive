import os
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.robustness import run_sensitivity_analysis, load_lmm_summary

@pytest.fixture
def mock_lmm_summary(tmp_path):
    """Create a mock lmm_final_summary.json for testing."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    mock_data = {
        "slope_year": -0.002,
        "se_year": 0.0005,
        "ci_lower": -0.003,
        "ci_upper": -0.001,
        "p_value_lrt": 0.03,
        "chi2_statistic": 4.5,
        "df_diff": 1
    }
    with open(results_dir / "lmm_final_summary.json", 'w') as f:
        json.dump(mock_data, f)
    return results_dir

@pytest.fixture
def setup_env(mock_lmm_summary, monkeypatch):
    """Change working directory to temp path to isolate file writes."""
    monkeypatch.chdir(mock_lmm_summary.parent)
    return mock_lmm_summary

def test_sensitivity_analysis_sweep(setup_env):
    """
    Integration test for T021: Verify sensitivity analysis sweeps alpha
    and produces the correct output file with required schema.
    """
    # Run the function
    result = run_sensitivity_analysis()
    
    # Check output file existence
    output_path = Path("results/sensitivity_report.json")
    assert output_path.exists(), "Sensitivity report file was not created."
    
    # Load and validate content
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    # Validate schema
    assert "alpha_values" in report, "Missing 'alpha_values' key."
    assert "conclusion" in report, "Missing 'conclusion' key."
    assert isinstance(report["alpha_values"], list), "'alpha_values' must be a list."
    assert isinstance(report["conclusion"], str), "'conclusion' must be a string."
    
    # Check specific alpha values (0.05 and 0.1 must be present)
    alphas = [item["alpha"] for item in report["alpha_values"]]
    assert 0.05 in alphas, "Alpha 0.05 must be in the sweep."
    assert 0.1 in alphas, "Alpha 0.1 must be in the sweep."
    
    # Validate entries have required keys
    for entry in report["alpha_values"]:
        assert "alpha" in entry
        assert "p_value" in entry
        assert "drift_significant" in entry
        assert isinstance(entry["drift_significant"], bool)
        
        # Verify logic: p_value < alpha implies significant
        expected_sig = entry["p_value"] < entry["alpha"]
        assert entry["drift_significant"] == expected_sig, \
            f"Significance logic error for alpha={entry['alpha']}"

    # Verify conclusion mentions sensitivity
    assert len(report["conclusion"]) > 0, "Conclusion should not be empty."
    # With p=0.03, it should be significant at 0.05 but not 0.01 (if tested)
    # The mock has p=0.03. 
    # 0.01 -> False, 0.05 -> True. So it should mention sensitivity.
    assert "sensitive" in report["conclusion"].lower() or "threshold" in report["conclusion"].lower(), \
        "Conclusion should discuss sensitivity to alpha choice when results diverge."