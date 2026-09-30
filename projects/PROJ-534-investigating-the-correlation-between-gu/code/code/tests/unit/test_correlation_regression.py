import pytest
import pandas as pd
import numpy as np
from code.src.analysis.correlation import run_regression_analysis, run_multiple_regressions, apply_benjamini_hochberg

def test_regression_analysis_basic():
    """Test basic regression analysis functionality."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "shannon_diversity": np.random.normal(3.5, 0.5, n),
        "cognitive_flexibility_score": np.random.normal(50, 10, n),
        "age": np.random.randint(65, 90, n),
        "sex": np.random.choice(["M", "F"], n),
        "bmi": np.random.normal(25, 3, n),
        "dietary_fiber": np.random.normal(20, 5, n),
        "antibiotic_use": np.random.choice([True, False], n)
    })

    result = run_regression_analysis(
        data,
        diversity_col="shannon_diversity",
        target_col="cognitive_flexibility_score",
        covariates=["age", "sex", "bmi", "dietary_fiber", "antibiotic_use"]
    )

    assert "r_squared" in result
    assert "baseline_r_squared" in result
    assert "delta_r_squared" in result
    assert "coefficients" in result
    assert "p_values" in result
    assert "diversity_p_value" in result
    assert isinstance(result["r_squared"], float)
    assert 0.0 <= result["r_squared"] <= 1.0

def test_regression_analysis_missing_column():
    """Test that regression fails gracefully with missing columns."""
    data = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ValueError):
        run_regression_analysis(
            data,
            diversity_col="missing_div",
            target_col="missing_target",
            covariates=[]
        )

def test_benjamini_hochberg_correction():
    """Test BH correction logic."""
    p_values = [0.01, 0.04, 0.03, 0.005, 0.06]
    adjusted = apply_benjamini_hochberg(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0.0 <= p <= 1.0 for p in adjusted)
    # The smallest p-value should generally increase or stay same in adjusted
    # (though BH can sometimes be conservative, it shouldn't decrease the smallest significantly below 0)
    # Specifically, adjusted p-values should be monotonically non-decreasing when sorted by original p-values
    sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
    sorted_adjusted = [adjusted[i] for i in sorted_indices]
    for i in range(1, len(sorted_adjusted)):
        assert sorted_adjusted[i] >= sorted_adjusted[i-1] - 1e-9

def test_multiple_regressions():
    """Test running multiple regressions and BH correction."""
    np.random.seed(42)
    n = 50
    data = pd.DataFrame({
        "shannon_diversity": np.random.normal(3.5, 0.5, n),
        "simpson_diversity": np.random.normal(0.9, 0.05, n),
        "chao1": np.random.normal(100, 20, n),
        "cognitive_flexibility_score": np.random.normal(50, 10, n),
        "age": np.random.randint(65, 90, n),
        "sex": np.random.choice(["M", "F"], n),
        "bmi": np.random.normal(25, 3, n),
        "dietary_fiber": np.random.normal(20, 5, n),
        "antibiotic_use": np.random.choice([True, False], n)
    })

    results = run_multiple_regressions(
        data,
        diversity_metrics=["shannon_diversity", "simpson_diversity", "chao1"],
        target_col="cognitive_flexibility_score",
        covariates=["age", "sex", "bmi", "dietary_fiber", "antibiotic_use"]
    )

    assert len(results) == 3
    for res in results:
        assert "metric" in res
        assert "r_squared" in res
        assert "adjusted_p_value" in res
        assert isinstance(res["adjusted_p_value"], float)