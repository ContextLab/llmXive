"""
Tier‑specific synthetic graph generators.

The functions generate deterministic or stochastic graphs according to the
tier specifications.  Each generator validates the graph and retries up to
``max_retries`` times before raising ``RuntimeError``.
"""

import json
import logging
import random
import uuid
from typing import List, Optional

import numpy as np

from .state_graph import StateGraph, Node, Edge
from .validator import validate_graph
from ..config import get_tier_config, set_seed

_log = logging.getLogger(__name__)

def _ensure_seed(seed: Optional[int]) -> None:
    """Set seeds for reproducibility if a seed is provided."""
    if seed is not None:
        set_seed(seed)

def _graph_id(tier: int, seed: Optional[int]) -> str:
    """Create a reasonably unique graph identifier."""
    base = f"tier{tier}_{seed}_{uuid.uuid4().hex[:8]}"
    return base

def _save_graph(sg: StateGraph) -> None:
    """Serialize a StateGraph to JSON in the synthetic_graphs folder."""
    from llmxive_toolkit import paths

    out_path = paths.data("raw", "synthetic_graphs", f"{sg.graph_id}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "graph_id": sg.graph_id,
                "tier": sg.tier,
                "nodes": [
                    {
                        "id": node.id,
                        "state_value": node.state_value,
                        "is_goal": node.is_goal,
                        "reward": node.reward,
                    }
                    for node in sg.nodes.values()
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "prob": edge.prob,
                        "reward": edge.reward,
                    }
                    for edge in sg.edges
                ],
                "start": sg.start,
                "goal": sg.goal,
                "metadata": sg.metadata,
            },
            f,
            indent=2,
        )
    _log.debug("Graph saved to %s", out_path)

# ----------------------------------------------------------------------
# Tier‑1 generator (deterministic chain)
# ----------------------------------------------------------------------
def generate_tier_1(seed: Optional[int] = None, max_retries: int = 100) -> StateGraph:
    """Generate a Tier‑1 deterministic graph."""
    _ensure_seed(seed)
    cfg = get_tier_config(1)
    min_nodes, max_nodes = cfg["node_range"]
    for _ in range(max_retries):
        n_nodes = random.randint(min_nodes, max_nodes)
        nodes = {f"n{i}": Node(id=f"n{i}", state_value=i) for i in range(n_nodes)}
        edges = [
            Edge(source=f"n{i}", target=f"n{i+1}", prob=1.0, reward=0.0)
            for i in range(n_nodes - 1)
        ]
        sg = StateGraph(
            tier=1,
            graph_id=_graph_id(1, seed),
            nodes=nodes,
            edges=edges,
            start="n0",
            goal=f"n{n_nodes-1}",
            metadata={},
        )
        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except RuntimeError:
            continue
    raise RuntimeError("Failed to generate a valid Tier‑1 graph after max retries")

# ----------------------------------------------------------------------
# Tier‑2 generator (stochastic branching)
# ----------------------------------------------------------------------
def generate_tier_2(seed: Optional[int] = None, max_retries: int = 100) -> StateGraph:
    """Generate a Tier‑2 stochastic graph."""
    _ensure_seed(seed)
    cfg = get_tier_config(2)
    min_nodes, max_nodes = cfg["node_range"]
    for _ in range(max_retries):
        n_nodes = random.randint(min_nodes, max_nodes)
        nodes = {f"n{i}": Node(id=f"n{i}", state_value=i) for i in range(n_nodes)}
        edges: List[Edge] = []

        # Ensure at least one branching node
        branching_node = random.randint(0, n_nodes - 2)
        for i in range(n_nodes - 1):
            if i == branching_node:
                # Create two outgoing edges with stochastic probabilities
                prob1 = random.uniform(0.4, 0.9)
                prob2 = 1.0 - prob1
                edges.append(Edge(source=f"n{i}", target=f"n{i+1}", prob=prob1, reward=0.0))
                edges.append(Edge(source=f"n{i}", target=f"n{i+2 if i+2 < n_nodes else i+1}", prob=prob2, reward=0.0))
            else:
                edges.append(Edge(source=f"n{i}", target=f"n{i+1}", prob=1.0, reward=0.0))

        # Randomly assign sparse rewards (≤10% of nodes)
        reward_nodes = random.sample(list(nodes.keys()), k=max(1, n_nodes // 10))
        for rn in reward_nodes:
            nodes[rn].reward = random.uniform(0.1, 1.0)

        sg = StateGraph(
            tier=2,
            graph_id=_graph_id(2, seed),
            nodes=nodes,
            edges=edges,
            start="n0",
            goal=f"n{n_nodes-1}",
            metadata={},
        )
        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except RuntimeError:
            continue
    raise RuntimeError("Failed to generate a valid Tier‑2 graph after max retries")

# ----------------------------------------------------------------------
# Tier‑3 generator (high‑entropy, sparse rewards)
# ----------------------------------------------------------------------
def generate_tier_3_nodes(seed: Optional[int] = None, num_nodes: Optional[int] = None) -> List[Node]:
    """Generate Tier‑3 nodes (100+ nodes with sparse rewards)."""
    _ensure_seed(seed)
    cfg = get_tier_config(3)
    min_nodes, max_nodes = cfg["node_range"]
    if num_nodes is None:
        num_nodes = random.randint(max(min_nodes, 100), max_nodes)
    nodes = [Node(id=f"n{i}", state_value=i) for i in range(num_nodes)]

    # Sparse rewards (≈1 per 10 nodes)
    reward_nodes = random.sample(nodes, k=max(1, num_nodes // 10))
    for node in reward_nodes:
        node.reward = random.uniform(0.1, 1.0)

    return nodes

def generate_tier_3_edges(nodes: List[Node], seed: Optional[int] = None) -> List[Edge]:
    """Generate Tier‑3 edges with high‑entropy transition probabilities."""
    _ensure_seed(seed)
    edges: List[Edge] = []
    n = len(nodes)
    for i in range(n - 1):
        # Connect to next node with a probability sampled from a beta distribution
        prob = np.random.beta(a=2.0, b=5.0)  # skewed towards lower probabilities
        edges.append(Edge(source=nodes[i].id, target=nodes[i + 1].id, prob=prob, reward=0.0))
    return edges

def generate_tier_3(seed: Optional[int] = None, num_nodes: Optional[int] = None, max_retries: int = 100) -> StateGraph:
    """Generate a complete Tier‑3 StateGraph."""
    _ensure_seed(seed)
    for _ in range(max_retries):
        nodes = {node.id: node for node in generate_tier_3_nodes(seed, num_nodes)}
        edges = generate_tier_3_edges(list(nodes.values()), seed)
        sg = StateGraph(
            tier=3,
            graph_id=_graph_id(3, seed),
            nodes=nodes,
            edges=edges,
            start=list(nodes.keys())[0],
            goal=list(nodes.keys())[-1],
            metadata={},
        )
        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except RuntimeError:
            continue
    raise RuntimeError("Failed to generate a valid Tier‑3 graph after max retries")