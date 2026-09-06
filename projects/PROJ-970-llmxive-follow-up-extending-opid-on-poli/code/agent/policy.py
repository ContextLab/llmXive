"""
Lightweight baseline policy module for OPID routing experiments.

This module implements a rule-based baseline policy that serves as a reference
for the OPID router's skill injection decisions. The policy uses deterministic
heuristics based on the StateGraph structure to select actions.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import numpy as np

# Import from project API surface
from env.state_graph import Node, Edge, StateGraph
from config import get_seed, set_seed


@dataclass
class BaselinePolicyConfig:
    """Configuration for the baseline policy."""
    temperature: float = 1.0
    """Softmax temperature for action probabilities."""
    prefer_shortest_path: bool = True
    """If True, bias towards actions that reduce distance to goal."""
    exploration_weight: float = 0.0
    """Weight for random exploration (0.0 = deterministic)."""


class BaselinePolicy:
    """
    A lightweight, rule-based baseline policy for StateGraph navigation.

    This policy implements a deterministic heuristic that:
    1. Calculates the shortest path distance from current node to goal
    2. Selects actions that minimize this distance
    3. Falls back to random selection if no progress is possible

    The policy is designed to be:
    - Fast (O(1) per step with pre-computed distances)
    - Deterministic (given same graph and seed)
    - Interpretable (clear decision logic)
    """

    def __init__(self, graph: StateGraph, config: Optional[BaselinePolicyConfig] = None):
        """
        Initialize the baseline policy for a given graph.

        Args:
            graph: The StateGraph to navigate
            config: Optional configuration for the policy
        """
        self.graph = graph
        self.config = config or BaselinePolicyConfig()

        # Pre-compute shortest path distances from all nodes to goal
        self._distances_to_goal: Dict[str, float] = {}
        self._precompute_distances()

    def _precompute_distances(self) -> None:
        """
        Compute shortest path distances from all nodes to the goal node.
        Uses BFS for unweighted graphs (or Dijkstra if weights exist).
        """
        goal_node = self.graph.get_goal_node()
        if goal_node is None:
            # No goal defined, all distances are infinity
            self._distances_to_goal = {
                node_id: float('inf')
                for node_id in self.graph.nodes
            }
            return

        goal_id = goal_node.node_id

        # BFS to compute distances (unweighted)
        distances = {node_id: float('inf') for node_id in self.graph.nodes}
        distances[goal_id] = 0.0

        queue = [goal_id]
        visited = {goal_id}

        while queue:
            current_id = queue.pop(0)

            # Find all nodes that can reach current_id (reverse edges)
            for node_id, node in self.graph.nodes.items():
                if node_id in visited:
                    continue

                # Check if there's an edge from node_id to current_id
                if current_id in node.get_outgoing_edge_ids():
                    # Reverse: current_id is reachable from node_id
                    # We need to check if current_id is in node's outgoing edges
                    pass

            # Better approach: build reverse adjacency
            pass

        # Re-implement with proper reverse graph traversal
        # Build reverse adjacency list
        reverse_adj: Dict[str, List[str]] = {node_id: [] for node_id in self.graph.nodes}
        for node_id, node in self.graph.nodes.items():
            for edge in node.outgoing_edges:
                if edge.target_node_id in self.graph.nodes:
                    reverse_adj[edge.target_node_id].append(node_id)

        # BFS from goal using reverse edges
        queue = [goal_id]
        visited = {goal_id}
        distances[goal_id] = 0.0

        while queue:
            current_id = queue.pop(0)
            for neighbor_id in reverse_adj[current_id]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    distances[neighbor_id] = distances[current_id] + 1.0
                    queue.append(neighbor_id)

        self._distances_to_goal = distances

    def get_action_probabilities(
        self,
        current_node_id: str,
        rng: Optional[np.random.Generator] = None
    ) -> Dict[str, float]:
        """
        Compute action probabilities for the current node.

        Args:
            current_node_id: The ID of the current node
            rng: Optional random number generator for exploration

        Returns:
            Dictionary mapping action IDs to probabilities
        """
        if current_node_id not in self.graph.nodes:
            raise ValueError(f"Node {current_node_id} not found in graph")

        node = self.graph.nodes[current_node_id]
        outgoing_edges = node.outgoing_edges

        if not outgoing_edges:
            # No actions available
            return {}

        # Calculate heuristic scores for each action
        scores: Dict[str, float] = {}
        current_distance = self._distances_to_goal.get(current_node_id, float('inf'))

        for edge in outgoing_edges:
            target_id = edge.target_node_id
            target_distance = self._distances_to_goal.get(target_id, float('inf'))

            # Heuristic: prefer actions that reduce distance to goal
            distance_improvement = current_distance - target_distance

            if self.config.prefer_shortest_path:
                # Higher score for better distance improvement
                score = distance_improvement
            else:
                # Random policy
                score = 0.0

            # Add exploration component
            if self.config.exploration_weight > 0:
                if rng is None:
                    rng = np.random.default_rng(get_seed())
                exploration_bonus = rng.uniform(0, self.config.exploration_weight)
                score += exploration_bonus

            scores[edge.action_id] = score

        # Convert scores to probabilities using softmax
        if not scores:
            return {}

        max_score = max(scores.values())
        # Avoid numerical issues
        exp_scores = {
            action_id: math.exp(score - max_score) / self.config.temperature
            for action_id, score in scores.items()
        }

        total = sum(exp_scores.values())
        if total == 0:
            # Fallback to uniform distribution
            prob = 1.0 / len(exp_scores)
            return {action_id: prob for action_id in exp_scores.keys()}

        probabilities = {
            action_id: exp_score / total
            for action_id, exp_score in exp_scores.items()
        }

        return probabilities

    def select_action(
        self,
        current_node_id: str,
        rng: Optional[np.random.Generator] = None
    ) -> str:
        """
        Select a single action for the current node.

        Args:
            current_node_id: The ID of the current node
            rng: Optional random number generator for sampling

        Returns:
            The selected action ID
        """
        probabilities = self.get_action_probabilities(current_node_id, rng)

        if not probabilities:
            raise ValueError(f"No actions available for node {current_node_id}")

        if rng is None:
            rng = np.random.default_rng(get_seed())

        # Sample from the probability distribution
        actions = list(probabilities.keys())
        probs = list(probabilities.values())

        selected_idx = rng.choice(len(actions), p=probs)
        return actions[selected_idx]

    def get_expected_value(self, current_node_id: str) -> float:
        """
        Get the expected value (distance to goal) for the current node.

        Args:
            current_node_id: The ID of the current node

        Returns:
            The expected distance to goal
        """
        return self._distances_to_goal.get(current_node_id, float('inf'))


def create_baseline_policy(
    graph: StateGraph,
    temperature: float = 1.0,
    prefer_shortest_path: bool = True,
    exploration_weight: float = 0.0
) -> BaselinePolicy:
    """
    Factory function to create a configured baseline policy.

    Args:
        graph: The StateGraph to navigate
        temperature: Softmax temperature
        prefer_shortest_path: Whether to bias towards shortest path
        exploration_weight: Weight for random exploration

    Returns:
        Configured BaselinePolicy instance
    """
    config = BaselinePolicyConfig(
        temperature=temperature,
        prefer_shortest_path=prefer_shortest_path,
        exploration_weight=exploration_weight
    )
    return BaselinePolicy(graph, config)


def main():
    """
    Simple test/demo of the baseline policy.
    """
    from env.graph_generator import GraphGenerator, GraphGenerationConfig
    from config import set_seed

    # Set seed for reproducibility
    set_seed(42)

    # Create a simple Tier 1 graph (deterministic path)
    config = GraphGenerationConfig(
        tier=1,
        num_nodes=5,
        seed=42
    )

    generator = GraphGenerator(config)
    graph = generator.generate()

    print(f"Generated graph with {len(graph.nodes)} nodes")
    print(f"Goal node: {graph.get_goal_node().node_id if graph.get_goal_node() else 'None'}")

    # Create baseline policy
    policy = create_baseline_policy(
        graph,
        temperature=1.0,
        prefer_shortest_path=True,
        exploration_weight=0.0
    )

    # Simulate a few steps
    current_node = graph.get_start_node()
    if current_node:
        print(f"\nStarting from node: {current_node.node_id}")

        for step in range(5):
            action = policy.select_action(current_node.node_id)
            expected_value = policy.get_expected_value(current_node.node_id)

            print(f"Step {step}: Node={current_node.node_id}, Action={action}, "
                  f"Expected Distance={expected_value:.2f}")

            # Move to next node (deterministic for Tier 1)
            next_node_id = None
            for edge in current_node.outgoing_edges:
                if edge.action_id == action:
                    next_node_id = edge.target_node_id
                    break

            if next_node_id and next_node_id in graph.nodes:
                current_node = graph.nodes[next_node_id]
            else:
                print("  -> No valid transition found")
                break

    print("\nBaseline policy test completed successfully.")


if __name__ == "__main__":
    main()