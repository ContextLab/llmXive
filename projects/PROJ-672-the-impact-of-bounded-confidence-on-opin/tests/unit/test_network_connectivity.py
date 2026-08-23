import pytest
import networkx as nx
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_networks import ensure_connected, generate_erdos_renyi, generate_watts_strogatz

class TestConnectivityValidation:
    """Tests for T015: Validation and handling of disconnected networks."""

    def test_already_connected_returns_copy(self):
        """If graph is already connected, ensure_connected returns a copy."""
        G = nx.barabasi_albert_graph(100, 3, seed=42)
        assert nx.is_connected(G)
        
        H = ensure_connected(G)
        assert nx.is_connected(H)
        assert G is not H  # Should be a copy
        assert G.number_of_nodes() == H.number_of_nodes()

    def test_disconnected_graph_keeps_largest(self):
        """If graph is disconnected, ensure_connected keeps only the largest component."""
        # Create a disconnected graph: two separate cliques
        G1 = nx.complete_graph(20)
        G2 = nx.complete_graph(10)
        G = nx.disjoint_union(G1, G2)
        
        assert not nx.is_connected(G)
        
        H = ensure_connected(G, strategy="largest")
        
        assert nx.is_connected(H)
        assert H.number_of_nodes() == 20  # Only the larger component
        assert H.number_of_edges() == nx.complete_graph(20).number_of_edges()

    def test_reindexing_preserves_structure(self):
        """Ensure nodes are re-indexed to 0..N-1 after component extraction."""
        G1 = nx.complete_graph(15)
        G2 = nx.complete_graph(5)
        G = nx.disjoint_union(G1, G2)
        
        H = ensure_connected(G, strategy="largest")
        
        nodes = list(H.nodes())
        assert sorted(nodes) == list(range(15))

    def test_watts_strogatz_high_rewiring_disconnects(self):
        """High rewiring probability can disconnect WS graphs; ensure_connected handles it."""
        # High p often leads to disconnection in small k
        G = generate_watts_strogatz(50, 2, 0.9, seed=123)
        
        # Force disconnection if it wasn't already (rare but possible)
        if nx.is_connected(G):
            G.remove_edge(0, 1) 
            if not nx.is_connected(G):
                pass # Good, we have a disconnected graph
            else:
                # If still connected, remove another edge carefully
                for u, v in G.edges():
                    G.remove_edge(u, v)
                    if not nx.is_connected(G):
                        break
        
        if not nx.is_connected(G):
            H = ensure_connected(G, strategy="largest")
            assert nx.is_connected(H)
            assert H.number_of_nodes() < G.number_of_nodes()

    def test_erdos_renyi_low_p_disconnects(self):
        """Low p in ER graphs often leads to disconnection."""
        # Very low p
        G = generate_erdos_renyi(100, 0.001, seed=999)
        
        # Check if disconnected (likely with such low p)
        if not nx.is_connected(G):
            H = ensure_connected(G, strategy="largest")
            assert nx.is_connected(H)
            assert H.number_of_nodes() > 0
        else:
            # If it happened to be connected, the function should just copy it
            H = ensure_connected(G, strategy="largest")
            assert nx.is_connected(H)
    
    def test_bridge_strategy_not_implemented(self):
        """Verify that the bridge strategy raises NotImplementedError."""
        G = nx.disjoint_union(nx.path_graph(5), nx.path_graph(5))
        with pytest.raises(NotImplementedError):
            ensure_connected(G, strategy="bridge")

    def test_empty_graph_raises(self):
        """Ensure empty graph raises ValueError."""
        G = nx.Graph()
        with pytest.raises(ValueError):
            ensure_connected(G)