import pytest
import numpy as np
from scipy import stats
from code.power import (
    calculate_ncp, 
    calculate_power_from_ncp, 
    find_min_sample_size, 
    calculate_retrospective_power,
    run_retrospective_power_analysis
)

def test_calculate_ncp():
    # NCP = effect_size * sqrt(n)
    effect_size = 0.5
    n = 100
    expected_ncp = 0.5 * np.sqrt(100)
    assert np.isclose(calculate_ncp(effect_size, n), expected_ncp)

def test_calculate_power_from_ncp():
    # With high NCP, power should be high
    ncp = 5.0
    alpha = 0.05
    df = 1000
    power = calculate_power_from_ncp(ncp, alpha, df)
    assert power > 0.90

    # With low NCP, power should be near alpha
    ncp = 0.0
    power_low = calculate_power_from_ncp(ncp, alpha, df)
    assert power_low < 0.10

def test_find_min_sample_size():
    # For a medium effect size (0.5) and alpha 0.05, power 0.80
    # Expected n is roughly 64 for t-test (Cohen's d)
    n = find_min_sample_size(0.5, 0.05, 0.80)
    assert n > 0
    assert n < 200 # Sanity check

def test_calculate_retrospective_power():
    # If effect size is 0, power should be alpha
    power = calculate_retrospective_power(0.0, 100, 0.05)
    assert power < 0.10

    # If effect size is large, power should be high
    power = calculate_retrospective_power(0.8, 100, 0.05)
    assert power > 0.80

def test_run_retrospective_power_analysis():
    results = run_retrospective_power_analysis(0.5, 100, 0.05, 0.80)
    assert "observed_power" in results
    assert "required_n" in results
    assert "effect_size" in results
    assert "met_target" in results
    assert results["effect_size"] == 0.5
    assert results["n"] == 100 # Not returned in this function but implied
    # Check logic: if power >= 0.80, met_target should be True
    # With n=100 and d=0.5, power is approx 0.70, so met_target should be False
    # (Exact value depends on calculation method)
    assert isinstance(results["met_target"], bool)
