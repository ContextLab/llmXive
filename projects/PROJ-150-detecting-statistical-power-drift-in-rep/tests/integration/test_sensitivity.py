import json
import os
import tempfile
import pytest
from pathlib import Path
import pandas as pd

# Import the function to test
from robustness import run_sensitivity_analysis, ALPHA_LEVELS

@pytest.fixture
def mock_lmm_data(tmp_path):
    """Create mock LMM summary CSV and LRT JSON for testing."""
    # Ensure directories exist
    derived_dir = tmp_path / "data" / "derived"
    derived_dir.mkdir(parents=True)
    
    # Create mock lmm_summary.csv
    csv_path = derived_dir / "lmm_summary.csv"
    mock_df = pd.DataFrame({
        'slope_year': [-0.005],
        'se_year': [0.002],
        'ci_lower': [-0.009],
        'ci_upper': [-0.001]
    })
    mock_df.to_csv(csv_path, index=False)
    
    # Create mock lrt_results.json
    json_path = derived_dir / "lrt_results.json"
    mock_lrt = {
        "chi2_statistic": 12.5,
        "p_value": 0.0004,
        "df_diff": 1
    }
    with open(json_path, 'w') as f:
        json.dump(mock_lrt, f)
    
    return tmp_path

def test_sensitivity_analysis_sweep(mock_lmm_data, tmp_path):
    """
    Integration test for T021: Verify sensitivity analysis sweeps alpha levels
    and produces valid significance rates.
    
    Verifies:
    - The function runs without error.
    - The output file is created.
    - The output contains the expected alpha levels.
    - The significance logic is correct (p < alpha).
    """
    # Change working directory to the temp path so relative paths in robustness.py work
    original_cwd = os.getcwd()
    os.chdir(mock_lmm_data)
    
    try:
        # Run the sensitivity analysis
        results = run_sensitivity_analysis()
        
        # Verify the returned results structure
        assert "alpha_sweep" in results
        assert len(results["alpha_sweep"]) == len(ALPHA_LEVELS)
        
        # Verify specific alpha levels are present
        alphas_in_results = [entry["alpha"] for entry in results["alpha_sweep"]]
        for alpha in ALPHA_LEVELS:
            assert alpha in alphas_in_results, f"Missing alpha level: {alpha}"
        
        # Verify the logic: for slope=-0.005, se=0.002 -> z=2.5 -> p=0.0124
        # So:
        # alpha=0.01 -> p(0.0124) > 0.01 -> False
        # alpha=0.05 -> p(0.0124) < 0.05 -> True
        # alpha=0.10 -> p(0.0124) < 0.10 -> True
        
        expected_significance = {
            0.01: False,
            0.05: True,
            0.10: True
        }
        
        for entry in results["alpha_sweep"]:
            alpha = entry["alpha"]
            is_sig = entry["is_significant"]
            assert is_sig == expected_significance[alpha], \
                f"Significance logic failed for alpha={alpha}: expected {expected_significance[alpha]}, got {is_sig}"
        
        # Verify output file was written
        output_path = Path("results/sensitivity_analysis.json")
        assert output_path.exists(), "Output file 'results/sensitivity_analysis.json' not created"
        
        # Verify JSON content matches results
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["alpha_sweep"] == results["alpha_sweep"]
        
    finally:
        os.chdir(original_cwd)