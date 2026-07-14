"""
Unit tests for network generation, specifically verifying Barabási-Albert
power-law degree distribution properties.
"""
import os
import sys
import tempfile
import json
import math

import pytest
import networkx as nx
import numpy as np

# Ensure the code directory is in the path for imports
_code_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if os.path.isdir(_code_path) and _code_path not in sys.path:
    sys.path.insert(0, _code_path)

from utils.metrics import calculate_assortativity, calculate_average_path_length, calculate_clustering_coefficient


def generate_barabasi_albert(N=500, m=3, seed=42):
    """
    Helper to generate a BA graph. In a full implementation, this would
    call the project's generator. Here we use NetworkX directly to
    generate the ground truth for the test.
    """
    G = nx.barabasi_albert_graph(N, m, seed=seed)
    return G


def get_degree_distribution(G):
    """
    Returns a dictionary mapping degree k to the probability P(k).
    """
    degrees = [d for n, d in G.degree()]
    counts = {}
    for d in degrees:
        counts[d] = counts.get(d, 0) + 1
    total = len(degrees)
    return {k: v / total for k, v in counts.items()}


def estimate_gamma_from_degrees(degrees):
    """
    Estimates the power-law exponent gamma using the method of moments
    (approximation: gamma = 1 + N / (sum(log(k/k_min)))).
    This is a standard estimator for discrete power laws.
    """
    if not degrees:
        return None
    # Filter for k >= 1 to avoid log(0)
    valid_degrees = [k for k in degrees if k >= 1]
    if not valid_degrees:
        return None
    
    k_min = 1
    # Estimate gamma using the maximum likelihood estimator for discrete power law
    # gamma = 1 + n / sum(log(x_i / k_min))
    sum_log = sum(math.log(k / k_min) for k in valid_degrees)
    if sum_log == 0:
        return None
    gamma = 1.0 + len(valid_degrees) / sum_log
    return gamma


class TestBarabasiAlbertPowerLaw:
    """
    Test suite for verifying the power-law degree distribution of Barabási-Albert networks.
    
    Theoretical expectation:
    For a Barabási-Albert network, the degree distribution P(k) follows a power law
    P(k) ~ k^(-gamma) with gamma approx 3.0 for large N.
    """

    @pytest.mark.parametrize("N,m,seed", [
        (500, 3, 42),
        (1000, 4, 123),
        (2000, 5, 999)
    ])
    def test_power_law_exponent_near_3(self, N, m, seed):
        """
        Verify that the estimated power-law exponent gamma is close to 3.0.
        Tolerance: 10% (0.3) to account for finite size effects in N=500.
        """
        G = generate_barabasi_albert(N, m, seed)
        degrees = [d for n, d in G.degree()]
        
        gamma = estimate_gamma_from_degrees(degrees)
        
        assert gamma is not None, "Could not estimate gamma"
        
        # For N=500, we expect gamma to be reasonably close to 3.0.
        # Finite size effects might push it slightly higher or lower.
        # A 10% tolerance is generous for small N.
        assert 2.5 <= gamma <= 3.5, f"Estimated gamma {gamma:.2f} is not within expected range [2.5, 3.5]"

    @pytest.mark.parametrize("N,m,seed", [
        (500, 3, 42),
    ])
    def test_log_log_linearity(self, N, m, seed):
        """
        Verify that the degree distribution is linear on a log-log scale,
        which is a hallmark of power-law behavior.
        """
        G = generate_barabasi_albert(N, m, seed)
        dist = get_degree_distribution(G)
        
        # Filter out degrees with zero probability
        log_k = []
        log_p = []
        for k, p in dist.items():
            if p > 0:
                log_k.append(math.log(k))
                log_p.append(math.log(p))
        
        assert len(log_k) > 2, "Not enough data points to fit a line"
        
        # Perform simple linear regression to check linearity
        # y = mx + c
        n = len(log_k)
        sum_x = sum(log_k)
        sum_y = sum(log_p)
        sum_xy = sum(x * y for x, y in zip(log_k, log_p))
        sum_xx = sum(x * x for x in log_k)
        
        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            # All points have same x, degenerate case
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate R-squared
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for y in log_p)
        ss_res = sum((y - (slope * x + (sum_y - slope * sum_x) / n)) ** 2 for x, y in zip(log_k, log_p))
        
        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        # For a power law, R^2 should be high on log-log scale
        # We use a threshold of 0.85 to allow for noise in small networks
        assert r_squared > 0.85, f"Log-log linearity R^2={r_squared:.3f} is too low, expected > 0.85"

    def test_degree_distribution_has_long_tail(self):
        """
        Verify that the degree distribution exhibits a long tail (some nodes have high degree).
        In a power law, the maximum degree should be significantly larger than the mean.
        """
        G = generate_barabasi_albert(500, 3, 42)
        degrees = [d for n, d in G.degree()]
        
        mean_degree = np.mean(degrees)
        max_degree = max(degrees)
        
        # In a BA network with N=500, m=3, max degree should be significantly higher than mean
        # Mean is approx 2*m = 6. Max degree should be at least 3-4x the mean for a clear tail
        assert max_degree > 3 * mean_degree, f"Max degree {max_degree} is not significantly larger than mean {mean_degree}"

    def test_structural_metrics_compatibility(self):
        """
        Verify that the generated network is compatible with the project's metric functions.
        This ensures the test can be extended to use the full pipeline.
        """
        G = generate_barabasi_albert(500, 3, 42)
        
        # These functions should run without error
        assortativity = calculate_assortativity(G)
        avg_path_len = calculate_average_path_length(G)
        clustering = calculate_clustering_coefficient(G)
        
        assert isinstance(assortativity, float)
        assert isinstance(avg_path_len, float)
        assert isinstance(clustering, float)
        
        # BA networks typically have negative assortativity
        assert assortativity < 0.1, "BA networks are typically disassortative"
        
        # BA networks have small-world properties
        assert avg_path_len < 10, "BA networks should have short average path length"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])