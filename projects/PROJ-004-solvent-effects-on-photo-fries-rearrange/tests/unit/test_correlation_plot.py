import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Mock imports for testing without full data pipeline
# We test the logic of the functions directly if possible, or mock dependencies

def test_compute_polarity_index():
    """Test that polarity index is normalized correctly."""
    from analysis.correlation import compute_polarity_index
    
    data = {
        'dielectric_constant': [2.0, 5.0, 10.0]
    }
    df = pd.DataFrame(data)
    result = compute_polarity_index(df)
    
    assert 'polarity_index' in result.columns
    assert result['polarity_index'].min() >= 0.0
    assert result['polarity_index'].max() <= 1.0
    # Check specific values
    # 2.0 -> 0.0, 10.0 -> 1.0, 5.0 -> (5-2)/(10-2) = 3/8 = 0.375
    assert np.isclose(result.loc[0, 'polarity_index'], 0.0)
    assert np.isclose(result.loc[2, 'polarity_index'], 1.0)
    assert np.isclose(result.loc[1, 'polarity_index'], 0.375)

def test_compute_vif():
    """Test VIF calculation logic."""
    from analysis.correlation import compute_vif
    
    # Perfect correlation -> VIF infinite (or very large)
    data = {
        'polarity_index': [1.0, 2.0, 3.0],
        'solvation_energy_kcal_mol': [2.0, 4.0, 6.0]
    }
    df = pd.DataFrame(data)
    vif = compute_vif(df)
    
    # With perfect correlation, 1 - R^2 is 0, so VIF is inf
    assert np.isinf(vif['polarity_index']) or vif['polarity_index'] > 1000

    # No correlation -> VIF = 1
    data_no_corr = {
        'polarity_index': [1.0, 2.0, 3.0],
        'solvation_energy_kcal_mol': [5.0, 1.0, 3.0] # Not perfectly correlated
    }
    df2 = pd.DataFrame(data_no_corr)
    vif2 = compute_vif(df2)
    
    assert vif2['polarity_index'] >= 1.0
    assert vif2['solvation_energy'] >= 1.0

def test_apply_multiple_comparison_correction():
    """Test Bonferroni correction."""
    from analysis.correlation import apply_multiple_comparison_correction
    
    p_vals = [0.01, 0.05, 0.1]
    corrected = apply_multiple_comparison_correction(p_vals, method="bonferroni")
    
    # 0.01 * 3 = 0.03
    assert corrected[0] == 0.03
    # 0.05 * 3 = 0.15
    assert corrected[1] == 0.15
    # 0.1 * 3 = 0.3
    assert corrected[2] == 0.3

def test_write_correlation_results_structure():
    """Test that the JSON output structure is correct."""
    from analysis.correlation import write_correlation_results
    import tempfile
    
    results = {
        "bayesian_r2": 0.85,
        "posterior_beta1_mean": -0.5,
        "posterior_beta1_ci_95": [-1.0, 0.0],
        "frequentist_p_value": 0.04,
        "n_samples": 3,
        "finding_framing": "Associational"
    }
    vif = {"polarity_index": 1.2, "solvation_energy": 1.2}
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = Path(f.name)
    
    write_correlation_results(results, vif, path)
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    assert "bayesian_analysis" in data
    assert "vif_scores" in data
    assert "methodology_notes" in data
    assert len(data["methodology_notes"]) > 0
    
    # Check specific framing
    assert "Associational" in str(data["methodology_notes"]) or data["bayesian_analysis"]["finding_framing"] == "Associational and Exploratory"
    
    path.unlink()