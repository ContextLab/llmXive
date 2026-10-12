import json
import logging
import random
import uuid
from typing import List, Optional

import numpy as np

from environment.state_graph import Node, Edge, StateGraph
from environment.validator import validate_graph
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def _ensure_seed(seed: Optional[int]) -> None:
    """Set seeds for reproducibility if a seed is provided."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

def _graph_id(tier: int, seed: Optional[int]) -> str:
    """Create a reasonably unique graph identifier."""
    unique_part = uuid.uuid4().hex[:8]
    base = f"tier{tier}"
    if seed is not None:
        base = f"{base}_{seed}"
    return f"{base}_{unique_part}"

def _save_graph(sg: StateGraph) -> None:
    """Serialize a StateGraph to JSON in the synthetic_graphs folder."""
    out_path = paths.data("raw", "synthetic_graphs", f"{sg.graph_id}.json")
    # Ensure the directory exists (paths.data creates parent dirs)
    graph_dict = {
        "graph_id": sg.graph_id,
        "tier": sg.tier,
        "nodes": [
            {
                "node_id": getattr(node, "node_id", getattr(node, "id", None)),
                "reward": getattr(node, "reward", 0.0),
                "metadata": getattr(node, "metadata", {})
            }
            for node in sg.nodes
        ],
        "edges": [
            {
                "source": getattr(edge, "source", None),
                "target": getattr(edge, "target", None),
                "probability": getattr(edge, "probability", 1.0),
                "metadata": getattr(edge, "metadata", {})
            }
            for edge in sg.edges
        ],
        "start": sg.start,
        "goal": sg.goal,
        "metadata": getattr(sg, "metadata", {})
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(graph_dict, f, indent=2)
    logger.info("Saved graph %s to %s", sg.graph_id, out_path)

# -------------------------------------------------------------------------
# Tier‑1 generator (deterministic, small)
# -------------------------------------------------------------------------

def generate_tier_1(seed: Optional[int] = None, max_retries: int = 100) -> StateGraph:
    """
    Generate a Tier‑1 deterministic graph.

    Acceptance criteria:
    - Node count between 5 and 10 (inclusive).
    - Exactly one path from start to goal (a simple chain).
    - All edges have probability 1.0 (no stochasticity).
    - No rewards on any node (reward sparsity = 0).

    The function retries up to ``max_retries`` times if validation fails.
    """
    _ensure_seed(seed)

    for attempt in range(max_retries):
        # Determine node count
        num_nodes = int(np.random.randint(5, 11))
        nodes: List[Node] = [
            Node(node_id=f"n{i}", reward=0.0, metadata={})
            for i in range(num_nodes)
        ]

        # Create a linear chain of edges
        edges: List[Edge] = [
            Edge(source=f"n{i}", target=f"n{i+1}", probability=1.0, metadata={})
            for i in range(num_nodes - 1)
        ]

        start = "n0"
        goal = f"n{num_nodes - 1}"
        sg = StateGraph(
            graph_id=_graph_id(tier=1, seed=seed),
            tier=1,
            nodes=nodes,
            edges=edges,
            start=start,
            goal=goal,
            metadata={}
        )

        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except Exception as e:
            logger.debug(
                "Tier‑1 generation attempt %d failed validation: %s", attempt + 1, e
            )
            continue

    raise RuntimeError(f"Failed to generate a valid Tier‑1 graph after {max_retries} attempts")

# -------------------------------------------------------------------------
# Tier‑2 generator (moderate size, branching, stochastic)
# -------------------------------------------------------------------------

def generate_tier_2(seed: Optional[int] = None, max_retries: int = 100) -> StateGraph:
    """
    Generate a Tier‑2 stochastic graph.

    Acceptance criteria:
    - Node count between 20 and 50 (inclusive).
    - At least one branching node (out‑degree > 1).
    - Some edges have probability < 1.0 (stochastic transitions).
    - Reward sparsity ≤ 0.1 (≤ 10 % of nodes have a positive reward).
    """
    _ensure_seed(seed)

    for attempt in range(max_retries):
        num_nodes = int(np.random.randint(20, 51))
        nodes: List[Node] = [
            Node(node_id=f"n{i}", reward=0.0, metadata={})
            for i in range(num_nodes)
        ]

        # Randomly decide which nodes get a reward (≤10%)
        reward_nodes = random.sample(
            range(num_nodes), k=int(max(1, num_nodes * 0.1))
        )
        for idx in reward_nodes:
            nodes[idx].reward = 1.0  # simple binary reward

        edges: List[Edge] = []
        # Ensure a base linear backbone for reachability
        for i in range(num_nodes - 1):
            prob = 1.0 if random.random() < 0.7 else np.random.uniform(0.5, 0.9)
            edges.append(
                Edge(source=f"n{i}", target=f"n{i+1}", probability=prob, metadata={})
            )

        # Add at least one branching edge
        branch_source = random.randint(0, num_nodes - 3)
        branch_target = random.randint(branch_source + 2, num_nodes - 1)
        prob_branch = np.random.uniform(0.5, 0.9)
        edges.append(
            Edge(
                source=f"n{branch_source}",
                target=f"n{branch_target}",
                probability=prob_branch,
                metadata={},
            )
        )

        # Possibly add a few extra stochastic edges (up to 10% of total edges)
        extra_edges = max(1, int(0.1 * len(edges)))
        for _ in range(extra_edges):
            src = random.randint(0, num_nodes - 2)
            dst = random.randint(src + 1, num_nodes - 1)
            prob = np.random.uniform(0.5, 0.9)
            edges.append(
                Edge(
                    source=f"n{src}",
                    target=f"n{dst}",
                    probability=prob,
                    metadata={},
                )
            )

        start = "n0"
        goal = f"n{num_nodes - 1}"
        sg = StateGraph(
            graph_id=_graph_id(tier=2, seed=seed),
            tier=2,
            nodes=nodes,
            edges=edges,
            start=start,
            goal=goal,
            metadata={},
        )

        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except Exception as e:
            logger.debug(
                "Tier‑2 generation attempt %d failed validation: %s", attempt + 1, e
            )
            continue

    raise RuntimeError(f"Failed to generate a valid Tier‑2 graph after {max_retries} attempts")

# -------------------------------------------------------------------------
# Tier‑3 generator (high‑entropy, large, sparse rewards)
# -------------------------------------------------------------------------

def generate_tier_3_nodes(
    seed: Optional[int] = None, num_nodes: Optional[int] = None
) -> List[Node]:
    """
    Generate Tier‑3 nodes: 100+ nodes with sparse rewards.

    Args:
        seed: Optional seed for reproducibility.
        num_nodes: Optional override for the number of nodes (defaults to 100).

    Returns:
        List of Node objects.
    """
    _ensure_seed(seed)
    if num_nodes is None:
        num_nodes = int(np.random.randint(100, 151))
    nodes = []
    for i in range(num_nodes):
        # Sparse reward: roughly 1 reward per 10 nodes
        reward = 1.0 if i % 10 == 0 else 0.0
        nodes.append(Node(node_id=f"n{i}", reward=reward, metadata={}))
    return nodes

def generate_tier_3_edges(
    nodes: List[Node], seed: Optional[int] = None
) -> List[Edge]:
    """
    Generate Tier‑3 edges with high‑entropy transition probabilities.

    Args:
        nodes: List of Node objects.
        seed: Optional seed for reproducibility.

    Returns:
        List of Edge objects.
    """
    _ensure_seed(seed)
    edges = []
    num_nodes = len(nodes)
    # Create a backbone path to guarantee reachability
    for i in range(num_nodes - 1):
        prob = np.random.uniform(0.3, 0.9)
        edges.append(
            Edge(source=nodes[i].node_id, target=nodes[i + 1].node_id, probability=prob, metadata={})
        )
    # Add additional stochastic edges
    extra_edge_count = max(1, int(0.2 * num_nodes))
    for _ in range(extra_edge_count):
        src_idx = np.random.randint(0, num_nodes - 2)
        dst_idx = np.random.randint(src_idx + 2, num_nodes)
        prob = np.random.uniform(0.3, 0.9)
        edges.append(
            Edge(
                source=nodes[src_idx].node_id,
                target=nodes[dst_idx].node_id,
                probability=prob,
                metadata={},
            )
        )
    return edges

def generate_tier_3(
    seed: Optional[int] = None,
    num_nodes: Optional[int] = None,
    max_retries: int = 100,
) -> StateGraph:
    """
    Generate a complete Tier‑3 StateGraph.

    Combines node and edge generation, then validates.

    Args:
        seed: Optional seed for reproducibility.
        num_nodes: Optional override for the number of nodes.
        max_retries: Maximum number of attempts to generate a valid graph.

    Returns:
        A valid StateGraph object.

    Raises:
        RuntimeError: If a valid graph cannot be generated within max_retries.
    """
    _ensure_seed(seed)

    for attempt in range(max_retries):
        nodes = generate_tier_3_nodes(seed=seed, num_nodes=num_nodes)
        edges = generate_tier_3_edges(nodes=nodes, seed=seed)

        start = nodes[0].node_id
        goal = nodes[-1].node_id

        sg = StateGraph(
            graph_id=_graph_id(tier=3, seed=seed),
            tier=3,
            nodes=nodes,
            edges=edges,
            start=start,
            goal=goal,
            metadata={},
        )

        try:
            validate_graph(sg)
            _save_graph(sg)
            return sg
        except Exception as e:
            logger.debug(
                "Tier‑3 generation attempt %d failed validation: %s", attempt + 1, e
            )
            continue

    raise RuntimeError(
        f"Failed to generate a valid Tier‑3 graph after {max_retries} attempts"
    )