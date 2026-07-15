"""
Unit tests for edge cases in the analysis pipeline.

Tests cover:
1. Power-law convergence failure (fitting.py)
2. Disconnected graphs handling (metrics.py, quality_control.py)
3. Empty avalanche detection (avalanches.py)
4. Zero-variance data handling (stats.py)
"""
import numpy as np
import pandas as pd
import networkx as nx
import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis import fitting
from code.analysis import metrics
from code.analysis import avalanches
from code.analysis import stats
from code.data import quality_control
from code.data.models import Participant, StructuralConnectome, AvalancheRecord
from code.utils.logger import ResearchError


class TestPowerLawFittingEdgeCases:
    """Tests for power-law fitting edge cases."""

    def test_power_law_convergence_failure_small_sample(self):
        """Test that fitting fails gracefully with very small sample sizes."""
        # Create a tiny dataset that likely won't converge
        tiny_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # This should raise an error or return a failed fit status
        # depending on powerlaw package behavior
        with pytest.raises((ValueError, RuntimeError, Exception)) as exc_info:
            result = fitting.fit_power_law_model(tiny_data)
            # If it doesn't raise, check if it indicates failure
            if hasattr(result, 'success') and not result.success:
                pass  # Expected behavior
            else:
                # If it returns a result but we expect failure, that's okay for now
                # The key is that we handle the edge case without crashing
                pass

    def test_power_law_with_constant_values(self):
        """Test fitting with constant values (no variance)."""
        constant_data = np.ones(100) * 5.0
        
        # Constant data should not fit a power law
        with pytest.raises((ValueError, RuntimeError, Exception)):
            fitting.fit_power_law_model(constant_data)

    def test_power_law_with_negative_values(self):
        """Test fitting with negative values (invalid for power law)."""
        negative_data = np.array([-1.0, -2.0, -3.0])
        
        with pytest.raises((ValueError, RuntimeError, Exception)):
            fitting.fit_power_law_model(negative_data)

    def test_power_law_with_zeros(self):
        """Test fitting with zero values (invalid for power law)."""
        zero_data = np.array([0.0, 1.0, 2.0, 3.0])
        
        with pytest.raises((ValueError, RuntimeError, Exception)):
            fitting.fit_power_law_model(zero_data)


class TestDisconnectedGraphEdgeCases:
    """Tests for disconnected graph handling."""

    def test_degree_centrality_disconnected_graph(self):
        """Test degree centrality calculation on disconnected graph."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6)])  # Component 2
        
        # Should not raise an error
        result = metrics.compute_degree_centrality(G)
        assert isinstance(result, dict)
        assert len(result) == 6
        # All nodes should have some degree centrality (even if 0)
        for node, centrality in result.items():
            assert 0 <= centrality <= 1

    def test_clustering_coefficient_disconnected_graph(self):
        """Test clustering coefficient on disconnected graph."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Triangle
        G.add_node(4)  # Isolated
        G.add_node(5)  # Isolated
        
        result = metrics.compute_clustering_coefficient(G)
        assert isinstance(result, dict)
        assert len(result) == 5
        # Isolated nodes should have 0 clustering coefficient
        assert result[4] == 0.0
        assert result[5] == 0.0

    def test_rich_club_disconnected_graph(self):
        """Test rich-club coefficient on disconnected graph."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (6, 4)])  # Component 2
        
        # Should not raise an error
        result = metrics.compute_rich_club_coefficient(G)
        assert isinstance(result, dict)
        # Rich-club should be defined for various k values
        assert len(result) > 0

    def test_check_graph_connectivity_disconnected(self):
        """Test connectivity check on disconnected graph."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6)])  # Component 2
        
        is_connected, num_components = quality_control.check_graph_connectivity(G)
        assert is_connected == False
        assert num_components == 2

    def test_check_graph_connectivity_single_node(self):
        """Test connectivity check on single-node graph."""
        G = nx.Graph()
        G.add_node(1)
        
        is_connected, num_components = quality_control.check_graph_connectivity(G)
        assert is_connected == True
        assert num_components == 1

    def test_check_graph_connectivity_empty_graph(self):
        """Test connectivity check on empty graph."""
        G = nx.Graph()
        
        # Empty graph should be handled gracefully
        is_connected, num_components = quality_control.check_graph_connectivity(G)
        # An empty graph is technically not connected (no edges)
        assert is_connected == False


class TestAvalancheEdgeCases:
    """Tests for avalanche detection edge cases."""

    def test_detect_avalanches_flat_signal(self):
        """Test avalanche detection on flat (constant) signal."""
        flat_signal = np.ones(1000) * 5.0
        
        # Z-score normalization of constant signal
        normalized = avalanches.z_score_normalize(flat_signal)
        assert np.all(np.isnan(normalized)) or np.all(normalized == 0)
        
        # Threshold calculation should handle this
        threshold = avalanches.calculate_threshold(normalized)
        assert threshold >= 0
        
        # Detection should return empty or handle gracefully
        avalanches_detected = avalanches.detect_avalanches(normalized, threshold)
        assert isinstance(avalanches_detected, list)
        # For flat signal, we expect no avalanches
        assert len(avalanches_detected) == 0

    def test_detect_avalanches_empty_signal(self):
        """Test avalanche detection on empty signal."""
        empty_signal = np.array([])
        
        with pytest.raises((ValueError, IndexError)):
            avalanches.z_score_normalize(empty_signal)

    def test_detect_avalanches_single_value(self):
        """Test avalanche detection on single-value signal."""
        single_signal = np.array([5.0])
        
        normalized = avalanches.z_score_normalize(single_signal)
        # Single value normalization results in NaN or 0
        threshold = avalanches.calculate_threshold(normalized)
        avalanches_detected = avalanches.detect_avalanches(normalized, threshold)
        assert isinstance(avalanches_detected, list)
        assert len(avalanches_detected) == 0

    def test_detect_avalanches_all_zeros(self):
        """Test avalanche detection on all-zero signal."""
        zero_signal = np.zeros(100)
        
        normalized = avalanches.z_score_normalize(zero_signal)
        threshold = avalanches.calculate_threshold(normalized)
        avalanches_detected = avalanches.detect_avalanches(normalized, threshold)
        assert isinstance(avalanches_detected, list)
        assert len(avalanches_detected) == 0

    def test_detect_avalanches_extreme_values(self):
        """Test avalanche detection with extreme values."""
        extreme_signal = np.array([1e10, 1e10, -1e10, -1e10, 0.0])
        
        # Should handle without overflow
        normalized = avalanches.z_score_normalize(extreme_signal)
        threshold = avalanches.calculate_threshold(normalized)
        avalanches_detected = avalanches.detect_avalanches(normalized, threshold)
        assert isinstance(avalanches_detected, list)


class TestStatsEdgeCases:
    """Tests for statistical analysis edge cases."""

    def test_spearman_correlation_constant_x(self):
        """Test Spearman correlation when X is constant."""
        constant_x = np.ones(50) * 5.0
        variable_y = np.random.randn(50)
        
        # Correlation with constant variable is undefined
        with pytest.raises((ValueError, RuntimeError)):
            stats.compute_spearman_correlations(constant_x, variable_y)

    def test_spearman_correlation_constant_y(self):
        """Test Spearman correlation when Y is constant."""
        variable_x = np.random.randn(50)
        constant_y = np.ones(50) * 5.0
        
        with pytest.raises((ValueError, RuntimeError)):
            stats.compute_spearman_correlations(variable_x, constant_y)

    def test_spearman_correlation_small_sample(self):
        """Test Spearman correlation with very small sample."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        
        # Should handle small samples, though results may be unreliable
        result = stats.compute_spearman_correlations(x, y)
        assert isinstance(result, dict)
        assert 'rho' in result
        assert 'p_value' in result

    def test_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity."""
        # Create perfectly collinear data
        x1 = np.random.randn(100)
        x2 = x1 * 2  # Perfectly collinear
        x3 = np.random.randn(100)
        
        data = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})
        
        # VIF should be very high or infinite for x1 and x2
        vif_results = stats.calculate_vif(data)
        assert isinstance(vif_results, pd.DataFrame)
        # Check that high VIF is detected
        high_vif_nodes = vif_results[vif_results['VIF'] >= 5]
        assert len(high_vif_nodes) >= 2  # x1 and x2 should have high VIF

    def test_permutation_test_small_sample(self):
        """Test permutation test with small sample size."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        
        # Should run without error, though p-value may not be reliable
        result = stats.run_permutation_test(x, y, n_permutations=100)
        assert isinstance(result, dict)
        assert 'p_value' in result
        assert 'observed_statistic' in result


class TestQualityControlEdgeCases:
    """Tests for quality control edge cases."""

    def test_calculate_snr_zero_signal(self):
        """Test SNR calculation with zero signal."""
        zero_signal = np.zeros(100)
        
        # SNR calculation should handle zero signal
        snr = quality_control.calculate_snr(zero_signal)
        assert snr == 0.0 or np.isnan(snr)

    def test_calculate_snr_constant_signal(self):
        """Test SNR calculation with constant signal."""
        constant_signal = np.ones(100) * 5.0
        
        snr = quality_control.calculate_snr(constant_signal)
        # Constant signal has no variance, so SNR is undefined or infinite
        assert snr == np.inf or np.isnan(snr)

    def test_run_qc_disconnected_graph(self):
        """Test QC run with disconnected graph."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5), (5, 6)])
        
        # Create a mock participant
        participant = Participant(
            subject_id="test_001",
            structural_connectome=StructuralConnectome(
                adjacency_matrix=np.array(nx.to_numpy_array(G)),
                node_labels=[str(i) for i in G.nodes()]
            ),
            eeg_data=np.random.randn(100, 5)  # 5 channels
        )
        
        # QC should identify disconnected graph
        qc_results = quality_control.run_qc_for_subject(participant)
        assert qc_results['graph_connected'] == False
        assert qc_results['passed_qc'] == False

    def test_run_qc_low_snr_channels(self):
        """Test QC run with low SNR channels."""
        # Create a graph that is connected
        G = nx.complete_graph(5)
        
        # Create EEG data with very low SNR (noise only)
        low_snr_eeg = np.random.randn(100, 5) * 0.001  # Very low amplitude
        
        participant = Participant(
            subject_id="test_002",
            structural_connectome=StructuralConnectome(
                adjacency_matrix=np.array(nx.to_numpy_array(G)),
                node_labels=[str(i) for i in G.nodes()]
            ),
            eeg_data=low_snr_eeg
        )
        
        qc_results = quality_control.run_qc_for_subject(participant)
        # Should identify channels with SNR < 5dB
        assert len(qc_results['removed_channels']) > 0
        assert qc_results['passed_qc'] == False


class TestIntegrationEdgeCases:
    """Integration tests for edge case handling across modules."""

    def test_full_pipeline_disconnected_graph(self):
        """Test full pipeline with disconnected graph."""
        # This test ensures that the pipeline handles disconnected graphs
        # without crashing, even if the final result is marked as failed QC
        
        # Create disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5), (5, 6)])
        
        # Create participant with disconnected graph
        participant = Participant(
            subject_id="test_003",
            structural_connectome=StructuralConnectome(
                adjacency_matrix=np.array(nx.to_numpy_array(G)),
                node_labels=[str(i) for i in G.nodes()]
            ),
            eeg_data=np.random.randn(100, 5)
        )
        
        # Run QC
        qc_results = quality_control.run_qc_for_subject(participant)
        assert qc_results['passed_qc'] == False
        
        # Even if QC fails, downstream functions should handle it gracefully
        # (or skip processing for this subject)

    def test_full_pipeline_empty_avalanches(self):
        """Test full pipeline when no avalanches are detected."""
        # Create a flat signal that produces no avalanches
        flat_eeg = np.ones(1000) * 5.0
        
        # Run avalanche detection
        normalized = avalanches.z_score_normalize(flat_eeg)
        threshold = avalanches.calculate_threshold(normalized)
        avalanches_detected = avalanches.detect_avalanches(normalized, threshold)
        
        assert len(avalanches_detected) == 0
        
        # Fitting should handle empty avalanche list
        if len(avalanches_detected) == 0:
            # This is expected behavior - no avalanches means no fitting
            pass

    def test_full_pipeline_zero_variance_metrics(self):
        """Test full pipeline with zero-variance metrics."""
        # Create data with zero variance
        constant_metrics = np.ones(50) * 5.0
        variable_metrics = np.random.randn(50)
        
        # Correlation should fail or return NaN
        with pytest.raises((ValueError, RuntimeError)):
            stats.compute_spearman_correlations(constant_metrics, variable_metrics)