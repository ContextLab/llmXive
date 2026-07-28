"""
Unit tests for network generation utilities, specifically focusing on User Story 1.
"""
import pytest
import networkx as nx
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from utils.metrics import calculate_clustering_coefficient

# Configuration for tests
NODES = 500
REWIRING_PROBS = [0.0, 0.01, 0.1, 0.5, 1.0]
TOLERANCE = 0.05  # 5% tolerance for theoretical expectations


def test_watts_strogatz_clustering_vs_rewiring():
    """
    Test that the clustering coefficient of Watts-Strogatz networks
    decreases as the rewiring probability increases.

    This test verifies the theoretical behavior where:
    - p=0 (regular lattice) has high clustering
    - p=1 (random graph) has low clustering (similar to Erdos-Renyi)
    """
    # Use a fixed seed for reproducibility
    base_seed = 42
    results = []

    for p in REWIRING_PROBS:
        # Generate multiple instances to get a stable average
        cluster_coeffs = []
        for i in range(5):  # 5 instances per p
            seed = base_seed + int(p * 1000) + i
            G = nx.watts_strogatz_graph(
                n=NODES,
                k=10,  # Average degree
                p=p,
                seed=seed
            )
            
            # Calculate clustering coefficient
            cc = calculate_clustering_coefficient(G)
            cluster_coeffs.append(cc)
        
        avg_cc = np.mean(cluster_coeffs)
        results.append((p, avg_cc))

    # Verify monotonic decrease in clustering coefficient
    # (with some tolerance for stochasticity)
    prev_cc = float('inf')
    for p, cc in results:
        # The clustering coefficient should generally decrease as p increases
        # We allow a small tolerance for stochastic variation
        if p > 0 and cc > prev_cc * 1.1:  # 10% tolerance for stochasticity
            pytest.fail(
                f"Clustering coefficient increased unexpectedly: "
                f"p={p:.2f}, cc={cc:.4f}, previous={prev_cc:.4f}"
            )
        prev_cc = cc

    # Specific checks for extreme cases
    p_zero_cc = next(cc for p, cc in results if p == 0.0)
    p_one_cc = next(cc for p, cc in results if p == 1.0)

    # p=0 should have significantly higher clustering than p=1
    assert p_zero_cc > p_one_cc * 10, (
        f"Watts-Strogatz with p=0 should have much higher clustering than p=1. "
        f"Got p=0: {p_zero_cc:.4f}, p=1: {p_one_cc:.4f}"
    )

    # p=0 should have clustering > 0.5 for k=10, N=500 (theoretical approx)
    # For a ring lattice with k=10, local clustering is ~0.75
    assert p_zero_cc > 0.5, (
        f"Watts-Strogatz with p=0 should have high clustering. "
        f"Got {p_zero_cc:.4f}"
    )

    # p=1 should have clustering similar to Erdos-Renyi with same density
    # Expected CC for ER graph is k/(N-1) ~ 10/499 ~ 0.02
    expected_er_cc = 10 / (NODES - 1)
    tolerance = expected_er_cc * 0.5  # 50% tolerance for small graph effects
    assert abs(p_one_cc - expected_er_cc) < tolerance, (
        f"Watts-Strogatz with p=1 should have clustering similar to ER graph. "
        f"Expected ~{expected_er_cc:.4f}, got {p_one_cc:.4f}"
    )


def test_watts_strogatz_clustering_monotonicity():
    """
    Test that clustering coefficient decreases monotonically with increasing
    rewiring probability (with reasonable tolerance for stochasticity).
    """
    base_seed = 123
    p_values = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
    
    cc_values = []
    for p in p_values:
        # Use multiple seeds to get a stable estimate
        seeds = [base_seed + i for i in range(10)]
        cluster_coeffs = []
        
        for seed in seeds:
            G = nx.watts_strogatz_graph(n=NODES, k=10, p=p, seed=seed)
            cc = calculate_clustering_coefficient(G)
            cluster_coeffs.append(cc)
        
        avg_cc = np.mean(cluster_coeffs)
        cc_values.append(avg_cc)
    
    # Check that the sequence is mostly decreasing (allowing for some noise)
    decreases = 0
    increases = 0
    
    for i in range(1, len(cc_values)):
        if cc_values[i] < cc_values[i-1] * 0.95:  # 5% tolerance
            decreases += 1
        elif cc_values[i] > cc_values[i-1] * 1.05:
            increases += 1
    
    # At least 80% of transitions should be decreases
    assert decreases / (len(cc_values) - 1) >= 0.8, (
        f"Clustering coefficient should generally decrease with rewiring probability. "
        f"Decreases: {decreases}, Increases: {increases}"
    )


def test_watts_strogatz_clustering_theoretical_bounds():
    """
    Test that clustering coefficients fall within theoretical bounds.
    """
    base_seed = 456
    
    for p in [0.0, 0.1, 0.5, 1.0]:
        # Generate multiple instances
        cluster_coeffs = []
        for i in range(10):
            seed = base_seed + i
            G = nx.watts_strogatz_graph(n=NODES, k=10, p=p, seed=seed)
            cc = calculate_clustering_coefficient(G)
            cluster_coeffs.append(cc)
        
        avg_cc = np.mean(cluster_coeffs)
        
        # Clustering coefficient must be between 0 and 1
        assert 0 <= avg_cc <= 1, (
            f"Clustering coefficient must be in [0, 1]. Got {avg_cc:.4f} for p={p}"
        )
        
        # For p=0, should be close to theoretical value for ring lattice
        if p == 0.0:
            # Theoretical clustering for ring lattice with k=10 is (3(k-2))/(4(k-1)) ~ 0.75
            theoretical = 3 * (10 - 2) / (4 * (10 - 1))
            assert abs(avg_cc - theoretical) < 0.1, (
                f"p=0 clustering should be close to theoretical {theoretical:.4f}. "
                f"Got {avg_cc:.4f}"
            )
        
        # For p=1, should be close to ER graph expectation
        if p == 1.0:
            er_expected = 10 / (NODES - 1)
            assert abs(avg_cc - er_expected) < 0.02, (
                f"p=1 clustering should be close to ER expectation {er_expected:.4f}. "
                f"Got {avg_cc:.4f}"
            )