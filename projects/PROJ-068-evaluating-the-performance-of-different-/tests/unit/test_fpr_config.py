"""
Unit tests for FPR configuration logic (Task T015).
"""
import pytest
import math
from bloom_filters.base import calculate_optimal_parameters, get_config_for_sizes, FPR_TARGETS


def test_fpr_targets_constant():
    """Verify Constitution Principle VI FPR targets."""
    assert FPR_TARGETS == [0.01, 0.05, 0.10]
    assert len(FPR_TARGETS) == 3


def test_calculate_optimal_parameters_small():
    """Test parameter calculation for a small dataset."""
    n = 1000
    fpr = 0.01
    m, k = calculate_optimal_parameters(n, fpr)

    # Theoretical check:
    # m = - (n * ln(p)) / (ln(2)^2)
    # k = (m/n) * ln(2)
    expected_m = - (n * math.log(fpr)) / (math.log(2) ** 2)
    expected_k = (expected_m / n) * math.log(2)

    # Allow for rounding differences (ceil)
    assert m >= expected_m
    assert k >= expected_k
    assert m > 0
    assert k > 0


def test_calculate_optimal_parameters_large():
    """Test parameter calculation for a large dataset."""
    n = 1_000_000
    fpr = 0.01
    m, k = calculate_optimal_parameters(n, fpr)

    assert m > 0
    assert k > 0
    # Verify the relationship holds approximately
    theoretical_fpr = (1 - math.exp(-k * n / m)) ** k
    # The calculated m/k should result in an FPR close to target (usually slightly lower due to ceil)
    assert theoretical_fpr <= fpr * 1.1  # Allow small margin for rounding up


def test_calculate_optimal_parameters_invalid_fpr():
    """Test that invalid FPR raises error."""
    with pytest.raises(ValueError):
        calculate_optimal_parameters(1000, 0.0)
    with pytest.raises(ValueError):
        calculate_optimal_parameters(1000, 1.0)
    with pytest.raises(ValueError):
        calculate_optimal_parameters(1000, -0.1)


def test_calculate_optimal_parameters_invalid_n():
    """Test that invalid n raises error."""
    with pytest.raises(ValueError):
        calculate_optimal_parameters(0, 0.01)
    with pytest.raises(ValueError):
        calculate_optimal_parameters(-100, 0.01)


def test_get_config_for_sizes():
    """Test configuration generation for multiple sizes and FPRs."""
    sizes = [1000, 10000]
    targets = [0.01, 0.05]
    configs = get_config_for_sizes(sizes, targets)

    # Should generate 2 sizes * 2 targets = 4 configs
    assert len(configs) == 4

    # Verify structure
    for cfg in configs:
        assert "n" in cfg
        assert "fpr_target" in cfg
        assert "m" in cfg
        assert "k" in cfg
        assert cfg["m"] > 0
        assert cfg["k"] > 0


def test_get_config_for_sizes_default_targets():
    """Test that default targets are used if not provided."""
    configs = get_config_for_sizes([1000])
    assert len(configs) == 3  # 3 default FPR targets
    fprs = [c["fpr_target"] for c in configs]
    assert set(fprs) == set(FPR_TARGETS)
