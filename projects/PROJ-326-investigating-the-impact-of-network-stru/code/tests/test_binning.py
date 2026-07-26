"""
Unit tests for the binning logic in code/src/generators/binning.py.
"""

import pytest
import networkx as nx
import numpy as np
from unittest.mock import patch, MagicMock

from code.src.generators.binning import classify_graph, _get_bin_boundaries, get_bin_range


class TestBinningLogic:
    """Tests for graph classification into clustering bins."""

    def test_classify_graph_watts_strogatz_low_rewiring(self):
        """Test that a Watts-Strogatz graph with low rewiring (high clustering) is classified correctly."""
        # Create a small WS graph with low rewiring -> high clustering
        G = nx.watts_strogatz_graph(n=20, k=4, p=0.0, seed=42)
        # Expected clustering should be high (> 0.5 usually for this config)
        
        # Mock config to force specific bins for deterministic testing
        mock_config = {
            "stratification_params": {
                "bins": [0.1, 0.3, 0.5, 0.7],
                "target_counts": {"bin_0": 1, "bin_1": 1, "bin_2": 1, "bin_3": 1, "bin_4": 1},
                "tolerance": 0.1
            }
        }

        with patch('code.src.generators.binning.get_global_config', return_value=mock_config):
            # WS with p=0 usually has clustering ~ k/(2(n-1)) -> 4/38 ~ 0.1, but for small n=20, k=4 it's actually 3/5 = 0.6
            # Let's calculate actual
            actual_cc = nx.average_clustering(G)
            result = classify_graph(G)
            
            # With bins [0.1, 0.3, 0.5, 0.7]:
            # If 0.6 < 0.7 -> bin_3. If 0.6 >= 0.7 -> bin_4.
            # 0.6 is < 0.7, so bin_3.
            assert result.startswith("bin_")
            assert result != "bin_0"  # Should be a higher bin

    def test_classify_graph_erdos_renyi(self):
        """Test classification of an Erdos-Renyi graph."""
        # ER graph with p=0.1 on 50 nodes -> expected clustering ~ p = 0.1
        G = nx.erdos_renyi_graph(n=50, p=0.1, seed=42)
        
        mock_config = {
            "stratification_params": {
                "bins": [0.05, 0.15, 0.25],
                "target_counts": {},
                "tolerance": 0.1
            }
        }

        with patch('code.src.generators.binning.get_global_config', return_value=mock_config):
            result = classify_graph(G)
            assert result.startswith("bin_")

    def test_classify_graph_small_network(self):
        """Test classification of a graph with < 3 nodes (edge case)."""
        G = nx.Graph()
        G.add_nodes_from([1, 2])
        
        mock_config = {
            "stratification_params": {
                "bins": [0.1, 0.5],
                "target_counts": {},
                "tolerance": 0.1
            }
        }

        with patch('code.src.generators.binning.get_global_config', return_value=mock_config):
            # Should not raise, should return bin_0
            result = classify_graph(G)
            assert result == "bin_0"

    def test_get_bin_boundaries_default(self):
        """Test that _get_bin_boundaries raises error if config is missing."""
        with patch('code.src.generators.binning.get_global_config', return_value=None):
            with pytest.raises(ValueError, match="Global config is not loaded"):
                _get_bin_boundaries()

    def test_get_bin_boundaries_missing_key(self):
        """Test error when bins key is missing."""
        mock_config = {"stratification_params": {}}
        with patch('code.src.generators.binning.get_global_config', return_value=mock_config):
            with pytest.raises(ValueError, match="Configuration missing"):
                _get_bin_boundaries()

    def test_get_bin_range(self):
        """Test calculation of bin ranges."""
        mock_config = {
            "stratification_params": {
                "bins": [0.2, 0.5],
                "target_counts": {},
                "tolerance": 0.1
            }
        }
        
        with patch('code.src.generators.binning.get_global_config', return_value=mock_config):
            # bin_0: [0.0, 0.2)
            assert get_bin_range("bin_0") == (0.0, 0.2)
            # bin_1: [0.2, 0.5)
            assert get_bin_range("bin_1") == (0.2, 0.5)
            # bin_2: [0.5, 1.0] (last bin)
            assert get_bin_range("bin_2") == (0.5, 1.0)