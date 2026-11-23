"""
Unit tests for generator_metrics.py.
"""
import pytest
from src.stats.generator_metrics import (
    calculate_generator_error_rate,
    evaluate_generator_against_prompt,
    aggregate_generator_metrics,
    GeneratorMetrics
)
from src.data_models import SceneGraph, ObjectNode, RelationshipEdge
from src.stats.simulator_metrics import calculate_graph_edit_distance


def create_test_graph(objects: list, relationships: list) -> SceneGraph:
    """Helper to create a SceneGraph for testing."""
    return SceneGraph(
        objects=objects,
        relationships=relationships
    )


def test_calculate_generator_error_rate_perfect_match():
    """Test that identical graphs yield 0.0 error rate."""
    obj = ObjectNode(id="1", label="cat", attributes=["black"])
    rel = RelationshipEdge(id="r1", source="1", target="2", label="on")
    obj2 = ObjectNode(id="2", label="mat", attributes=["red"])
    
    graph = create_test_graph([obj, obj2], [rel])
    
    error = calculate_generator_error_rate(graph, graph)
    assert error == 0.0


def test_calculate_generator_error_rate_complete_mismatch():
    """Test that completely different graphs yield high error rate."""
    # Intended: Cat on Mat
    intended_obj1 = ObjectNode(id="1", label="cat", attributes=[])
    intended_obj2 = ObjectNode(id="2", label="mat", attributes=[])
    intended_rel = RelationshipEdge(id="r1", source="1", target="2", label="on")
    intended = create_test_graph([intended_obj1, intended_obj2], [intended_rel])
    
    # Generated: Dog on Bone
    gen_obj1 = ObjectNode(id="1", label="dog", attributes=[])
    gen_obj2 = ObjectNode(id="2", label="bone", attributes=[])
    gen_rel = RelationshipEdge(id="r1", source="1", target="2", label="on") # Same relation, different objects
    generated = create_test_graph([gen_obj1, gen_obj2], [gen_rel])
    
    # Edit distance should be non-zero. 
    # Nodes: 2 vs 2. Edges: 1 vs 1.
    # If labels differ, distance > 0.
    error = calculate_generator_error_rate(generated, intended)
    assert error > 0.0
    assert error <= 1.0


def test_calculate_generator_error_rate_missing_objects():
    """Test error rate when objects are missing in generated graph."""
    # Intended: 2 objects
    intended = create_test_graph(
        [ObjectNode(id="1", label="A"), ObjectNode(id="2", label="B")],
        []
    )
    
    # Generated: 1 object
    generated = create_test_graph(
        [ObjectNode(id="1", label="A")],
        []
    )
    
    error = calculate_generator_error_rate(generated, intended)
    # Distance is 1 (missing node). Total intended elements = 2.
    # Error = 1/2 = 0.5
    assert error == 0.5


def test_aggregate_generator_metrics():
    """Test aggregation logic."""
    # Sample 1: Perfect (Error 0)
    g1 = create_test_graph([ObjectNode(id="1", label="A")], [])
    i1 = create_test_graph([ObjectNode(id="1", label="A")], [])
    
    # Sample 2: Error (Error 0.5)
    g2 = create_test_graph([ObjectNode(id="1", label="A")], [])
    i2 = create_test_graph([ObjectNode(id="1", label="A"), ObjectNode(id="2", label="B")], [])
    
    samples = [(g1, i1), (g2, i2)]
    
    metrics = aggregate_generator_metrics(samples)
    
    assert metrics.total_samples == 2
    assert metrics.failed_samples == 1 # Only sample 1 had 0 error
    assert metrics.generator_error_rate == 0.25 # (0 + 0.5) / 2
    assert metrics.avg_edit_distance == 0.25


def test_empty_intended_graph():
    """Test handling of empty intended graph."""
    intended = create_test_graph([], [])
    generated = create_test_graph([], [])
    
    error = calculate_generator_error_rate(generated, intended)
    assert error == 0.0
    
    generated_non_empty = create_test_graph([ObjectNode(id="1", label="A")], [])
    error_non_empty = calculate_generator_error_rate(generated_non_empty, intended)
    assert error_non_empty == 1.0


def test_generator_metrics_dataclass():
    """Test the GeneratorMetrics dataclass methods."""
    metrics = GeneratorMetrics()
    metrics.add_sample(0.1, is_success=False)
    metrics.add_sample(0.0, is_success=True)
    metrics.add_sample(0.3, is_success=False)
    
    metrics.finalize()
    
    assert metrics.total_samples == 3
    assert metrics.failed_samples == 2
    assert abs(metrics.avg_edit_distance - 0.13333333) < 0.0001
    assert abs(metrics.generator_error_rate - 0.13333333) < 0.0001