import logging
import random
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

from env.state_graph import Node, Edge, StateGraph
from config import get_seed, set_seed

logger = logging.getLogger(__name__)


class GraphGenerator:
    """
    Generates synthetic State-Graph Environments with multiple complexity tiers.
    """

    def __init__(self):
        self.tier_1_node_range = (10, 20)
        self.tier_2_node_count = (20, 50)
        self.tier_3_node_count = (100, 200)
        self.tier_3_reward_density = 0.1

    def generate(self, tier: int, seed: Optional[int] = None) -> StateGraph:
        """
        Generate a graph for the specified tier.

        Args:
            tier: 1 (deterministic), 2 (stochastic branching), 3 (high-entropy sparse)
            seed: Optional seed override. If None, uses global config seed.

        Returns:
            A valid StateGraph instance.

        Raises:
            ValueError: If tier is not 1, 2, or 3.
        """
        if seed is not None:
            set_seed(seed)
        else:
            set_seed(get_seed())

        if tier == 1:
            return self.generate_tier_1()
        elif tier == 2:
            return self.generate_tier_2()
        elif tier == 3:
            return self.generate_tier_3()
        else:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3.")

    def _is_valid_graph(self, graph: StateGraph) -> bool:
        """
        Validates that the graph has a reachable goal from the start node.
        Performs a BFS to ensure connectivity.
        """
        if not graph.nodes:
            return False
        if graph.start is None or graph.goal is None:
            return False
        if graph.start not in graph.nodes or graph.goal not in graph.nodes:
            return False

        visited = set()
        queue = [graph.start]
        visited.add(graph.start)

        while queue:
            current = queue.pop(0)
            if current == graph.goal:
                return True
            for edge in graph.edges:
                if edge.src == current and edge.dst not in visited:
                    visited.add(edge.dst)
                    queue.append(edge.dst)

        return False

    def generate_tier_1(self) -> StateGraph:
        """
        Generate Tier 1: A single unique path with variable node count.
        Zero stochastic branching.
        """
        max_attempts = 100
        for attempt in range(max_attempts):
            num_nodes = random.randint(self.tier_1_node_range[0], self.tier_1_node_range[1])
            nodes = []
            edges = []

            for i in range(num_nodes):
                node_id = f"N{i}"
                node = Node(id=node_id, is_goal=(i == num_nodes - 1))
                nodes.append(node)

            for i in range(num_nodes - 1):
                edge = Edge(src=f"N{i}", dst=f"N{i+1}", probability=1.0)
                edges.append(edge)

            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=1
            )

            if self._is_valid_graph(graph):
                logger.info(f"Tier 1 graph generated successfully with {num_nodes} nodes (Attempt {attempt + 1})")
                return graph

        raise RuntimeError(f"Failed to generate valid Tier 1 graph after {max_attempts} attempts")

    def generate_tier_2(self) -> StateGraph:
        """
        Generate Tier 2: 20-50 nodes with multiple branching paths and stochastic transitions (p=0.8).
        """
        max_attempts = 100
        for attempt in range(max_attempts):
            num_nodes = random.randint(self.tier_2_node_count[0], self.tier_2_node_count[1])
            nodes = []
            edges = []

            # Create layers to ensure forward progress
            layer_size = max(3, num_nodes // 10)
            num_layers = max(5, num_nodes // layer_size)
            nodes_per_layer = [layer_size] * num_layers
            # Adjust last layer to be smaller if needed
            if sum(nodes_per_layer) > num_nodes:
                nodes_per_layer[-1] = num_nodes - sum(nodes_per_layer[:-1])

            current_node_idx = 0
            layer_start_indices = [0]
            for size in nodes_per_layer:
                layer_start_indices.append(layer_start_indices[-1] + size)

            # Create nodes
            for i in range(num_nodes):
                is_goal = (i == num_nodes - 1)
                node = Node(id=f"N{i}", is_goal=is_goal)
                nodes.append(node)

            # Create edges with branching
            for i in range(num_nodes - 1):
                current_layer_idx = -1
                for l_idx, start in enumerate(layer_start_indices):
                    if i >= start:
                        current_layer_idx = l_idx
                    else:
                        break

                if current_layer_idx == -1 or current_layer_idx == len(nodes_per_layer) - 1:
                    continue

                # Connect to next layer
                next_layer_start = layer_start_indices[current_layer_idx + 1]
                next_layer_end = layer_start_indices[current_layer_idx + 2]

                # Determine how many edges to create (branching factor)
                max_connections = min(3, next_layer_end - next_layer_start)
                num_connections = random.randint(1, max_connections)

                targets = random.sample(range(next_layer_start, next_layer_end), num_connections)

                for target in targets:
                    prob = 0.8 if len(targets) > 1 else 1.0
                    edge = Edge(src=f"N{i}", dst=f"N{target}", probability=prob)
                    edges.append(edge)

            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=2
            )

            if self._is_valid_graph(graph):
                logger.info(f"Tier 2 graph generated successfully with {num_nodes} nodes (Attempt {attempt + 1})")
                return graph

        raise RuntimeError(f"Failed to generate valid Tier 2 graph after {max_attempts} attempts")

    def generate_tier_3(self) -> StateGraph:
        """
        Generate Tier 3: A scalable network of nodes with sparse reward signals
        (approximately one reward per ten nodes) and high-entropy transitions.

        Requirements:
        - 100+ nodes
        - Sparse rewards (~1 per 10 nodes)
        - High-entropy transitions (probabilities distributed widely)
        - Internal loop to regenerate if invalid
        """
        max_attempts = 100
        for attempt in range(max_attempts):
            num_nodes = random.randint(self.tier_3_node_count[0], self.tier_3_node_count[1])
            nodes = []
            edges = []

            # Create a layered structure to ensure reachability but with high connectivity
            layer_size = max(10, num_nodes // 10)
            num_layers = max(10, num_nodes // layer_size)
            nodes_per_layer = [layer_size] * num_layers
            if sum(nodes_per_layer) > num_nodes:
                nodes_per_layer[-1] = num_nodes - sum(nodes_per_layer[:-1])

            layer_start_indices = [0]
            for size in nodes_per_layer:
                layer_start_indices.append(layer_start_indices[-1] + size)

            # Create nodes
            for i in range(num_nodes):
                node = Node(id=f"N{i}", is_goal=False)
                nodes.append(node)
            nodes[-1].is_goal = True

            # Assign sparse rewards: approx 1 per 10 nodes
            reward_indices = set()
            num_rewards = max(1, int(num_nodes * self.tier_3_reward_density))
            # Ensure start and goal are not rewarded (usually)
            available_indices = list(range(1, num_nodes - 1))
            if len(available_indices) > 0:
                reward_indices = set(random.sample(available_indices, min(num_rewards, len(available_indices))))
                for idx in reward_indices:
                    nodes[idx].reward = 1.0
                logger.debug(f"Assigned rewards to nodes: {sorted(reward_indices)}")

            # Create edges with high-entropy transitions
            for i in range(num_nodes - 1):
                current_layer_idx = -1
                for l_idx, start in enumerate(layer_start_indices):
                    if i >= start:
                        current_layer_idx = l_idx
                    else:
                        break

                if current_layer_idx == -1 or current_layer_idx == len(nodes_per_layer) - 1:
                    continue

                next_layer_start = layer_start_indices[current_layer_idx + 1]
                next_layer_end = layer_start_indices[current_layer_idx + 2]

                # High branching factor for complexity
                max_connections = min(5, next_layer_end - next_layer_start)
                num_connections = random.randint(2, max_connections)

                targets = random.sample(range(next_layer_start, next_layer_end), num_connections)

                for target in targets:
                    # High entropy: probabilities vary significantly
                    # Use a distribution that isn't uniform or deterministic
                    prob = np.random.beta(2, 5)  # Skewed towards lower values, high variance
                    # Ensure probability is reasonable for a path to exist
                    if prob < 0.1:
                        prob = 0.1
                    edge = Edge(src=f"N{i}", dst=f"N{target}", probability=prob)
                    edges.append(edge)

            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=3
            )

            if self._is_valid_graph(graph):
                logger.info(f"Tier 3 graph generated successfully with {num_nodes} nodes, {len(reward_indices)} rewards (Attempt {attempt + 1})")
                return graph

        raise RuntimeError(f"Failed to generate valid Tier 3 graph after {max_attempts} attempts")


def main():
    """Main entry point for testing graph generation."""
    logging.basicConfig(level=logging.INFO)
    generator = GraphGenerator()

    # Test Tier 3 generation
    print("Generating Tier 3 graph...")
    try:
        graph = generator.generate_tier_3()
        print(f"Success! Generated graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
        print(f"Start: {graph.start}, Goal: {graph.goal}")
        reward_count = sum(1 for n in graph.nodes if n.reward > 0)
        print(f"Reward nodes: {reward_count}")
    except Exception as e:
        print(f"Failed: {e}")
        raise


if __name__ == "__main__":
    main()