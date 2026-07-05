"""
Unit tests for simulation module, specifically spatial variance calculation and divergence detection.
"""
import pytest
import numpy as np
import networkx as nx
from typing import List, Dict, Any

# Import the function under test from the simulation module
# The function is expected to be in code/src/simulation/metrics.py
# We import it here for testing. If the file doesn't exist yet, this test
# will fail with ImportError, which is the expected behavior for TDD
# (Write test first, ensure it fails before implementation).
try:
    from code.src.simulation.metrics import calculate_spatial_variance
except ImportError:
    # If the module doesn't exist yet, we define a placeholder to allow
    # the test structure to be valid, but the test will logically fail
    # or be skipped. In a real TDD flow, the implementer creates the file.
    def calculate_spatial_variance(spins: np.ndarray, graph: nx.Graph) -> float:
        raise NotImplementedError("calculate_spatial_variance not yet implemented")

# Import divergence detection functions
# Expected in code/src/simulation/stability.py
try:
    from code.src.simulation.stability import check_divergence, detect_abnormal_energy_growth
except ImportError:
    # Placeholder for TDD
    def check_divergence(energy_history: List[float], threshold: float = 1e6) -> bool:
        raise NotImplementedError("check_divergence not yet implemented")
    
    def detect_abnormal_energy_growth(
        energy_history: List[float], 
        growth_rate_threshold: float = 1.0, 
        min_steps: int = 5
    ) -> bool:
        raise NotImplementedError("detect_abnormal_energy_growth not yet implemented")


class TestSpatialVarianceCalculation:
    """
    Tests for the spatial variance calculation in spin systems.
    Spatial variance measures the heterogeneity of spin energy distribution
    across the network topology.
    """

    def test_spatial_variance_complete_alignment(self):
        """
        Test that spatial variance is zero when all spins are aligned.
        """
        # Create a simple ring graph
        graph = nx.cycle_graph(10)
        
        # All spins up (1.0) - complete alignment
        spins = np.ones(10)
        
        variance = calculate_spatial_variance(spins, graph)
        
        # With perfect alignment, variance should be effectively zero
        assert np.isclose(variance, 0.0, atol=1e-10), \
            f"Expected variance ~0 for aligned spins, got {variance}"

    def test_spatial_variance_alternating_spins(self):
        """
        Test spatial variance with alternating spin configuration.
        This should produce a non-zero, calculable variance.
        """
        # Create a path graph
        graph = nx.path_graph(4)
        
        # Alternating spins: [1, -1, 1, -1]
        spins = np.array([1.0, -1.0, 1.0, -1.0])
        
        variance = calculate_spatial_variance(spins, graph)
        
        # Calculate expected variance manually:
        # Mean = (1 - 1 + 1 - 1) / 4 = 0
        # Squared differences: (1-0)^2, (-1-0)^2, (1-0)^2, (-1-0)^2 = 1, 1, 1, 1
        # Variance = (1+1+1+1)/4 = 1.0
        expected_variance = 1.0
        
        assert np.isclose(variance, expected_variance, atol=1e-10), \
            f"Expected variance {expected_variance}, got {variance}"

    def test_spatial_variance_random_spins(self):
        """
        Test spatial variance with random spin configuration.
        """
        np.random.seed(42)  # For reproducibility
        n_nodes = 20
        graph = nx.watts_strogatz_graph(n_nodes, 4, 0.1)
        
        # Random spins between -1 and 1
        spins = np.random.uniform(-1, 1, n_nodes)
        
        variance = calculate_spatial_variance(spins, graph)
        
        # Variance must be non-negative
        assert variance >= 0.0, f"Variance cannot be negative: {variance}"
        
        # For random uniform [-1, 1], theoretical variance is approx 1/3
        # We just check it's in a reasonable range
        assert 0.1 < variance < 0.8, \
            f"Variance {variance} out of expected range for random spins"

    def test_spatial_variance_empty_graph(self):
        """
        Test that spatial variance handles an empty graph gracefully.
        """
        graph = nx.Graph()
        spins = np.array([])
        
        # Should either return 0 or raise a specific error
        # We expect it to return 0.0 for empty input
        variance = calculate_spatial_variance(spins, graph)
        
        assert np.isclose(variance, 0.0, atol=1e-10), \
            f"Expected variance 0.0 for empty graph, got {variance}"

    def test_spatial_variance_single_node(self):
        """
        Test spatial variance with a single node.
        """
        graph = nx.Graph()
        graph.add_node(0)
        spins = np.array([1.0])
        
        variance = calculate_spatial_variance(spins, graph)
        
        # Single node: variance should be 0 (no deviation from mean)
        assert np.isclose(variance, 0.0, atol=1e-10), \
            f"Expected variance 0.0 for single node, got {variance}"

    def test_spatial_variance_weighted_graph(self):
        """
        Test that spatial variance calculation considers graph topology.
        Note: The current implementation might be a simple statistical variance.
        If the spec requires topology-weighted variance, this test validates that.
        """
        # Create a graph with two disconnected components
        graph = nx.Graph()
        graph.add_nodes_from([0, 1, 2, 3, 4, 5])
        graph.add_edges_from([(0, 1), (1, 2), (3, 4), (4, 5)])
        
        # Spins: component 1 (0,1,2) all up, component 2 (3,4,5) all down
        spins = np.array([1.0, 1.0, 1.0, -1.0, -1.0, -1.0])
        
        variance = calculate_spatial_variance(spins, graph)
        
        # Mean = 0
        # Squared diffs: 1, 1, 1, 1, 1, 1 -> sum = 6
        # Variance = 6/6 = 1.0
        expected_variance = 1.0
        
        assert np.isclose(variance, expected_variance, atol=1e-10), \
            f"Expected variance {expected_variance}, got {variance}"

    def test_spatial_variance_dtype_preservation(self):
        """
        Test that the output dtype is appropriate (float).
        """
        graph = nx.path_graph(5)
        spins = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
        
        variance = calculate_spatial_variance(spins, graph)
        
        # Result should be a float
        assert isinstance(variance, (float, np.floating)), \
            f"Expected float output, got {type(variance)}"


class TestDivergenceDetection:
    """
    Tests for divergence detection and abort logic in spin simulations.
    These tests verify that numerical instabilities are correctly identified
    and that the simulation abort logic functions as expected.
    """

    def test_check_divergence_no_divergence(self):
        """
        Test that normal energy values do not trigger divergence.
        """
        # Normal energy history (stable simulation)
        energy_history = [1.0, 1.1, 1.05, 1.08, 1.02]
        threshold = 1e6  # Very high threshold
        
        is_divergent = check_divergence(energy_history, threshold)
        
        assert not is_divergent, "Normal values should not trigger divergence"

    def test_check_divergence_exceeds_threshold(self):
        """
        Test that energy exceeding threshold triggers divergence detection.
        """
        # Energy history with one extreme value
        energy_history = [1.0, 1.1, 1.05, 1e7, 1.02]
        threshold = 1e6
        
        is_divergent = check_divergence(energy_history, threshold)
        
        assert is_divergent, "Energy exceeding threshold should trigger divergence"

    def test_check_divergence_negative_threshold(self):
        """
        Test that negative energy values exceeding magnitude trigger divergence.
        """
        # Energy history with large negative value
        energy_history = [1.0, 1.1, 1.05, -1e7, 1.02]
        threshold = 1e6
        
        is_divergent = check_divergence(energy_history, threshold)
        
        assert is_divergent, "Large negative energy should trigger divergence"

    def test_check_divergence_empty_history(self):
        """
        Test that empty energy history does not trigger divergence.
        """
        energy_history = []
        threshold = 1e6
        
        is_divergent = check_divergence(energy_history, threshold)
        
        assert not is_divergent, "Empty history should not trigger divergence"

    def test_check_divergence_single_value(self):
        """
        Test divergence check with single energy value.
        """
        energy_history = [1.0]
        threshold = 1e6
        
        is_divergent = check_divergence(energy_history, threshold)
        
        assert not is_divergent, "Single normal value should not trigger divergence"

    def test_detect_abnormal_growth_normal(self):
        """
        Test that normal growth rates do not trigger abort.
        """
        # Normal exponential decay (stable)
        energy_history = [1.0, 0.9, 0.81, 0.729, 0.6561]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.0, 
            min_steps=3
        )
        
        assert not is_abnormal, "Normal decay should not trigger abort"

    def test_detect_abnormal_growth_explosive(self):
        """
        Test that explosive growth triggers abort logic.
        """
        # Explosive exponential growth
        energy_history = [1.0, 2.0, 4.0, 8.0, 16.0]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.5,  # Growth rate > 1.5 per step
            min_steps=3
        )
        
        assert is_abnormal, "Explosive growth should trigger abort"

    def test_detect_abnormal_growth_oscillating(self):
        """
        Test that oscillating energy does not trigger abort.
        """
        # Oscillating energy (stable but fluctuating)
        energy_history = [1.0, 0.5, 1.0, 0.5, 1.0]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.0, 
            min_steps=3
        )
        
        assert not is_abnormal, "Oscillating values should not trigger abort"

    def test_detect_abnormal_growth_insufficient_steps(self):
        """
        Test that insufficient history length does not trigger abort.
        """
        # Too few steps to evaluate
        energy_history = [1.0, 2.0]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.5, 
            min_steps=5
        )
        
        assert not is_abnormal, "Insufficient steps should not trigger abort"

    def test_detect_abnormal_growth_just_below_threshold(self):
        """
        Test growth rate just below threshold does not trigger abort.
        """
        # Growth rate exactly at threshold boundary
        # 1.0 -> 1.4 -> 1.96 -> 2.744 -> 3.8416 (ratio ~1.4 each step)
        energy_history = [1.0, 1.4, 1.96, 2.744, 3.8416]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.5,  # Threshold is 1.5, actual is 1.4
            min_steps=3
        )
        
        assert not is_abnormal, "Growth below threshold should not trigger abort"

    def test_detect_abnormal_growth_just_above_threshold(self):
        """
        Test growth rate just above threshold triggers abort.
        """
        # Growth rate slightly above threshold
        # 1.0 -> 1.6 -> 2.56 -> 4.096 -> 6.5536 (ratio ~1.6 each step)
        energy_history = [1.0, 1.6, 2.56, 4.096, 6.5536]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.5,  # Threshold is 1.5, actual is 1.6
            min_steps=3
        )
        
        assert is_abnormal, "Growth above threshold should trigger abort"

    def test_detect_abnormal_growth_with_zeros(self):
        """
        Test handling of zero values in energy history.
        """
        # Energy history with zeros (could cause division issues)
        energy_history = [1.0, 0.0, 0.0, 0.0, 0.0]
        
        # Should not crash and should not trigger abort (no growth)
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.0, 
            min_steps=3
        )
        
        assert not is_abnormal, "Zero values should not cause crash or false abort"

    def test_detect_abnormal_growth_with_negative_values(self):
        """
        Test handling of negative energy values.
        """
        # Energy history with negative values
        energy_history = [1.0, -1.0, 1.0, -1.0, 1.0]
        
        # Should not crash
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.0, 
            min_steps=3
        )
        
        # Oscillating sign changes should not be considered "growth"
        assert not is_abnormal, "Sign oscillation should not trigger abort"

    def test_detect_abnormal_growth_very_small_values(self):
        """
        Test handling of very small energy values (numerical precision).
        """
        # Very small values near machine epsilon
        energy_history = [1e-10, 1e-10, 1e-10, 1e-10, 1e-10]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.0, 
            min_steps=3
        )
        
        assert not is_abnormal, "Stable small values should not trigger abort"

    def test_detect_abnormal_growth_very_large_values(self):
        """
        Test handling of very large energy values.
        """
        # Very large values
        energy_history = [1e10, 2e10, 4e10, 8e10, 16e10]
        
        is_abnormal = detect_abnormal_energy_growth(
            energy_history, 
            growth_rate_threshold=1.5, 
            min_steps=3
        )
        
        assert is_abnormal, "Explosive large growth should trigger abort"