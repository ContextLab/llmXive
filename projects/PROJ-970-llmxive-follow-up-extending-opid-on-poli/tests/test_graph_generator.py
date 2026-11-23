import pytest
from env.graph_generator import GraphGenerator, GraphGenerationConfig

def test_tier1_generation():
    config = GraphGenerationConfig(tier=1, seed=42)
    generator = GraphGenerator(config)
    graph = generator.generate()
    
    assert len(graph.nodes) >= 5
    assert len(graph.nodes) <= 10
    assert graph.start_node is not None
    assert graph.goal_node is not None

def test_tier2_generation():
    config = GraphGenerationConfig(tier=2, seed=42)
    generator = GraphGenerator(config)
    graph = generator.generate()
    
    assert len(graph.nodes) >= 15
    assert len(graph.nodes) <= 30
    assert len(graph.edges) > 0

def test_tier3_generation():
    config = GraphGenerationConfig(tier=3, seed=42)
    generator = GraphGenerator(config)
    graph = generator.generate()
    
    assert len(graph.nodes) >= 40
    assert len(graph.nodes) <= 60
    assert len(graph.edges) > 0
