"""
Baseline Policy Implementation for OPID Critical-First Routing.

This module implements a lightweight baseline policy using CPU-only numpy operations.
It supports a Stochastic Softmax Policy with a configurable temperature parameter
to ensure non-zero baseline entropy variance, as required by the specification.
"""
import math
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import numpy as np

from env.state_graph import Node, Edge, StateGraph
from config import get_seed, set_seed

logger = logging.getLogger(__name__)


@dataclass
class BaselinePolicyConfig:
    """Configuration for the BaselinePolicy."""
    policy_type: str = "softmax"  # Options: "softmax", "rule_based"
    temperature: float = 1.0      # Temperature for softmax (tau > 0)
    seed: int = 42
    # Parameters for rule-based if selected
    greedy_prob: float = 0.9      # Probability of taking greedy action in rule-based mode


class BaselinePolicy:
    """
    A lightweight baseline policy using CPU-only numpy operations.

    Supports:
    1. Stochastic Softmax Policy: Uses action logits and a temperature parameter
       to produce a probability distribution over valid actions.
    2. Rule-Based Agent: A simple heuristic agent (greedy with some exploration).

    This class does NOT use PyTorch or TensorFlow.
    """

    def __init__(self, config: BaselinePolicyConfig):
        self.config = config
        self.policy_type = config.policy_type
        self.temperature = config.temperature
        self.seed = config.seed

        # Validate temperature
        if self.temperature <= 0:
            raise ValueError(f"Temperature must be > 0. Got {self.temperature}")

        # Initialize RNG
        set_seed(self.seed)
        self.rng = np.random.default_rng(self.seed)

        logger.info(f"Initialized BaselinePolicy: type={self.policy_type}, tau={self.temperature}")

    def get_action_logits(self, state: Node, graph: StateGraph) -> Dict[str, float]:
        """
        Compute raw logits for available actions from the current state.

        Args:
            state: The current Node in the StateGraph.
            graph: The full StateGraph context.

        Returns:
            A dictionary mapping action identifiers (edge IDs or target node IDs) to logit values.
        """
        # Identify valid outgoing edges from the current state
        valid_actions = {}
        for edge in graph.edges:
            if edge.source == state.id:
                # Action is the target node ID
                valid_actions[edge.target] = 0.0  # Base logit

        if not valid_actions:
            # Terminal state or no outgoing edges
            return {}

        # If using rule-based, we might bias logits here, but softmax handles it via temperature
        # For pure softmax, we start with uniform logits (0.0)
        return valid_actions

    def select_action(self, state: Node, graph: StateGraph) -> Tuple[str, float]:
        """
        Select an action based on the current policy.

        Returns:
            Tuple of (action_id, log_prob_of_action)
        """
        logits = self.get_action_logits(state, graph)

        if not logits:
            # No valid actions
            return None, 0.0

        if self.policy_type == "softmax":
            return self._sample_softmax(logits)
        elif self.policy_type == "rule_based":
            return self._sample_rule_based(logits)
        else:
            raise ValueError(f"Unknown policy type: {self.policy_type}")

    def _sample_softmax(self, logits: Dict[str, float]) -> Tuple[str, float]:
        """
        Sample an action using the softmax distribution with temperature.

        P(a) = exp(logit(a) / tau) / sum(exp(logit(a') / tau))
        """
        actions = list(logits.keys())
        raw_logits = np.array([logits[a] for a in actions], dtype=np.float64)

        # Apply temperature
        scaled_logits = raw_logits / self.temperature

        # Numerical stability: subtract max
        max_logit = np.max(scaled_logits)
        exp_logits = np.exp(scaled_logits - max_logit)
        probs = exp_logits / np.sum(exp_logits)

        # Sample
        idx = self.rng.choice(len(actions), p=probs)
        action = actions[idx]

        # Compute log probability
        # log(P) = logit/tau - max_logit - log(sum(exp(logit/tau - max_logit)))
        log_prob = scaled_logits[idx] - max_logit - np.log(np.sum(exp_logits))

        return action, log_prob

    def _sample_rule_based(self, logits: Dict[str, float]) -> Tuple[str, float]:
        """
        Rule-based selection: Greedy with epsilon-exploration.
        For simplicity, we pick the action with the highest logit (arbitrary if equal)
        with probability `greedy_prob`, else random.
        """
        actions = list(logits.keys())
        if len(actions) == 1:
            return actions[0], 0.0  # Only one choice

        # Find max logit
        max_logit_val = max(logits.values())
        best_actions = [a for a, v in logits.items() if v == max_logit_val]

        if self.rng.random() < self.config.greedy_prob:
            # Pick best
            action = self.rng.choice(best_actions)
            # Approximate log prob for greedy: not strictly defined in rule-based,
            # but we can return a high value or 0. Let's return 0 for simplicity
            # or a placeholder indicating "deterministic choice".
            return action, 0.0
        else:
            # Random
            action = self.rng.choice(actions)
            return action, math.log(1.0 / len(actions))

    def evaluate_batch(self, states: List[Node], graphs: List[StateGraph]) -> List[Tuple[str, float]]:
        """
        Evaluate actions for a batch of states.
        """
        results = []
        for s, g in zip(states, graphs):
            results.append(self.select_action(s, g))
        return results


def create_baseline_policy(config: Optional[BaselinePolicyConfig] = None) -> BaselinePolicy:
    """
    Factory function to create a BaselinePolicy instance.
    """
    if config is None:
        config = BaselinePolicyConfig()
    return BaselinePolicy(config)


def main():
    """
    Main entry point for testing the policy module.
    """
    print("Testing BaselinePolicy...")

    # Mock a simple graph for testing
    # We need to import StateGraph, Node, Edge to construct a valid test
    from env.state_graph import StateGraph, Node, Edge

    # Create a dummy graph
    g = StateGraph(tier=1)
    n1 = Node(id="n1", state_value=0, is_goal=False)
    n2 = Node(id="n2", state_value=1, is_goal=False)
    n3 = Node(id="n3", state_value=2, is_goal=True)

    g.nodes = {"n1": n1, "n2": n2, "n3": n3}
    g.edges = [
        Edge(source="n1", target="n2", prob=1.0, reward=0),
        Edge(source="n2", target="n3", prob=1.0, reward=1.0)
    ]
    g.start = "n1"
    g.goal = "n3"

    # Test Softmax Policy
    cfg = BaselinePolicyConfig(policy_type="softmax", temperature=0.5, seed=42)
    policy = create_baseline_policy(cfg)

    # Run a few steps
    current = g.nodes["n1"]
    for i in range(3):
        action, log_prob = policy.select_action(current, g)
        print(f"Step {i}: State={current.id}, Action={action}, LogProb={log_prob:.4f}")
        if action:
            # Move to next node (simplified)
            for e in g.edges:
                if e.source == current.id and e.target == action:
                    current = g.nodes[action]
                    break
        else:
            break

    # Test Rule-Based Policy
    cfg_rb = BaselinePolicyConfig(policy_type="rule_based", greedy_prob=0.8, seed=42)
    policy_rb = create_baseline_policy(cfg_rb)
    current = g.nodes["n1"]
    print("\nRule-based Policy:")
    for i in range(3):
        action, log_prob = policy_rb.select_action(current, g)
        print(f"Step {i}: State={current.id}, Action={action}, LogProb={log_prob:.4f}")
        if action:
            for e in g.edges:
                if e.source == current.id and e.target == action:
                    current = g.nodes[action]
                    break
        else:
            break

    print("\nBaselinePolicy tests completed.")


if __name__ == "__main__":
    main()
