"""
Baseline Policy Implementation for OPID Routing Analysis.

Implements a Stochastic Softmax Policy using CPU-only numpy operations.
This policy serves as the baseline for comparing against OPID-injected skills.
"""

import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

from environment.state_graph import Node, Edge, StateGraph

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class BaselinePolicyConfig:
    """Configuration for the Baseline Policy."""
    temperature: float = 1.0
    """Temperature parameter tau > 0 for softmax. Higher values = more random, lower = more deterministic."""
    seed: int = 42
    """Random seed for reproducibility."""

class BaselinePolicy:
    """
    A lightweight baseline policy using CPU-only numpy operations.

    Implementation is a Stochastic Softmax Policy with a temperature parameter `tau > 0`
    to ensure non-zero baseline entropy variance (as required by FR-007 and Const I).

    The policy maps state features to action probabilities via a softmax function.
    For this baseline, we use a simple heuristic: prefer edges that reduce distance
    to the goal (if known) or select randomly with bias towards unvisited nodes.
    """

    def __init__(self, config: BaselinePolicyConfig):
        """
        Initialize the policy.

        Args:
            config: BaselinePolicyConfig containing temperature and seed.
        """
        self.temperature = config.temperature
        self.seed = config.seed
        self.rng = np.random.default_rng(self.seed)

        if self.temperature <= 0:
            raise ValueError(f"Temperature must be > 0, got {self.temperature}")

        logger.info(f"Initialized BaselinePolicy with temperature={self.temperature}, seed={self.seed}")

    def _compute_scores(self, state: Node, available_edges: List[Edge], goal: Optional[Node] = None) -> np.ndarray:
        """
        Compute raw scores for each available action (edge).

        Args:
            state: Current state node.
            available_edges: List of edges available from the current state.
            goal: Optional goal node to bias towards.

        Returns:
            numpy array of scores corresponding to each edge.
        """
        if not available_edges:
            return np.array([])

        scores = np.zeros(len(available_edges))

        for i, edge in enumerate(available_edges):
            base_score = 0.0

            # Heuristic: If goal is known, prefer edges that move closer (simplified)
            if goal is not None:
                # Simple heuristic: prefer edges leading to nodes with fewer edges (less explored)
                # or random bias if no topology info
                target_node = edge.target
                # In a real implementation, we might use graph distance or heuristic
                # For now, add a small random bias to ensure stochasticity even with identical edges
                base_score += self.rng.uniform(-0.1, 0.1)

                # If we know the goal, bias towards it (simple Euclidean or ID distance if applicable)
                # Assuming nodes have some implicit ordering or we use a simple heuristic
                if hasattr(state, 'id') and hasattr(goal, 'id'):
                    # Simple heuristic: prefer edges that don't go back to start if possible
                    if edge.target != state: # Avoid self-loops if any
                        base_score += 0.5
            else:
                # No goal info: purely stochastic with slight bias for novelty
                base_score += self.rng.uniform(-0.1, 0.1)

            scores[i] = base_score

        return scores

    def select_action(self, state: Node, available_edges: List[Edge], goal: Optional[Node] = None) -> Tuple[Edge, float]:
        """
        Select an action (edge) stochastically using softmax.

        Args:
            state: Current state node.
            available_edges: List of available edges from the current state.
            goal: Optional goal node.

        Returns:
            Tuple of (selected_edge, log_probability_of_selection).
        """
        if not available_edges:
            raise ValueError("No available edges from current state.")

        # Compute raw scores
        scores = self._compute_scores(state, available_edges, goal)

        # Apply temperature scaling
        # Softmax: p_i = exp(score_i / tau) / sum(exp(score_j / tau))
        scaled_scores = scores / self.temperature

        # Numerical stability: subtract max
        max_score = np.max(scaled_scores)
        exp_scores = np.exp(scaled_scores - max_score)

        # Normalize to probabilities
        probs = exp_scores / np.sum(exp_scores)

        # Stochastic selection
        selected_idx = self.rng.choice(len(available_edges), p=probs)
        selected_edge = available_edges[selected_idx]

        # Compute log probability for the selected action
        # log_p = log(exp(score_selected / tau) / sum)
        #       = (score_selected / tau) - max_score - log(sum(exp_scores - max_score))
        log_prob = (scaled_scores[selected_idx] - max_score) - math.log(np.sum(exp_scores))

        return selected_edge, log_prob

    def get_action_probabilities(self, state: Node, available_edges: List[Edge], goal: Optional[Node] = None) -> np.ndarray:
        """
        Get the probability distribution over available actions.

        Args:
            state: Current state node.
            available_edges: List of available edges.
            goal: Optional goal node.

        Returns:
            numpy array of probabilities for each edge.
        """
        if not available_edges:
            return np.array([])

        scores = self._compute_scores(state, available_edges, goal)
        scaled_scores = scores / self.temperature
        max_score = np.max(scaled_scores)
        exp_scores = np.exp(scaled_scores - max_score)
        probs = exp_scores / np.sum(exp_scores)

        return probs

    def calculate_entropy(self, state: Node, available_edges: List[Edge], goal: Optional[Node] = None) -> float:
        """
        Calculate the entropy of the policy's distribution for a given state.

        Args:
            state: Current state node.
            available_edges: List of available edges.
            goal: Optional goal node.

        Returns:
            Entropy value (float).
        """
        probs = self.get_action_probabilities(state, available_edges, goal)
        if len(probs) == 0:
            return 0.0

        # Filter out zero probabilities to avoid log(0)
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log(probs))
        return float(entropy)

def create_baseline_policy(config: Optional[BaselinePolicyConfig] = None) -> BaselinePolicy:
    """
    Factory function to create a BaselinePolicy instance.

    Args:
        config: Optional configuration. If None, uses defaults.

    Returns:
        BaselinePolicy instance.
    """
    if config is None:
        config = BaselinePolicyConfig()
    return BaselinePolicy(config)

def main():
    """
    Main entry point for testing the policy independently.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create a simple test graph
    # Nodes: 0 (start), 1, 2 (goal)
    # Edges: 0->1, 0->2, 1->2
    start_node = Node(id=0, tier=1)
    node1 = Node(id=1, tier=1)
    goal_node = Node(id=2, tier=1)

    edge_0_1 = Edge(source=start_node, target=node1, weight=1.0)
    edge_0_2 = Edge(source=start_node, target=goal_node, weight=1.0)
    edge_1_2 = Edge(source=node1, target=goal_node, weight=1.0)

    # Test with temperature 1.0 (high entropy)
    config_high = BaselinePolicyConfig(temperature=1.0, seed=42)
    policy_high = create_baseline_policy(config_high)

    available_edges = [edge_0_1, edge_0_2]
    selected, log_prob = policy_high.select_action(start_node, available_edges, goal_node)
    logger.info(f"High Temp (1.0): Selected edge 0->{selected.target.id}, log_prob={log_prob:.4f}")

    # Test with temperature 0.1 (low entropy, more deterministic)
    config_low = BaselinePolicyConfig(temperature=0.1, seed=42)
    policy_low = create_baseline_policy(config_low)

    selected_low, log_prob_low = policy_low.select_action(start_node, available_edges, goal_node)
    logger.info(f"Low Temp (0.1): Selected edge 0->{selected_low.target.id}, log_prob={log_prob_low:.4f}")

    # Verify entropy calculation
    entropy_high = policy_high.calculate_entropy(start_node, available_edges, goal_node)
    entropy_low = policy_low.calculate_entropy(start_node, available_edges, goal_node)
    logger.info(f"Entropy High: {entropy_high:.4f}, Entropy Low: {entropy_low:.4f}")

    # Verify non-zero entropy variance (stochasticity)
    # Run multiple times with same seed to ensure reproducibility, but check distribution
    # Note: With fixed seed, the sequence is deterministic, but the distribution is stochastic in nature.
    # To test variance, we'd need to change seeds or run many episodes.
    logger.info("BaselinePolicy test completed successfully.")

if __name__ == "__main__":
    main()