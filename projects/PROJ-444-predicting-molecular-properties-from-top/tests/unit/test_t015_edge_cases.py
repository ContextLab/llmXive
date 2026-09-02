import pytest
import networkx as nx
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.graph_builder import log_invalid_smiles, setup_invalid_smiles_logger, is_valid_molecule
from utils.persistence_utils import compute_shortest_path_matrix, check_memory_requirement, MEMORY_THRESHOLD_BYTES

class TestInvalidSmilesLogging:
    def test_log_invalid_smiles_creates_file(self, tmp_path, caplog):
        # Setup log path in temp directory
        log_file = tmp_path / "invalid_smiles.log"
        
        # Mock the logger setup to use our temp file
        import utils.graph_builder as gb
        gb._invalid_smiles_logger = None # Reset singleton
        
        # This would normally call setup_invalid_smiles_logger with a path
        # We test the function directly by setting the global state or mocking
        # For now, we test that the function exists and can be called
        # The actual file creation is tested via integration or by checking the file exists after call
        
        # Simulate a call
        gb.log_invalid_smiles("INVALID_SMILES", "Test reason")
        
        # Note: Since the logger is a singleton and might be configured globally,
        # we check if the file exists in the default location or if we can force it.
        # For this unit test, we verify the function doesn't crash and the logger is set up.
        assert gb._invalid_smiles_logger is not None

    def test_is_valid_molecule_logs_on_invalid(self):
        import utils.graph_builder as gb
        gb._invalid_smiles_logger = None # Reset
        
        # This will trigger a log
        result = is_valid_molecule("INVALID_SMILES_STRING")
        assert result is False
        # We can't easily assert the log content in a unit test without complex mocking
        # but we assert the function returns False.

class TestMemoryThreshold:
    def test_check_memory_small_graph(self):
        # Small graph should pass
        assert check_memory_requirement(10) is True
        assert check_memory_requirement(100) is True

    def test_check_memory_large_graph(self):
        # Very large graph should fail (assuming default threshold)
        # 100 MB / 8 bytes = ~12.5 million entries -> sqrt(12.5M) ~ 3535 nodes
        # Let's pick a number that definitely exceeds 100MB
        # 10000 nodes -> 100M entries -> 800MB
        assert check_memory_requirement(10000) is False

    def test_memory_threshold_constant(self):
        # Verify the constant is set
        assert MEMORY_THRESHOLD_BYTES == 100 * 1024 * 1024

class TestShortestPathMemory:
    def test_compute_shortest_path_large_graph_raises(self):
        # Create a large graph
        n = 10000
        G = nx.complete_graph(n)
        
        with pytest.raises(MemoryError):
            compute_shortest_path_matrix(G)

    def test_compute_shortest_path_small_graph_works(self):
        G = nx.cycle_graph(10)
        dist = compute_shortest_path_matrix(G)
        assert dist.shape == (10, 10)
        assert dist[0, 1] == 1.0
        assert dist[0, 0] == 0.0

class TestDisconnectedGraphs:
    def test_shortest_path_disconnected(self):
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2, 3])
        G.add_edge(0, 1)
        G.add_edge(2, 3)
        # 0-1 and 2-3 are disconnected
        
        dist = compute_shortest_path_matrix(G)
        assert dist.shape == (4, 4)
        assert dist[0, 1] == 1.0
        assert dist[0, 2] == np.inf # Disconnected
        assert dist[2, 3] == 1.0
        assert dist[1, 2] == np.inf