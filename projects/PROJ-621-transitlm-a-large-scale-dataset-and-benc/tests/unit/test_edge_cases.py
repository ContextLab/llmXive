import pytest
from src.models.validation import check_infinite_loop, check_hallucinated_station
from src.contracts.models import GTFSGraph, StationNode, TransferEdge, TransitLine
from typing import List, Optional, Dict, Any

class TestEdgeCases:
    """Tests for edge cases in route validation."""

    def test_infinite_loop_detection(self):
        """Test that infinite loops in route sequences are detected.
        
        Input sequence: ["A", "B", "A", "B"]
        Expected: valid=False (infinite loop detected)
        """
        sequence = ["A", "B", "A", "B"]
        result = check_infinite_loop(sequence)
        assert result is False, "Infinite loop should be detected in sequence A-B-A-B"

    def test_no_loop_valid_sequence(self):
        """Test that valid sequences without loops pass validation.
        
        Input sequence: ["A", "B", "C", "D"]
        Expected: valid=True (no infinite loop)
        """
        sequence = ["A", "B", "C", "D"]
        result = check_infinite_loop(sequence)
        assert result is True, "Valid sequence without loops should pass"

    def test_single_station(self):
        """Test single station sequence.
        
        Input sequence: ["A"]
        Expected: valid=True (no loop possible)
        """
        sequence = ["A"]
        result = check_infinite_loop(sequence)
        assert result is True, "Single station should not be considered a loop"

    def test_two_stations_no_loop(self):
        """Test two station sequence without loop.
        
        Input sequence: ["A", "B"]
        Expected: valid=True (no loop)
        """
        sequence = ["A", "B"]
        result = check_infinite_loop(sequence)
        assert result is True, "Two distinct stations should not be a loop"

    def test_three_stations_with_loop(self):
        """Test three station sequence with loop.
        
        Input sequence: ["A", "B", "C", "A"]
        Expected: valid=False (loop detected)
        """
        sequence = ["A", "B", "C", "A"]
        result = check_infinite_loop(sequence)
        assert result is False, "Loop A-B-C-A should be detected"

    def test_empty_sequence(self):
        """Test empty sequence.
        
        Input sequence: []
        Expected: valid=True (no loop possible)
        """
        sequence = []
        result = check_infinite_loop(sequence)
        assert result is True, "Empty sequence should not be considered a loop"

    def test_repeated_stations_not_immediately_loop(self):
        """Test that repeated stations that don't form a loop are valid.
        
        Input sequence: ["A", "B", "A", "C"]
        Expected: valid=True (A appears twice but no immediate loop A-B-A-B)
        Note: This test clarifies that we detect immediate loops (A-B-A-B pattern),
        not just any repetition. The sequence A-B-A-C is valid if it represents
        a path that goes A->B->A->C.
        """
        sequence = ["A", "B", "A", "C"]
        result = check_infinite_loop(sequence)
        # A-B-A-C is not an infinite loop (A-B-A-B pattern)
        # It's a valid path that returns to A and continues to C
        assert result is True, "A-B-A-C is not an infinite loop pattern"

    def test_hallucinated_station(self):
        """Test that hallucinated stations (not in graph) are detected.
        
        Input sequence: ["A", "FakeStation", "B"]
        Graph: Contains only stations "A" and "B"
        Expected: valid=False (hallucinated station detected)
        """
        # Create a minimal graph with only stations A and B
        graph = GTFSGraph(
            nodes=[
                StationNode(station_id="A", station_name="Station A"),
                StationNode(station_id="B", station_name="Station B")
            ],
            edges=[
                TransferEdge(from_station="A", to_station="B", transfer_type="direct")
            ],
            lines=[
                TransitLine(line_id="L1", line_name="Line 1")
            ]
        )
        
        sequence = ["A", "FakeStation", "B"]
        result = check_hallucinated_station(sequence, graph)
        assert result is False, "Hallucinated station 'FakeStation' should be detected"

    def test_all_stations_valid(self):
        """Test that a sequence with all valid stations passes.
        
        Input sequence: ["A", "B"]
        Graph: Contains stations "A" and "B"
        Expected: valid=True (all stations exist in graph)
        """
        graph = GTFSGraph(
            nodes=[
                StationNode(station_id="A", station_name="Station A"),
                StationNode(station_id="B", station_name="Station B")
            ],
            edges=[
                TransferEdge(from_station="A", to_station="B", transfer_type="direct")
            ],
            lines=[
                TransitLine(line_id="L1", line_name="Line 1")
            ]
        )
        
        sequence = ["A", "B"]
        result = check_hallucinated_station(sequence, graph)
        assert result is True, "All stations in sequence should be valid"

    def test_multiple_hallucinated_stations(self):
        """Test detection of multiple hallucinated stations.
        
        Input sequence: ["A", "Fake1", "B", "Fake2"]
        Graph: Contains only stations "A" and "B"
        Expected: valid=False (multiple hallucinated stations detected)
        """
        graph = GTFSGraph(
            nodes=[
                StationNode(station_id="A", station_name="Station A"),
                StationNode(station_id="B", station_name="Station B")
            ],
            edges=[
                TransferEdge(from_station="A", to_station="B", transfer_type="direct")
            ],
            lines=[
                TransitLine(line_id="L1", line_name="Line 1")
            ]
        )
        
        sequence = ["A", "Fake1", "B", "Fake2"]
        result = check_hallucinated_station(sequence, graph)
        assert result is False, "Multiple hallucinated stations should be detected"

    def test_empty_sequence_no_hallucination(self):
        """Test that empty sequence has no hallucinated stations.
        
        Input sequence: []
        Expected: valid=True (no stations to validate)
        """
        graph = GTFSGraph(
            nodes=[
                StationNode(station_id="A", station_name="Station A")
            ],
            edges=[],
            lines=[]
        )
        
        sequence = []
        result = check_hallucinated_station(sequence, graph)
        assert result is True, "Empty sequence should not have hallucinated stations"

    def test_single_hallucinated_station(self):
        """Test detection of a single hallucinated station.
        
        Input sequence: ["FakeStation"]
        Graph: Contains only station "A"
        Expected: valid=False (hallucinated station detected)
        """
        graph = GTFSGraph(
            nodes=[
                StationNode(station_id="A", station_name="Station A")
            ],
            edges=[],
            lines=[]
        )
        
        sequence = ["FakeStation"]
        result = check_hallucinated_station(sequence, graph)
        assert result is False, "Single hallucinated station should be detected"