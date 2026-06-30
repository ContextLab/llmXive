import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.contracts.models import GTFSGraph, StationNode, TransferEdge, TransitLine, RouteSequence, ValidationResult, ValidationStatus
from src.models.validation import validate_route_sequence
from src.lib.config import set_seed, get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_graph() -> GTFSGraph:
    """
    Creates a simple linear graph for testing:
    Station_A --(Line 1)--> Station_B --(Line 1)--> Station_Z
    """
    nodes = [
        StationNode(station_id="Station_A", name="Station A"),
        StationNode(station_id="Station_B", name="Station B"),
        StationNode(station_id="Station_Z", name="Station Z"),
    ]
    
    transfers = [
        TransferEdge(from_station="Station_A", to_station="Station_B", line_id="Line 1", weight=1.0),
        TransferEdge(from_station="Station_B", to_station="Station_Z", line_id="Line 1", weight=1.0),
        # Reverse edges for undirected graph simulation if needed, 
        # but validation usually checks directed paths or undirected. 
        # Assuming directed for strict sequence validation.
        TransferEdge(from_station="Station_B", to_station="Station_A", line_id="Line 1", weight=1.0),
        TransferEdge(from_station="Station_Z", to_station="Station_B", line_id="Line 1", weight=1.0),
    ]

    lines = [
        TransitLine(line_id="Line 1", name="Line 1", color="#000000")
    ]

    return GTFSGraph(
        nodes=nodes,
        edges=transfers,
        lines=lines
    )

@pytest.fixture
def valid_sequence() -> RouteSequence:
    """
    A valid sequence: Station_A -> Station_B -> Station_Z
    """
    return RouteSequence(
        origin="Station_A",
        destination="Station_Z",
        stations=["Station_A", "Station_B", "Station_Z"],
        lines=["Line 1"],
        status=ValidationStatus.PENDING
    )

@pytest.fixture
def invalid_sequence() -> RouteSequence:
    """
    An invalid sequence: Station_A -> Station_Z (direct jump, no edge exists)
    """
    return RouteSequence(
        origin="Station_A",
        destination="Station_Z",
        stations=["Station_A", "Station_Z"],
        lines=[],
        status=ValidationStatus.PENDING
    )

def test_end_to_end_generation(sample_graph: GTFSGraph, valid_sequence: RouteSequence, invalid_sequence: RouteSequence):
    """
    Integration test for end-to-end route generation validation.
    
    Input: O-D pair ("Station_A", "Station_Z") represented by sequences.
    Assert: 
      1. Output format is {"valid": bool, "score": float}
      2. valid_sequence yields validity_score > 0.0 (specifically 1.0 for exact match)
      3. invalid_sequence yields validity_score == 0.0
    """
    set_seed(42)
    
    # Test Valid Sequence
    logger.info("Testing valid sequence: Station_A -> Station_B -> Station_Z")
    result_valid = validate_route_sequence(sample_graph, valid_sequence)
    
    assert isinstance(result_valid, ValidationResult), "Result must be a ValidationResult object"
    
    output_format = {
        "valid": result_valid.status == ValidationStatus.VALID,
        "score": result_valid.exact_match_score if result_valid.exact_match_score is not None else 0.0
    }
    
    assert "valid" in output_format, "Output must contain 'valid' key"
    assert "score" in output_format, "Output must contain 'score' key"
    assert isinstance(output_format["valid"], bool), "'valid' must be a boolean"
    assert isinstance(output_format["score"], float), "'score' must be a float"
    
    # The valid sequence should have a score > 0.0 (ideally 1.0 for exact match)
    assert output_format["score"] > 0.0, f"Valid sequence should have score > 0.0, got {output_format['score']}"
    assert output_format["valid"] is True, f"Valid sequence should be marked as valid, got {output_format['valid']}"
    
    logger.info(f"Valid sequence result: {output_format}")

    # Test Invalid Sequence (Direct jump A->Z with no edge)
    logger.info("Testing invalid sequence: Station_A -> Station_Z (no edge)")
    result_invalid = validate_route_sequence(sample_graph, invalid_sequence)
    
    assert isinstance(result_invalid, ValidationResult), "Result must be a ValidationResult object"
    
    output_format_invalid = {
        "valid": result_invalid.status == ValidationStatus.VALID,
        "score": result_invalid.exact_match_score if result_invalid.exact_match_score is not None else 0.0
    }
    
    # The invalid sequence should have a score of 0.0
    assert output_format_invalid["score"] == 0.0, f"Invalid sequence should have score 0.0, got {output_format_invalid['score']}"
    assert output_format_invalid["valid"] is False, f"Invalid sequence should be marked as invalid, got {output_format_invalid['valid']}"
    
    logger.info(f"Invalid sequence result: {output_format_invalid}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
