import pytest
import numpy as np
from typing import List
from analysis.dynamics import calculate_flexibility, detect_communities
from errors import DataMissingCreativityError

class TestCalculateFlexibility:
    def test_flexibility_zero_changes(self):
        """Test flexibility when community labels never change."""
        # Two time windows, same communities for all ROIs
        community_labels: List[List[int]] = [
            [0, 0, 1, 1],  # Window 1
            [0, 0, 1, 1]   # Window 2
        ]
        result = calculate_flexibility(community_labels)
        assert result == 0.0, "Flexibility should be 0 when no changes occur"

    def test_flexibility_max_changes(self):
        """Test flexibility when every ROI changes community every window."""
        # 3 windows, 2 ROIs, completely different labels each time
        community_labels: List[List[int]] = [
            [0, 1],  # Window 1
            [1, 0],  # Window 2
            [0, 1]   # Window 3
        ]
        # ROI 0: 0->1 (change), 1->0 (change) = 2 changes
        # ROI 1: 1->0 (change), 0->1 (change) = 2 changes
        # Total changes = 4, total possible transitions = 2 ROIs * 2 transitions = 4
        # Flexibility = 4/4 = 1.0
        result = calculate_flexibility(community_labels)
        assert result == 1.0, "Flexibility should be 1.0 when all ROIs change every window"

    def test_flexibility_partial_changes(self):
        """Test flexibility with mixed change patterns."""
        # 3 windows, 2 ROIs
        # ROI 0: 0 -> 0 -> 1 (1 change)
        # ROI 1: 1 -> 1 -> 1 (0 changes)
        community_labels: List[List[int]] = [
            [0, 1],
            [0, 1],
            [1, 1]
        ]
        # Total changes = 1, total transitions = 2 * 2 = 4
        # Flexibility = 1/4 = 0.25
        result = calculate_flexibility(community_labels)
        assert result == 0.25, f"Expected 0.25, got {result}"

    def test_flexibility_single_window(self):
        """Test flexibility with only one window (no transitions possible)."""
        community_labels: List[List[int]] = [
            [0, 1, 2]
        ]
        result = calculate_flexibility(community_labels)
        assert result == 0.0, "Flexibility should be 0 with only one window"

    def test_flexibility_empty_input(self):
        """Test flexibility with empty community labels."""
        community_labels: List[List[int]] = []
        result = calculate_flexibility(community_labels)
        assert result == 0.0, "Flexibility should be 0 for empty input"

class TestDetectCommunities:
    def test_detect_communities_simple(self):
        """Test community detection on a simple graph."""
        # Create a simple graph with 2 clear communities
        # Nodes 0,1 connected; Nodes 2,3 connected; No connection between groups
        import networkx as nx
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        
        labels = detect_communities(G, gamma=1.0)
        
        # Check that we got labels for all nodes
        assert len(labels) == 4
        # Check that nodes 0,1 share a community and nodes 2,3 share a different one
        # (order might vary, so check equality within groups)
        assert labels[0] == labels[1], "Nodes 0 and 1 should be in same community"
        assert labels[2] == labels[3], "Nodes 2 and 3 should be in same community"
        assert labels[0] != labels[2], "Nodes 0 and 2 should be in different communities"

    def test_detect_communities_gamma_effect(self):
        """Test that gamma parameter affects resolution."""
        import networkx as nx
        # Create a graph where higher gamma should split communities more
        G = nx.Graph()
        # Add edges to create a structure sensitive to gamma
        G.add_edges_from([
            (0, 1), (1, 2), (2, 0),  # Triangle 1
            (3, 4), (4, 5), (5, 3),  # Triangle 2
            (2, 3)                    # Connection between triangles
        ])
        
        labels_low = detect_communities(G, gamma=0.5)
        labels_high = detect_communities(G, gamma=2.0)
        
        # Higher gamma should result in more communities (or same, never fewer)
        num_communities_low = len(set(labels_low))
        num_communities_high = len(set(labels_high))
        
        assert num_communities_high >= num_communities_low, \
            "Higher gamma should not reduce number of communities"

    def test_detect_communities_single_node(self):
        """Test community detection on a graph with a single node."""
        import networkx as nx
        G = nx.Graph()
        G.add_node(0)
        
        labels = detect_communities(G, gamma=1.0)
        assert len(labels) == 1
        assert labels[0] == 0  # Single node should be in its own community
