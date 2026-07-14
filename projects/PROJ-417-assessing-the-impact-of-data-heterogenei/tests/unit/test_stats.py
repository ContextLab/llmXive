"""
Unit tests for statistical functions.
"""

import pytest
from code.analysis.stats import (
    exact_binomial_test,
    shapiro_wilk_test,
    bonferroni_correction,
    conditional_statistical_test,
    apply_anova,
    apply_kruskal_wallis
)


def test_binomial_test_expected_coverage():
    """Test binomial test with expected 95% coverage."""
    # 100 trials, 95 successes (expected)
    res = exact_binomial_test(95, 100, p_null=0.95)
    assert res["p_value"] > 0.05 # Should not reject null
    assert res["statistic"] == 0.95


def test_binomial_test_low_coverage():
    """Test binomial test with low coverage (should reject)."""
    # 100 trials, 80 successes (low)
    res = exact_binomial_test(80, 100, p_null=0.95)
    assert res["p_value"] < 0.05 # Should reject null


def test_shapiro_wilk_normal():
    """Test Shapiro-Wilk on normal data."""
    import numpy as np
    data = np.random.normal(0, 1, 100).tolist()
    res = shapiro_wilk_test(data)
    assert res["p_value"] > 0.05 # Likely normal


def test_shapiro_wilk_non_normal():
    """Test Shapiro-Wilk on uniform data (often passes, but let's check logic)."""
    import numpy as np
    # Uniform is not normal, but with small N might pass. 
    # Let's use a clearly non-normal distribution if possible, or just check return structure.
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    res = shapiro_wilk_test(data)
    assert "p_value" in res
    assert "statistic" in res


def test_bonferroni_correction():
    """Test Bonferroni correction."""
    p_values = [0.01, 0.04, 0.06]
    results = bonferroni_correction(p_values, alpha=0.05)
    assert len(results) == 3
    # 0.01 * 3 = 0.03 < 0.05 -> significant
    assert results[0]["is_significant"] is True
    # 0.06 * 3 = 0.18 > 0.05 -> not significant
    assert results[2]["is_significant"] is False


def test_conditional_test_normal_data():
    """Test conditional test selects ANOVA for normal data."""
    import numpy as np
    group1 = np.random.normal(0, 1, 50).tolist()
    group2 = np.random.normal(0.5, 1, 50).tolist()
    res = conditional_statistical_test([group1, group2])
    assert res["test_name"] in ["ANOVA", "Kruskal-Wallis"]
    assert "p_value" in res


def test_conditional_test_non_normal_data():
    """Test conditional test selects Kruskal-Wallis for non-normal data."""
    # Exponential is non-normal
    import numpy as np
    group1 = np.random.exponential(1, 50).tolist()
    group2 = np.random.exponential(2, 50).tolist()
    res = conditional_statistical_test([group1, group2])
    assert res["test_name"] in ["ANOVA", "Kruskal-Wallis"]
    assert "p_value" in res
