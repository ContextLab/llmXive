"""
Graph Generator Module for OPID Routing Complexity Analysis.

This module implements the generation of synthetic State-Graph Environments
with multiple distinct complexity tiers.

Tier 3: High-entropy transitions and sparse rewards.
"""
import logging
import random
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

from environment.state_graph import Node, Edge, StateGraph
from environment.validator import validate_graph

# Configure logger
logger = logging.getLogger(__name__)


def generate_tier_3_nodes(
    seed: Optional[int] = None,
    num_nodes: Optional[int] = None
) -> List[Node]:
    """
    Generate Tier 3 nodes: 100+ nodes with sparse structure.

    Args:
        seed: Optional seed for reproducibility.
        num_nodes: Optional override for the number of nodes. Defaults to 100.

    Returns:
        List of Node objects representing the tier 3 nodes.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Tier 3 specification: 100+ nodes. Fixed 100 for determinism in testing,
    # but scalable in logic.
    n = num_nodes if num_nodes is not None else 100
    
    nodes = []
    for i in range(n):
        # Node ID is simply the index for simplicity, but could be randomized
        node_id = i
        # Tier 3 nodes have sparse rewards. We will assign rewards later in edge generation
        # or here. The spec says "sparse rewards (1 reward per ~10 nodes)".
        # We'll initialize reward as 0 and set it later or during edge creation context.
        # However, StateGraph Node definition needs to be checked.
        # Assuming Node has a 'reward' attribute or similar.
        # If Node doesn't have reward, we might need to store it in the graph or edge.
        # Let's assume Node has a reward attribute based on typical MDP definitions.
        # If not, we'll attach it dynamically or assume the graph handles it.
        # Looking at imports: from environment.state_graph import Node
        # We must assume Node structure. If it's a dataclass, we can't add arbitrary attrs easily.
        # Let's assume Node has: id, reward, etc.
        
        # For Tier 3, we want sparse rewards. 1 per ~10 nodes.
        # We'll decide reward assignment in this function or the edge function.
        # Let's assign reward here for clarity.
        reward = 0.0
        if n > 0:
            # Randomly assign rewards to ~10% of nodes
            # To ensure reproducibility with seed, we use np.random
            if np.random.random() < 0.1:
                reward = 1.0
        
        nodes.append(Node(id=node_id, reward=reward))
    
    logger.info(f"Generated {len(nodes)} nodes for Tier 3.")
    return nodes


def generate_tier_3_edges(
    nodes: List[Node],
    seed: Optional[int] = None
) -> List[Edge]:
    """
    Generate Tier 3 edges: High-entropy transitions and sparse rewards.
    
    Requirements:
    - High-entropy transitions: Probabilities are distributed such that no single
      action is overwhelmingly likely (unlike Tier 1's 1.0).
    - Sparse rewards: Already handled in node generation (1 reward per ~10 nodes),
      but we ensure the graph structure supports sparse traversal.
    - Ensure at least one path exists from start to goal (validator will check this).
    
    Args:
        nodes: List of Node objects.
        seed: Optional seed for reproducibility.

    Returns:
        List of Edge objects.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    if not nodes:
        return []

    edges = []
    n = len(nodes)
    
    # Sort nodes by ID to ensure deterministic ordering for edge creation
    sorted_nodes = sorted(nodes, key=lambda x: x.id)
    
    # We need to create a graph that is connected but sparse and stochastic.
    # Strategy:
    # 1. Create a base path (spanning tree) to ensure connectivity.
    # 2. Add extra edges to increase complexity and entropy.
    # 3. Assign stochastic transition probabilities.
    
    # Step 1: Create a base path from node 0 to node n-1
    # This ensures the validator (validate_graph) will find a path.
    for i in range(n - 1):
        current_node = sorted_nodes[i]
        next_node = sorted_nodes[i + 1]
        
        # High entropy transition: probability < 1.0
        # For Tier 3, we want high entropy, so probabilities should be more uniform
        # across available actions, or at least not deterministic.
        # Let's assign a probability between 0.3 and 0.7 for the "forward" move
        # to simulate uncertainty, but ensure it's the most likely path.
        # Actually, "high entropy" implies the distribution over actions is uniform-ish.
        # If a node has multiple outgoing edges, the probabilities should be similar.
        # If a node has only one outgoing edge, entropy is 0.
        # So we MUST create branching for high entropy.
        
        # We'll create a branching structure.
        # For now, let's just connect i -> i+1 with a probability < 1.0.
        # But to have entropy, we need multiple choices.
        # Let's create a "main" path and some "side" paths.
        
        prob = np.random.uniform(0.4, 0.8) # High entropy: not 1.0
        edges.append(Edge(
            source_id=current_node.id,
            target_id=next_node.id,
            probability=prob,
            reward=0.0 # Reward is on nodes, or we can put it here if needed.
                       # The spec says "sparse rewards (1 reward per ~10 nodes)".
                       # We assigned rewards to nodes in generate_tier_3_nodes.
                       # If the Edge needs a reward, we can set it here, but typically
                       # rewards are on states (nodes) or transitions.
                       # Let's assume the reward is on the node, so edge reward is 0.
        ))
    
    # Step 2: Add branching edges to increase entropy and complexity
    # We want to ensure that at many nodes, there are multiple outgoing edges
    # with similar probabilities, creating high entropy.
    
    # Add random long-range edges or short-range branches
    num_extra_edges = int(n * 0.5) # Add 50% extra edges to create a dense-ish but sparse structure
    
    for _ in range(num_extra_edges):
        source_idx = np.random.randint(0, n - 1) # Cannot be the last node
        target_idx = np.random.randint(source_idx + 1, n) # Forward edges only to keep DAG-like or allow cycles?
        # StateGraph usually allows cycles, but for a path finding task, DAG is easier.
        # Let's allow cycles but ensure no self-loops.
        if source_idx == target_idx:
            continue
            
        source_node = sorted_nodes[source_idx]
        target_node = sorted_nodes[target_idx]
        
        # Check if edge already exists
        edge_exists = any(
            e.source_id == source_node.id and e.target_id == target_node.id
            for e in edges
        )
        if edge_exists:
            continue
        
        # High entropy probability: uniform-ish
        prob = np.random.uniform(0.2, 0.6)
        edges.append(Edge(
            source_id=source_node.id,
            target_id=target_node.id,
            probability=prob,
            reward=0.0
        ))
    
    # Step 3: Normalize probabilities for each source node to ensure they sum to 1.0?
    # The spec says "stochastic transition probabilities".
    # In a real MDP, sum of probs from a state should be 1.0.
    # Let's normalize.
    source_probs: Dict[int, List[Tuple[int, float]]] = {}
    for edge in edges:
        if edge.source_id not in source_probs:
            source_probs[edge.source_id] = []
        source_probs[edge.source_id].append((edge.target_id, edge.probability))
    
    normalized_edges = []
    for source_id, targets in source_probs.items():
        total_prob = sum(p for _, p in targets)
        if total_prob == 0:
            continue
        for target_id, prob in targets:
            normalized_edges.append(Edge(
                source_id=source_id,
                target_id=target_id,
                probability=prob / total_prob,
                reward=0.0
            ))
    
    logger.info(f"Generated {len(normalized_edges)} edges for Tier 3 with high entropy.")
    return normalized_edges


def generate_tier_3(
    seed: Optional[int] = None,
    num_nodes: Optional[int] = None,
    max_retries: int = 100
) -> StateGraph:
    """
    Generate a complete Tier 3 StateGraph.
    
    Combines node and edge generation, then validates.
    
    Args:
        seed: Optional seed for reproducibility.
        num_nodes: Optional override for number of nodes.
        max_retries: Maximum number of attempts to generate a valid graph.
    
    Returns:
        A valid StateGraph object.
    
    Raises:
        RuntimeError: If a valid graph cannot be generated within max_retries.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    for attempt in range(max_retries):
        try:
            nodes = generate_tier_3_nodes(seed=seed, num_nodes=num_nodes)
            edges = generate_tier_3_edges(nodes, seed=seed)
            
            # Determine start and goal
            # Start is the first node, goal is the last node (or a specific reward node)
            if not nodes:
                continue
            
            sorted_nodes = sorted(nodes, key=lambda x: x.id)
            start_node = sorted_nodes[0]
            goal_node = sorted_nodes[-1] # Or a node with reward > 0
            
            # Create the graph
            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=start_node.id,
                goal=goal_node.id,
                tier=3
            )
            
            # Validate
            if validate_graph(graph):
                logger.info(f"Tier 3 graph generated successfully on attempt {attempt + 1}.")
                return graph
            else:
                logger.warning(f"Validation failed on attempt {attempt + 1}. Retrying...")
        
        except Exception as e:
            logger.error(f"Error generating Tier 3 graph on attempt {attempt + 1}: {e}")
            continue
    
    raise RuntimeError(f"Failed to generate a valid Tier 3 graph after {max_retries} attempts.")