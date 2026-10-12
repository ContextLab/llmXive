"""
Contract test for handling of disconnected graphs in the Kuramoto simulation.

The simulation pipeline must recognize that a graph with multiple disconnected
components cannot achieve global synchronization. In this case the returned
``SimulationResult`` should have ``coupling_strength_threshold`` set to ``None``
(or ``null`` in JSON) and its ``status`` should indicate ``disconnected``.

This test is expected to **fail** until the implementation in ``src/simulation.py``
correctly handles the disconnected case.
"""

import networkx as nx
import pytest

# Import the processing function and the status enum from the project modules.
from src.simulation import process_single_network
from src.data_models import SynchronizationStatus, SimulationResult

def test_disconnected_graph_handling():
    """
    Create a simple disconnected graph and verify that the simulation result
    reflects the disconnected status.

    Expected:
      - ``coupling_strength_threshold`` is ``None`` (null in JSON).
      - ``status`` equals ``SynchronizationStatus.DISCONNECTED``.
    """
    # Construct a graph with two separate components.
    G = nx.Graph()
    # Component 1: a single edge between nodes 0 and 1.
    G.add_edge(0, 1)
    # Component 2: isolated node 2 (no edges), making the graph disconnected.
    G.add_node(2)

    # Process the network; the identifier can be any string.
    result = process_single_network(G, network_id="test_disconnected")

    # The result should be an instance of SimulationResult.
    assert isinstance(result, SimulationResult)

    # The coupling strength threshold must be None (null) for disconnected graphs.
    assert result.coupling_strength_threshold is None, (
        "Expected coupling_strength_threshold to be None for a disconnected graph"
    )

    # The status field must indicate the graph is disconnected.
    # The enum value is expected to be SynchronizationStatus.DISCONNECTED.
    assert (
        result.status == SynchronizationStatus.DISCONNECTED
    ), f"Expected status {SynchronizationStatus.DISCONNECTED}, got {result.status}"
    
    # Additional sanity check: the result should not contain a valid threshold value.
    assert result.coupling_strength_threshold is None
    
    # The test deliberately fails if the implementation does not set the correct
    # fields for a disconnected graph. Once the implementation is complete,
    # this test should pass.