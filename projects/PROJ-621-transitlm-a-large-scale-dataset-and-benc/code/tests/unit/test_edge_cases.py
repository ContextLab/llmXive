import pytest
from pathlib import Path
from typing import List, Dict, Any
from src.contracts.models import GTFSGraph, StationNode, TransferEdge, TransitLine
from src.models.validation import validate_route_sequence, check_connectivity

class TestInfiniteLoopDetection:
    """Tests for T030a: Infinite loop detection in route sequences."""

    def test_infinite_loop_detection(self):
        """Input sequence ["A", "B", "A", "B"]; Assert valid=False"""
        # Create a simple graph where A-B exists
        nodes = [
            StationNode(id="A", name="Station A"),
            StationNode(id="B", name="Station B"),
        ]
        edges = [
            TransferEdge(from_node="A", to_node="B", line="X"),
            TransferEdge(from_node="B", to_node="A", line="X"), # Bidirectional for the loop
        ]
        lines = [TransitLine(id="X", name="Line X")]

        graph = GTFSGraph(nodes=nodes, edges=edges, lines=lines)
        
        # Sequence that loops infinitely
        sequence = ["A", "B", "A", "B"]
        
        result = validate_route_sequence(graph, sequence)
        
        assert result.valid is False
        assert "infinite loop" in result.reason.lower() or "cycle" in result.reason.lower()

class TestHallucinatedStation:
    """Tests for T030b: Hallucinated station detection."""

    def test_hallucinated_station(self):
        """Input sequence ["A", "FakeStation", "B"]; Assert valid=False"""
        # Create a graph with A and B, but NO FakeStation
        nodes = [
            StationNode(id="A", name="Station A"),
            StationNode(id="B", name="Station B"),
        ]
        edges = [
            TransferEdge(from_node="A", to_node="B", line="X"),
        ]
        lines = [TransitLine(id="X", name="Line X")]

        graph = GTFSGraph(nodes=nodes, edges=edges, lines=lines)
        
        # Sequence with a non-existent station
        sequence = ["A", "FakeStation", "B"]
        
        result = validate_route_sequence(graph, sequence)
        
        assert result.valid is False
        assert "hallucinated" in result.reason.lower() or "not found" in result.reason.lower() or "unknown" in result.reason.lower()

class TestDisconnectedPairs:
    """Tests for T030c: Disconnected O-D pairs."""

    def test_disconnected_pairs(self):
        """Input O-D pair with no path; Assert validity_score=0"""
        # Create a graph with two disconnected components
        # Component 1: A-B
        # Component 2: C-D
        nodes = [
            StationNode(id="A", name="Station A"),
            StationNode(id="B", name="Station B"),
            StationNode(id="C", name="Station C"),
            StationNode(id="D", name="Station D"),
        ]
        edges = [
            TransferEdge(from_node="A", to_node="B", line="X"),
            TransferEdge(from_node="C", to_node="D", line="Y"),
        ]
        lines = [
            TransitLine(id="X", name="Line X"),
            TransitLine(id="Y", name="Line Y"),
        ]

        graph = GTFSGraph(nodes=nodes, edges=edges, lines=lines)
        
        # Attempt to validate a route from A to C (no path exists)
        # We construct a sequence that tries to go A -> C directly or via non-existent links
        # Since there is no path, any sequence attempting this should fail connectivity
        sequence = ["A", "C"] 
        
        result = validate_route_sequence(graph, sequence)
        
        assert result.valid is False
        assert result.score == 0.0
        assert "disconnected" in result.reason.lower() or "no path" in result.reason.lower() or "unreachable" in result.reason.lower()

    def test_disconnected_pairs_trivial(self):
        """Test that a single node sequence in a disconnected graph is valid if start==end, 
           but an O-D pair with no path fails."""
        
        nodes = [
            StationNode(id="A", name="Station A"),
            StationNode(id="B", name="Station B"),
        ]
        # No edges between A and B
        edges = []
        lines = [TransitLine(id="X", name="Line X")]

        graph = GTFSGraph(nodes=nodes, edges=edges, lines=lines)
        
        # Try to go from A to B with no edges
        sequence = ["A", "B"]
        
        result = validate_route_sequence(graph, sequence)
        
        assert result.valid is False
        assert result.score == 0.0