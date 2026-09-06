import pytest
import os
import json
from config import set_seed, get_seed, ensure_directories
from env.graph_generator import GraphGenerator, GraphGenerationConfig
from env.state_graph import StateGraph

@pytest.fixture
def generator():
    set_seed(42)
    ensure_directories()
    return GraphGenerator()

def test_tier3_node_count(generator):
    """Test that Tier 3 generates a sufficient number of nodes."""
    graph = generator.generate_tier_3()
    # Tier 3 should have a "sufficient" number of nodes (e.g., > 50)
    assert len(graph.nodes) >= 50, f"Tier 3 graph has too few nodes: {len(graph.nodes)}"

def test_tier3_sparse_rewards(generator):
    """Test that Tier 3 has sparse reward signals (only goal node has reward)."""
    graph = generator.generate_tier_3()
    
    # Count nodes with reward > 0
    rewarded_nodes = [n for n in graph.nodes.values() if n.reward > 0]
    
    # Should have exactly 1 goal node with reward
    assert len(rewarded_nodes) == 1, f"Expected 1 rewarded node, found {len(rewarded_nodes)}"
    
    # The rewarded node should be the goal
    goal_node = rewarded_nodes[0]
    assert goal_node.is_goal, "The rewarded node should be marked as goal"

def test_tier3_high_entropy_branching(generator):
    """Test that Tier 3 has high-entropy state transitions (multiple branches)."""
    graph = generator.generate_tier_3()
    
    # Check that nodes have multiple outgoing edges (branching)
    branching_count = 0
    for node in graph.nodes.values():
        outgoing = graph.get_outgoing_edges(node.id)
        if len(outgoing) > 1:
            branching_count += 1
    
    # At least 20% of nodes should have branching
    min_branching_nodes = int(len(graph.nodes) * 0.2)
    assert branching_count >= min_branching_nodes, \
        f"Insufficient branching: only {branching_count} nodes have multiple paths"

def test_tier3_goal_reachability(generator):
    """Test that the goal is reachable from the start node in Tier 3."""
    graph = generator.generate_tier_3()
    start_id = 0
    goal_id = next(n.id for n in graph.nodes.values() if n.is_goal)
    
    # Use BFS to check reachability
    visited = set()
    queue = [start_id]
    reachable = False
    
    while queue:
        current = queue.pop(0)
        if current == goal_id:
            reachable = True
            break
        if current in visited:
            continue
        visited.add(current)
        
        for edge in graph.get_outgoing_edges(current):
            if edge.probability > 0:
                queue.append(edge.target_id)
    
    assert reachable, "Goal node is not reachable from start node in Tier 3 graph"

def test_tier3_deterministic_with_seed():
    """Test that Tier 3 generation is deterministic given the same seed."""
    set_seed(12345)
    gen1 = GraphGenerator()
    graph1 = gen1.generate_tier_3()
    
    set_seed(12345)
    gen2 = GraphGenerator()
    graph2 = gen2.generate_tier_3()
    
    # Compare node counts
    assert len(graph1.nodes) == len(graph2.nodes), "Node count differs with same seed"
    
    # Compare edge counts
    assert len(graph1.edges) == len(graph2.edges), "Edge count differs with same seed"
    
    # Compare node IDs
    node_ids_1 = sorted([n.id for n in graph1.nodes.values()])
    node_ids_2 = sorted([n.id for n in graph2.nodes.values()])
    assert node_ids_1 == node_ids_2, "Node IDs differ with same seed"

def test_tier3_output_file_creation():
    """Test that the main function creates the expected output file."""
    # Run the main function which should write to data/processed/tier3_graph.json
    from env.graph_generator import main
    main()
    
    output_path = "data/processed/tier3_graph.json"
    assert os.path.exists(output_path), f"Output file {output_path} was not created"
    
    # Verify it's valid JSON
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "tier" in data, "Missing 'tier' in output JSON"
    assert data["tier"] == 3, "Incorrect tier in output JSON"
    assert "nodes" in data, "Missing 'nodes' in output JSON"
    assert "edges" in data, "Missing 'edges' in output JSON"
    assert len(data["nodes"]) > 0, "No nodes in output JSON"
    assert len(data["edges"]) > 0, "No edges in output JSON"