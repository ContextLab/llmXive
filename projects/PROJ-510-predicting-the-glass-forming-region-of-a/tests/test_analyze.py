"""
Unit and integration tests for analysis and sensitivity.
"""
import pytest
import pandas as pd
import numpy as np
from code.analyze import analyze_feature_importance, run_sensitivity_analysis


def test_analyze_feature_importance_structure():
    """Test that feature importance analysis returns expected structure."""
    # Create mock data
    data = {
        "mixing_enthalpy": np.random.rand(100),
        "atomic_size_mismatch": np.random.rand(100),
        "electronegativity_variance": np.random.rand(100),
        "critical_cooling_rate": np.random.rand(100) * 100
    }
    df = pd.DataFrame(data)

    # Mock model (RandomForestRegressor)
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(df[["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance"]], df["critical_cooling_rate"])

    importance_results = analyze_feature_importance(model, df)
    assert "feature_importance" in importance_results
    assert "p_values" in importance_results
    assert len(importance_results["feature_importance"]) == 3


def test_run_sensitivity_analysis_thresholds():
    """Test sensitivity analysis across specified thresholds."""
    # Create mock data
    data = {
        "mixing_enthalpy": np.random.rand(100),
        "atomic_size_mismatch": np.random.rand(100),
        "electronegativity_variance": np.random.rand(100),
        "critical_cooling_rate": np.random.rand(100) * 100
    }
    df = pd.DataFrame(data)

    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(df[["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance"]], df["critical_cooling_rate"])

    thresholds = [50, 100, 150]
    results = run_sensitivity_analysis(model, df, thresholds)

    assert len(results) == len(thresholds)
    for res in results:
        assert "threshold" in res
        assert "metric_type" in res
        assert "value" in res