import pytest
import networkx as nx
from unittest.mock import MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from extract import YadeParser

class TestT016bMissingContacts:
    """Tests for T016b: Handling missing contacts (topological disconnect)."""

    def test_excludes_timestep_when_missing_gt_50_percent(self):
        """Verify timestep is excluded if >50% of expected contacts are missing."""
        parser = YadeParser("dummy_file.txt")
        parser._expected_contact_count = 100
        
        # Create a graph with only 40 edges (60% missing)
        G = nx.Graph()
        G.add_edges_from([(i, i+1) for i in range(40)])
        
        # Mock build_contact_network to return our specific graph
        original_build = parser.build_contact_network
        parser.build_contact_network = lambda: G

        # Mock other dependencies to return 0
        parser.calc_coordination_clustering = lambda g: (0.0, 0.0)
        parser.calc_dissipation = lambda w, ke, pe: 0.0
        parser.normalize_dissipation = lambda d, w: 0.0

        timestep_data = {"timestep": 1}
        
        # This should return None because missing_ratio = 0.6 > 0.5
        result = parser.process_timestep(timestep_data)
        
        assert result is None, "Timestep should be excluded when >50% contacts missing"

    def test_sets_clustering_to_zero_when_missing_lt_50_percent(self):
        """Verify clustering is set to 0.0 if <50% contacts missing and flagged."""
        parser = YadeParser("dummy_file.txt")
        parser._expected_contact_count = 100
        
        # Create a graph with 60 edges (40% missing)
        G = nx.Graph()
        G.add_edges_from([(i, i+1) for i in range(60)])
        
        # Mock build_contact_network
        parser.build_contact_network = lambda: G
        
        # Mock calc_coordination_clustering to return normal values (which should be overridden)
        def mock_calc(G):
            return 5.0, 0.8 # Normal values
        parser.calc_coordination_clustering = mock_calc

        timestep_data = {"timestep": 2}
        
        result = parser.process_timestep(timestep_data)
        
        assert result is not None, "Timestep should be included when <50% missing"
        assert result["clustering_coefficient"] == 0.0, "Clustering should be forced to 0.0"
        assert result["data_quality_flag"] == "DISCONNECTED", "Should be flagged as DISCONNECTED"
        assert result["missing_contacts_ratio"] == 0.4, "Missing ratio should be recorded"

    def test_normal_processing_when_no_missing_contacts(self):
        """Verify normal processing when no contacts are missing."""
        parser = YadeParser("dummy_file.txt")
        parser._expected_contact_count = 100
        
        # Create a graph with 100 edges (0% missing)
        G = nx.Graph()
        G.add_edges_from([(i, i+1) for i in range(100)])
        
        parser.build_contact_network = lambda: G
        
        def mock_calc(G):
            return 5.0, 0.9
        parser.calc_coordination_clustering = mock_calc

        timestep_data = {"timestep": 3}
        
        result = parser.process_timestep(timestep_data)
        
        assert result is not None
        assert result["data_quality_flag"] == "OK"
        # Clustering should be the calculated value, not forced to 0
        assert result["clustering_coefficient"] == 0.9