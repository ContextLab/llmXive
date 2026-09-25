import logging
import random
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from environment.state_graph import Node, Edge, StateGraph
from config import get_seed, set_seed

logger = logging.getLogger(__name__)

class GraphGenerator:
    """
    Generates synthetic State-Graph Environments with multiple distinct complexity tiers.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate(self, tier: int, seed: Optional[int] = None) -> StateGraph:
        """
        Generate a graph for the specified tier.

        Args:
            tier: The complexity tier (1, 2, or 3).
            seed: Optional seed for reproducibility.

        Returns:
            A valid StateGraph instance.

        Raises:
            ValueError: If tier is not 1, 2, or 3.
            RuntimeError: If a valid graph cannot be generated within max_retries.
        """
        if seed is not None:
            set_seed(seed)

        if tier == 1:
            return self.generate_tier_1()
        elif tier == 2:
            return self.generate_tier_2()
        elif tier == 3:
            return self.generate_tier_3()
        else:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3.")

    def generate_tier_1(self) -> StateGraph:
        """
        Tier 1: Single unique path with 5 to 10 nodes, zero stochastic branching.
        Regenerates if graph is invalid (path exists from start to goal).
        """
        max_retries = 100
        attempts = 0

        while attempts < max_retries:
            # Determine number of nodes (5 to 10)
            num_nodes = random.randint(5, 10)
            
            # Create a simple linear path
            nodes = []
            edges = []
            
            # Create nodes
            for i in range(num_nodes):
                node_id = f"node_{i}"
                reward = 1.0 if i == num_nodes - 1 else 0.0  # Reward only at goal
                nodes.append(Node(id=node_id, reward=reward, is_start=(i == 0), is_goal=(i == num_nodes - 1)))
            
            # Create edges (linear path)
            for i in range(num_nodes - 1):
                src_id = f"node_{i}"
                dst_id = f"node_{i+1}"
                edges.append(Edge(src=src_id, dst=dst_id, prob=1.0))
            
            # Create graph
            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=1
            )
            
            # Validate
            if graph.is_valid():
                return graph
            
            attempts += 1
        
        raise RuntimeError(f"Failed to generate valid Tier 1 graph after {max_retries} attempts")

    def generate_tier_2(self) -> StateGraph:
        """
        Tier 2: 20 to 50 nodes with multiple branching paths and stochastic transition probabilities (p=0.8).
        Regenerates if graph is invalid (path exists from start to goal).
        """
        max_retries = 100
        attempts = 0

        while attempts < max_retries:
            # Determine number of nodes (20 to 50)
            num_nodes = random.randint(20, 50)
            
            nodes = []
            edges = []
            
            # Create nodes
            for i in range(num_nodes):
                node_id = f"node_{i}"
                # Sparse rewards: roughly 1 per 5-10 nodes
                reward = 1.0 if (i > 0 and i < num_nodes - 1 and random.random() < 0.1) or (i == num_nodes - 1) else 0.0
                nodes.append(Node(id=node_id, reward=reward, is_start=(i == 0), is_goal=(i == num_nodes - 1)))
            
            # Create branching edges
            # Ensure forward progress and some branching
            for i in range(num_nodes - 1):
                src_id = f"node_{i}"
                # Always connect to next node
                dst_id = f"node_{i+1}"
                edges.append(Edge(src=src_id, dst=dst_id, prob=0.8))
                
                # Add branching with some probability
                if i < num_nodes - 2 and random.random() < 0.3:
                    # Branch to a node 2 steps ahead
                    branch_dst = f"node_{i+2}"
                    edges.append(Edge(src=src_id, dst=branch_dst, prob=0.2))
            
            # Create graph
            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=2
            )
            
            # Validate
            if graph.is_valid():
                return graph
            
            attempts += 1
        
        raise RuntimeError(f"Failed to generate valid Tier 2 graph after {max_retries} attempts")

    def generate_tier_3(self) -> StateGraph:
        """
        Tier 3: Scalable network with multiple nodes, sparse reward signals (approx one per ten nodes),
        and high-entropy transitions.
        Regenerates if graph is invalid (path exists from start to goal).
        
        Constraint: max_retries=100; valid graph defined as 'path exists from start to goal'.
        """
        max_retries = 100
        attempts = 0

        while attempts < max_retries:
            # Determine number of nodes (scalable, e.g., 50 to 150)
            num_nodes = random.randint(50, 150)
            
            nodes = []
            edges = []
            
            # Create nodes with sparse rewards
            for i in range(num_nodes):
                node_id = f"node_{i}"
                # Sparse reward: approximately one per ten nodes
                # Goal node always has reward, others randomly
                if i == num_nodes - 1:
                    reward = 1.0
                elif random.random() < 0.1:  # ~10% chance
                    reward = 1.0
                else:
                    reward = 0.0
                
                nodes.append(Node(
                    id=node_id,
                    reward=reward,
                    is_start=(i == 0),
                    is_goal=(i == num_nodes - 1)
                ))
            
            # Create high-entropy edges (more branching, lower probabilities)
            for i in range(num_nodes - 1):
                src_id = f"node_{i}"
                
                # Multiple possible destinations to create high entropy
                possible_dests = []
                
                # Always include next node
                next_node = f"node_{i+1}"
                possible_dests.append((next_node, 0.4))
                
                # Add more branches with lower probabilities
                if i < num_nodes - 2:
                    jump2 = f"node_{i+2}"
                    possible_dests.append((jump2, 0.3))
                
                if i < num_nodes - 3:
                    jump3 = f"node_{i+3}"
                    possible_dests.append((jump3, 0.2))
                
                if i < num_nodes - 4:
                    jump4 = f"node_{i+4}"
                    possible_dests.append((jump4, 0.1))
                
                # Create edges with these probabilities
                for dst_id, prob in possible_dests:
                    edges.append(Edge(src=src_id, dst=dst_id, prob=prob))
            
            # Create graph
            graph = StateGraph(
                nodes=nodes,
                edges=edges,
                start=nodes[0].id,
                goal=nodes[-1].id,
                tier=3
            )
            
            # Validate
            if graph.is_valid():
                return graph
            
            attempts += 1
        
        raise RuntimeError(f"Failed to generate valid Tier 3 graph after {max_retries} attempts")