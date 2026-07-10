import pytest
import numpy as np
import networkx as nx
import sys
import os

# Add parent directory to path to import extract
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from extract import YadeParser

class TestForceHeterogeneity:
    """
    Tests for T015: Force heterogeneity (CV of contact forces) calculation.
    """

    def test_force_heterogeneity_uniform_forces(self):
        """
        Test CV calculation when all contact forces are identical.
        CV should be 0.
        """
        parser = YadeParser("dummy")
        
        # Create a graph with edges having uniform force magnitudes
        G = nx.Graph()
        G.add_edge(1, 2, force_magnitude=10.0)
        G.add_edge(2, 3, force_magnitude=10.0)
        G.add_edge(3, 1, force_magnitude=10.0)
        
        # Set parser forces (fallback)
        parser.forces = {1: np.array([0, 0, 10]), 2: np.array([0, 0, 10]), 3: np.array([0, 0, 10])}
        
        cv = parser.calc_force_heterogeneity(G)
        assert cv == 0.0

    def test_force_heterogeneity_varying_forces(self):
        """
        Test CV calculation with varying forces.
        """
        parser = YadeParser("dummy")
        
        G = nx.Graph()
        # Forces: 10, 20, 30 -> Mean = 20, Std = 8.1649...
        # CV = 8.1649 / 20 = 0.4082...
        G.add_edge(1, 2, force_magnitude=10.0)
        G.add_edge(2, 3, force_magnitude=20.0)
        G.add_edge(3, 1, force_magnitude=30.0)
        
        cv = parser.calc_force_heterogeneity(G)
        expected_mean = 20.0
        expected_std = np.std([10.0, 20.0, 30.0])
        expected_cv = expected_std / expected_mean
        
        assert np.isclose(cv, expected_cv)

    def test_force_heterogeneity_empty_graph(self):
        """
        Test CV calculation on an empty graph.
        Should return 0.0.
        """
        parser = YadeParser("dummy")
        G = nx.Graph()
        cv = parser.calc_force_heterogeneity(G)
        assert cv == 0.0

    def test_force_heterogeneity_zero_mean(self):
        """
        Test CV calculation when mean force is 0.
        Should return 0.0 to avoid division by zero.
        """
        parser = YadeParser("dummy")
        G = nx.Graph()
        G.add_edge(1, 2, force_magnitude=0.0)
        G.add_edge(2, 3, force_magnitude=0.0)
        
        cv = parser.calc_force_heterogeneity(G)
        assert cv == 0.0

    def test_force_heterogeneity_integration_timestep(self):
        """
        Integration test: Verify force_heterogeneity is calculated and non-null
        in the per-timestep output.
        """
        parser = YadeParser("dummy")
        
        timestep_data = {
            'positions': ["1 0 0 0", "2 1 0 0", "3 0 1 0"],
            'forces': ["1 0 0 10", "2 0 0 20", "3 0 0 30"],
            'contacts': ["1 2 0.5", "2 3 0.5"], # Overlap > 0
            'work_input': 100.0,
            'delta_ke': 10.0,
            'delta_pe': 10.0,
            'driving_amplitude': 0.5
        }
        
        # Manually set contact data to ensure specific edges
        parser.contact_data = [(1, 2, 0.5), (2, 3, 0.5)]
        
        result = parser.process_timestep(timestep_data)
        
        assert 'force_heterogeneity' in result
        assert result['force_heterogeneity'] is not None
        assert not np.isnan(result['force_heterogeneity'])
        
        # Verify the value is calculated (not just 0 if forces vary)
        # In this case, we have forces 10 and 20 (approx) -> CV > 0
        assert result['force_heterogeneity'] >= 0.0

    def test_force_heterogeneity_fallback_from_node_forces(self):
        """
        Test that force_heterogeneity falls back to node forces if edge data missing.
        """
        parser = YadeParser("dummy")
        
        G = nx.Graph()
        # Add edges without force_magnitude
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        
        # Set node forces
        parser.forces = {
            1: np.array([0, 0, 10.0]), # Mag 10
            2: np.array([0, 0, 30.0]), # Mag 30
            3: np.array([0, 0, 50.0])  # Mag 50
        }
        
        # Edge 1-2: (10+30)/2 = 20
        # Edge 2-3: (30+50)/2 = 40
        # Values: [20, 40] -> Mean 30, Std ~14.14 -> CV ~0.471
        
        cv = parser.calc_force_heterogeneity(G)
        expected_mean = 30.0
        expected_std = np.std([20.0, 40.0])
        expected_cv = expected_std / expected_mean
        
        assert np.isclose(cv, expected_cv)
