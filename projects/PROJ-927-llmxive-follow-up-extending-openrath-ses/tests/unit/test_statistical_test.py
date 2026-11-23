"""Unit tests for statistical tests (T034a, T034b, T034c, T038)."""
import pytest

def test_cochran_q_test():
    """Test Cochran's Q test implementation (T034a)."""
    from analyzers.statistical_test import cochrans_q_test
    
    # Mock data: 3 treatments, 10 subjects
    # 1 = success, 0 = failure
    data = [
        [1, 1, 0],
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
        [1, 0, 1]
    ]
    
    try:
        result = cochrans_q_test(data)
        assert "statistic" in result
        assert "p_value" in result
    except ImportError:
        pytest.skip("Scipy not available for statistical tests")

def test_mcnemar_post_hoc():
    """Test McNemar's post-hoc with Holm-Bonferroni (T034b)."""
    from analyzers.statistical_test import mcnemar_post_hoc
    
    # Mock contingency tables for pairwise comparisons
    tables = [
        [[10, 5], [2, 20]], # Arch A vs B
        [[8, 7], [3, 18]],  # Arch A vs C
        [[12, 3], [1, 22]]  # Arch B vs C
    ]
    
    try:
        result = mcnemar_post_hoc(tables)
        assert "adjusted_p_values" in result
    except ImportError:
        pytest.skip("Scipy not available")

def test_latency_t_test():
    """Test Paired t-test for latency (T034c)."""
    from analyzers.statistical_test import compare_latency_t_test
    
    arch_a_latencies = [100, 110, 105, 120, 95]
    arch_b_latencies = [102, 108, 103, 118, 98]
    
    try:
        result = compare_latency_t_test(arch_a_latencies, arch_b_latencies)
        assert "statistic" in result
        assert "p_value" in result
    except ImportError:
        pytest.skip("Scipy not available")

def test_monte_carlo_fallback():
    """Test Monte Carlo fallback for small N (T038)."""
    from analyzers.statistical_test import cochrans_q_monte_carlo
    
    # Small dataset that violates assumptions
    data = [
        [1, 0],
        [1, 1],
        [0, 0],
        [1, 1],
        [0, 1]
    ]
    
    try:
        result = cochrans_q_monte_carlo(data, n_simulations=1000)
        assert "p_value" in result
    except ImportError:
        pytest.skip("Scipy not available")
