import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Any

from src.analysis.generate_validation_scores import generate_validation_scores
from src.lib.splitter import save_sequences
from src.contracts.models import GTFSGraph, StationNode, TransitLine

@pytest.fixture
def sample_graph():
    """Create a simple linear graph: A -> B -> C"""
    nodes = [
        StationNode(id="A", name="Station A", lines=["1"]),
        StationNode(id="B", name="Station B", lines=["1", "2"]),
        StationNode(id="C", name="Station C", lines=["2"])
    ]
    lines = [
        TransitLine(id="1", name="Line 1", stations=["A", "B"]),
        TransitLine(id="2", name="Line 2", stations=["B", "C"])
    ]
    graph = GTFSGraph(nodes=nodes, lines=lines)
    return graph

@pytest.fixture
def sample_od_pairs():
    """Create sample O-D pairs"""
    return [
        {"id": "od_1", "origin": "A", "destination": "C"},
        {"id": "od_2", "origin": "A", "destination": "B"},
        {"id": "od_3", "origin": "B", "destination": "C"}
    ]

@pytest.fixture
def sample_model_outputs():
    """Create sample model outputs"""
    return {
        "od_1": "Take Line 1 from Station A to Station B, then Line 2 to Station C.",
        "od_2": "Take Line 1 from Station A to Station B.",
        "od_3": "Take Line 2 from Station B to Station C."
    }

def test_generate_validation_scores_creates_file(
    sample_graph, sample_od_pairs, sample_model_outputs, tmp_path: Path
):
    """Test that the function creates the output file."""
    # Save inputs
    graph_file = tmp_path / "graph.json"
    od_file = tmp_path / "od_pairs.json"
    outputs_file = tmp_path / "outputs.json"
    result_file = tmp_path / "results.json"

    # Use the contract's model_to_json to save graph
    from src.contracts.models import model_to_json
    with open(graph_file, 'w') as f:
        json.dump(model_to_json(sample_graph), f)

    with open(od_file, 'w') as f:
        json.dump(sample_od_pairs, f)

    with open(outputs_file, 'w') as f:
        json.dump(sample_model_outputs, f)

    # Run generation
    result = generate_validation_scores(
        od_pairs_path=od_file,
        graph_path=graph_file,
        output_path=result_file,
        model_output_path=outputs_file
    )

    # Verify output file exists
    assert result_file.exists()

    # Verify result structure
    assert "summary" in result
    assert "results" in result
    assert result["summary"]["total_samples"] == 3

def test_validation_scores_contain_expected_fields(
    sample_graph, sample_od_pairs, sample_model_outputs, tmp_path: Path
):
    """Test that validation results contain all expected fields."""
    graph_file = tmp_path / "graph.json"
    od_file = tmp_path / "od_pairs.json"
    outputs_file = tmp_path / "outputs.json"
    result_file = tmp_path / "results.json"

    from src.contracts.models import model_to_json
    with open(graph_file, 'w') as f:
        json.dump(model_to_json(sample_graph), f)

    with open(od_file, 'w') as f:
        json.dump(sample_od_pairs, f)

    with open(outputs_file, 'w') as f:
        json.dump(sample_model_outputs, f)

    generate_validation_scores(
        od_pairs_path=od_file,
        graph_path=graph_file,
        output_path=result_file,
        model_output_path=outputs_file
    )

    with open(result_file, 'r') as f:
        data = json.load(f)

    # Check structure of a single result
    first_result = next(iter(data["results"].values()))
    required_fields = [
        "origin", "destination", "predicted_sequence", "is_valid",
        "exact_match_score", "connectivity_valid", "has_infinite_loop",
        "has_hallucinated_station"
    ]
    for field in required_fields:
        assert field in first_result, f"Missing field: {field}"

def test_invalid_route_marked_as_invalid(
    sample_graph, sample_od_pairs, tmp_path: Path
):
    """Test that a route with hallucinated stations is marked invalid."""
    graph_file = tmp_path / "graph.json"
    od_file = tmp_path / "od_pairs.json"
    outputs_file = tmp_path / "outputs.json"
    result_file = tmp_path / "results.json"

    from src.contracts.models import model_to_json
    with open(graph_file, 'w') as f:
        json.dump(model_to_json(sample_graph), f)

    # Override one output to include a fake station
    bad_outputs = sample_model_outputs.copy()
    bad_outputs["od_1"] = "Take Line 1 from Station A to FakeStation to Station C."

    with open(od_file, 'w') as f:
        json.dump(sample_od_pairs, f)

    with open(outputs_file, 'w') as f:
        json.dump(bad_outputs, f)

    generate_validation_scores(
        od_pairs_path=od_file,
        graph_path=graph_file,
        output_path=result_file,
        model_output_path=outputs_file
    )

    with open(result_file, 'r') as f:
        data = json.load(f)

    # The first result should be invalid due to hallucinated station
    assert data["results"]["od_1"]["has_hallucinated_station"] is True
    assert data["results"]["od_1"]["is_valid"] is False