"""
Unit tests for the chi‑squared method‑recording requirement (T018).
"""

import pytest

from stats import run_chi_squared_test, calculate_chi_squared_statistic, \
    run_full_statistical_analysis

def test_chi_squared_method_monte_carlo():
    # Uniform synthetic data for prime=5, N=100 (expected counts = 20 >= 5)
    prime = 5
    N = 100
    observed = {r: N // prime for r in range(prime)}
    p_val, method = run_chi_squared_test(observed, prime, M=500, seed=123)
    assert method == "chi_squared_monte_carlo"
    assert 0.0 <= p_val <= 1.0

def test_chi_squared_method_exact():
    # Small N leading to expected count < 5 forces exact fallback.
    prime = 5
    N = 10  # expected count = 2 < 5
    observed = {r: (N // prime) + (1 if r == 0 else 0) for r in range(prime)}
    p_val, method = run_chi_squared_test(observed, prime, M=500, seed=123)
    assert method == "chi_squared_exact"
    assert 0.0 <= p_val <= 1.0

def test_full_statistical_result_includes_method():
    prime = 5
    N = 100
    observed = {r: N // prime for r in range(prime)}
    config = {"seed": 42, "chi2_mc_samples": 200, "bootstrap_samples": 100}
    result = run_full_statistical_analysis(observed, prime, N, config)
    assert hasattr(result, "method")
    assert result.method in {"chi_squared_monte_carlo", "chi_squared_exact"}
    # Ensure the result can be serialized without error.
    json_str = result.to_json()
    assert "\"method\"" in json_str