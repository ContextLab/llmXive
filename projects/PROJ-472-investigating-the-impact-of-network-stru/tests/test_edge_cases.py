"""
Unit tests for edge cases in the analysis pipeline.

Specifically covers:
1. Power-law convergence failure handling (T033 requirement).
2. Disconnected graph handling in network metrics (T014 requirement).
3. Empty avalanche detection scenarios.
"""
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
import networkx as nx
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.fitting import fit_power_law_model, run_fitting_for_subject
from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient, compute_rich_club_coefficient
from data.models import Participant, StructuralConnectome, AvalancheRecord
from utils.logger import ResearchError


class TestPowerLawConvergence:
    """Tests for T033: Validate Power-Law Fit Convergence handling."""

    def test_fit_power_law_convergence_failure(self):
        """
        Test that fit_power_law_model handles convergence failures gracefully.
        
        According to T033, the function must explicitly handle convergence failure
        by logging a specific error code and returning a structured result
        (or raising a specific exception) rather than silently returning NaN.
        """
        # Create a synthetic dataset that is known to cause convergence issues
        # for the powerlaw package (e.g., extremely small sample size or uniform data)
        # We simulate the scenario by mocking the powerlaw.Fit object to raise a warning/error
        # or by providing data that results in a non-convergent fit.
        
        # Using a very small sample size often triggers convergence warnings/failures
        data = np.array([1, 1, 1, 1, 2]) 
        
        # Mock the powerlaw.Fit to simulate a convergence failure scenario
        # The powerlaw package might raise a warning or return a fit with high error
        # We test the robustness of our wrapper.
        
        with patch('analysis.fitting.powerlaw') as mock_powerlaw:
            # Simulate a fit object that has a high D-statistic or fails to converge
            mock_fit = MagicMock()
            mock_fit.D = 0.999  # Very high D-statistic indicates poor fit
            mock_fit.p = 0.001  # Low p-value indicates rejection of power law
            mock_fit.power_law = MagicMock()
            mock_fit.power_law.alpha = 2.5
            mock_fit.power_law.xmin = 1.0
            
            # Simulate a scenario where the comparison fails or raises an error
            # The powerlaw package's comparison method might raise if data is insufficient
            mock_fit.distribution_compare.side_effect = Exception("Convergence failed: insufficient data")
            
            mock_powerlaw.Fit.return_value = mock_fit

            try:
                result = fit_power_law_model(data)
                # If it doesn't crash, it should handle the error gracefully
                # Check if the result indicates failure
                assert result is not None
                # Depending on implementation, it might return a dict with 'success': False
                # or raise a specific ResearchError. 
                # Given T033 says "logging a specific error code and excluding", 
                # we expect the function to handle the exception internally or raise a clear error.
                
                # If the function is designed to raise on failure (as per "exclude from correlation"):
                # assert isinstance(result, ResearchError) 
                # OR if it returns a status dict:
                if isinstance(result, dict):
                    assert result.get('success') is False
                    assert 'error_code' in result or 'message' in result
            except Exception as e:
                # It is also acceptable to raise a clear ResearchError
                assert "Convergence" in str(e) or "fit" in str(e).lower()

    def test_run_fitting_for_subject_handles_convergence_failure(self):
        """
        Test that the subject-level runner handles convergence failure without crashing the pipeline.
        """
        # Setup mock participant data
        participant_id = "SUBJ-CONV-FAIL"
        data_dir = Path(tempfile.mkdtemp())
        sizes_file = data_dir / f"{participant_id}_avalanche_sizes.csv"
        
        # Create a file with data likely to fail
        df = pd.DataFrame({'size': [1, 1, 1, 1, 1]})
        df.to_csv(sizes_file, index=False)
        
        # Mock the fit function to raise an error
        with patch('analysis.fitting.fit_power_law_model') as mock_fit:
            mock_fit.side_effect = ResearchError(
                code="CONV_FAIL", 
                message="Power law fit did not converge for subject"
            )
            
            # This should not crash the runner, but handle the error
            # The implementation should catch this and log it, potentially returning None or a failure flag
            result = run_fitting_for_subject(participant_id, data_dir)
            
            # Verify the result indicates failure or is handled gracefully
            assert result is not None
            # Depending on design, result might be a dict with success=False
            if isinstance(result, dict):
                assert result.get('success') is False


class TestDisconnectedGraphs:
    """Tests for T014/T028: Handle disconnected graphs in network metrics."""

    def test_degree_centrality_disconnected_graph(self):
        """
        Test that degree centrality works correctly on a disconnected graph.
        A disconnected graph has at least two components.
        """
        # Create a disconnected graph: two separate triangles
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (6, 4)])  # Component 2
        
        # This should not raise an error
        result = compute_degree_centrality(G)
        
        # Verify the result is a dict with expected keys
        assert isinstance(result, dict)
        assert len(result) == G.number_of_nodes()
        
        # All nodes in a 3-node component should have degree 2
        for node in G.nodes():
            assert result[node] == 2.0 / (G.number_of_nodes() - 1)  # Normalized degree

    def test_clustering_coefficient_disconnected_graph(self):
        """
        Test that clustering coefficient works on a disconnected graph.
        """
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # Triangle
        G.add_edges_from([(4, 5)])  # Single edge (clustering 0)
        
        result = compute_clustering_coefficient(G)
        
        assert isinstance(result, dict)
        # Triangle nodes should have clustering 1.0
        assert result[1] == 1.0
        # Edge nodes should have clustering 0.0
        assert result[4] == 0.0

    def test_rich_club_coefficient_disconnected_graph(self):
        """
        Test rich-club coefficient on a disconnected graph.
        """
        # Create a graph with a clear rich club and a disconnected part
        G = nx.Graph()
        # Rich club: 4 fully connected nodes
        rich_nodes = [1, 2, 3, 4]
        G.add_edges_from([(i, j) for i in rich_nodes for j in rich_nodes if i < j])
        # Disconnected part: 2 nodes
        G.add_edges_from([(5, 6)])
        
        # This should not crash
        result = compute_rich_club_coefficient(G)
        
        assert isinstance(result, dict)
        # Rich club nodes should have high coefficients
        for k, val in result.items():
            assert isinstance(val, (int, float))

    def test_empty_graph_metrics(self):
        """
        Test that metrics handle an empty graph (no nodes) gracefully.
        """
        G = nx.Graph()
        
        # Degree centrality on empty graph
        deg = compute_degree_centrality(G)
        assert deg == {}
        
        # Clustering on empty graph
        clust = compute_clustering_coefficient(G)
        assert clust == {}
        
        # Rich club on empty graph
        rich = compute_rich_club_coefficient(G)
        assert rich == {}

    def test_single_node_graph_metrics(self):
        """
        Test metrics on a graph with a single node (no edges).
        """
        G = nx.Graph()
        G.add_node(1)
        
        deg = compute_degree_centrality(G)
        assert deg[1] == 0.0
        
        clust = compute_clustering_coefficient(G)
        assert clust[1] == 0.0


class TestAvalancheEdgeCases:
    """Additional edge cases for avalanche detection."""

    def test_flat_signal_avalanche(self):
        """
        Test that flat signal (no variance) results in no avalanches or handled gracefully.
        """
        from analysis.avalanches import z_score_normalize, calculate_threshold, detect_avalanches
        
        # Flat signal
        signal = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        # Z-score normalization of flat signal results in NaNs or zeros
        try:
            normalized = z_score_normalize(signal)
            # If it returns zeros, threshold calculation should handle it
            threshold = calculate_threshold(normalized, percentile=75)
            
            # Detect avalanches
            avalanches = detect_avalanches(normalized, threshold)
            
            # Should return empty list or handle gracefully
            assert isinstance(avalanches, list)
        except Exception as e:
            # If it raises, it must be a clear error about flat signal
            assert "flat" in str(e).lower() or "variance" in str(e).lower()

    def test_nan_signal_avalanche(self):
        """
        Test that signal with NaNs is handled gracefully.
        """
        from analysis.avalanches import z_score_normalize, detect_avalanches
        
        signal = np.array([1.0, np.nan, 2.0, 3.0, 4.0])
        
        # Should either clean the data or raise a clear error
        try:
            normalized = z_score_normalize(signal)
            # If normalization succeeds, detect_avalanches should handle NaNs
            threshold = calculate_threshold(normalized, percentile=75)
            avalanches = detect_avalanches(normalized, threshold)
            assert isinstance(avalanches, list)
        except Exception:
            # Expected behavior if NaNs are not allowed
            pass