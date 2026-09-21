"""
Baseline Policy implementation for OPID Critical-First Routing.

This module provides a lightweight, CPU-only baseline policy using numpy.
It implements a Stochastic Softmax Policy with a tunable temperature parameter (tau)
to ensure non-zero baseline entropy variance, satisfying the spec's requirements
for a configurable policy head.
"""
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

# Import from project API surface
from env.state_graph import Node, Edge, StateGraph
from config import get_seed, set_seed

logger = logging.getLogger(__name__)

@dataclass
class BaselinePolicyConfig:
    """Configuration for the Baseline Policy."""
    policy_type: str = "softmax"  # Options: "softmax", "rule_based"
    temperature: float = 1.0      # Tau > 0 for softmax; controls entropy
    random_action_prob: float = 0.05 # For rule-based exploration fallback
    seed: int = 42

class BaselinePolicy:
    """
    A lightweight baseline policy using CPU-only numpy operations.
    
    Supports two modes:
    1. Stochastic Softmax Policy: Uses logits derived from node features and
       a temperature parameter to sample actions. Ensures non-zero entropy.
    2. Rule-based Agent: A deterministic heuristic with optional random exploration.
    
    Attributes:
        config: BaselinePolicyConfig instance.
        temperature: The softmax temperature (tau).
    """
    
    def __init__(self, config: Optional[BaselinePolicyConfig] = None):
        self.config = config or BaselinePolicyConfig()
        self.temperature = self.config.temperature
        set_seed(self.config.seed)
        
        if self.temperature <= 0:
            raise ValueError("Temperature (tau) must be strictly greater than 0.")
        
        logger.info(f"Initialized BaselinePolicy: type={self.config.policy_type}, tau={self.temperature}")

    def _compute_logits(self, state: StateGraph, current_node: Node, available_actions: List[str]) -> Dict[str, float]:
        """
        Computes raw logits for available actions based on state features.
        
        For the softmax policy, we derive a score based on heuristic distance
        to the goal (if known) or random node properties to ensure non-zero variance.
        
        Args:
            state: The current StateGraph environment.
            current_node: The node the agent is currently at.
            available_actions: List of action identifiers (edge targets or 'stay').
        
        Returns:
            Dictionary mapping action identifiers to logit scores.
        """
        logits = {}
        
        # Determine if we have goal information (state_graph has a 'goal' attribute)
        has_goal = hasattr(state, 'goal') and state.goal is not None
        
        for action in available_actions:
            score = 0.0
            
            if self.config.policy_type == "softmax":
                # Softmax Policy Logic:
                # 1. Base score: Random noise scaled by temperature to ensure entropy.
                # 2. Heuristic bias: If goal is known, bias towards nodes closer to goal.
                
                # Use a deterministic hash of the action and current node ID for reproducibility
                # instead of random noise, so the same state always yields the same logits.
                # This satisfies "reproducibility" while maintaining "stochasticity" via sampling.
                hash_val = hash((current_node.id, action)) % 1000
                base_score = (hash_val - 500) / 1000.0  # Range [-0.5, 0.5]
                
                # If goal is known, calculate a simple distance heuristic
                if has_goal:
                    # Simple heuristic: prefer edges that lead to nodes with IDs closer to goal ID
                    # (Assuming node IDs are somewhat sequential or numeric for this heuristic)
                    # In a real scenario, this would be a learned value function or BFS distance.
                    # Here we simulate a "skill" signal: if action leads to 'goal', give high boost.
                    # We check if the action string contains the goal ID or if the target node is the goal.
                    # For generality, we assume action is the target node ID string.
                    try:
                        target_id = int(action)
                        goal_id = int(state.goal.id) if hasattr(state.goal, 'id') else 0
                        # Closer to goal -> higher score
                        dist = abs(target_id - goal_id)
                        max_dist = 1000 # Arbitrary scaling factor
                        heuristic_bonus = max(0, 1.0 - (dist / max_dist))
                        score = base_score + (2.0 * heuristic_bonus)
                    except (ValueError, TypeError):
                        score = base_score
                else:
                    score = base_score
                    
            elif self.config.policy_type == "rule_based":
                # Rule-based Logic:
                # Prefer actions that are not 'stay' if possible, else random.
                if action != "stay":
                    score = 1.0
                else:
                    score = 0.0
                
                # Add small random jitter if exploration is enabled
                if self.config.random_action_prob > 0:
                    if np.random.random() < self.config.random_action_prob:
                        score += np.random.uniform(-0.1, 0.1)
            
            logits[action] = score
        
        return logits

    def get_action_probabilities(self, state: StateGraph, current_node: Node, available_actions: List[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calculates action probabilities and log-probabilities.
        
        Args:
            state: The current StateGraph.
            current_node: Current node ID or object.
            available_actions: List of valid action strings.
        
        Returns:
            Tuple of (probabilities dict, log_probabilities dict).
        """
        if not available_actions:
            return {}, {}
        
        logits = self._compute_logits(state, current_node, available_actions)
        
        # Convert logits to probabilities using softmax with temperature
        # P(a) = exp(logit / tau) / sum(exp(logit / tau))
        scaled_logits = {k: v / self.temperature for k, v in logits.items()}
        
        max_logit = max(scaled_logits.values())
        # Numerical stability
        exp_logits = {k: math.exp(v - max_logit) for k, v in scaled_logits.items()}
        sum_exp = sum(exp_logits.values())
        
        probs = {k: v / sum_exp for k, v in exp_logits.items()}
        log_probs = {k: math.log(p) for k, p in probs.items()}
        
        return probs, log_probs

    def sample_action(self, state: StateGraph, current_node: Node, available_actions: List[str]) -> Tuple[str, float]:
        """
        Samples an action from the policy distribution.
        
        Args:
            state: The current StateGraph.
            current_node: Current node.
            available_actions: List of valid actions.
        
        Returns:
            Tuple of (selected_action, log_probability_of_selection).
        """
        if not available_actions:
            raise ValueError("No available actions to sample from.")
        
        probs, log_probs = self.get_action_probabilities(state, current_node, available_actions)
        
        # Sample using numpy
        actions = list(probs.keys())
        probabilities = list(probs.values())
        
        # Ensure probabilities sum to 1.0 for numpy (floating point safety)
        probabilities = np.array(probabilities)
        probabilities = probabilities / probabilities.sum()
        
        selected_idx = np.random.choice(len(actions), p=probabilities)
        selected_action = actions[selected_idx]
        selected_log_prob = log_probs[selected_action]
        
        return selected_action, selected_log_prob

    def get_best_action(self, state: StateGraph, current_node: Node, available_actions: List[str]) -> Tuple[str, float]:
        """
        Returns the greedy action (highest probability) without sampling.
        Useful for debugging or deterministic evaluation.
        
        Returns:
            Tuple of (best_action, log_probability).
        """
        probs, log_probs = self.get_action_probabilities(state, current_node, available_actions)
        best_action = max(probs, key=probs.get)
        return best_action, log_probs[best_action]

def create_baseline_policy(config: Optional[Dict[str, Any]] = None) -> BaselinePolicy:
    """
    Factory function to create a BaselinePolicy instance.
    
    Args:
        config: Optional dictionary of configuration parameters.
    
    Returns:
        A configured BaselinePolicy instance.
    """
    if config:
        policy_config = BaselinePolicyConfig(**config)
    else:
        policy_config = BaselinePolicyConfig()
    
    return BaselinePolicy(policy_config)

def main():
    """
    Entry point for testing the policy module.
    """
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create a mock state graph for testing
    # This simulates the environment without needing the full generator
    from env.state_graph import Node, Edge, StateGraph
    
    # Create nodes
    start_node = Node(id="0", tier=1)
    mid_node = Node(id="1", tier=1)
    goal_node = Node(id="2", tier=1)
    
    # Create edges
    edges = [
        Edge(source=start_node, target=mid_node, prob=1.0, reward=0.0),
        Edge(source=mid_node, target=goal_node, prob=1.0, reward=1.0)
    ]
    
    # Create graph
    graph = StateGraph(
        nodes=[start_node, mid_node, goal_node],
        edges=edges,
        start=start_node,
        goal=goal_node,
        tier=1
    )
    
    # Initialize policy
    policy = create_baseline_policy({
        "policy_type": "softmax",
        "temperature": 0.5,
        "seed": 42
    })
    
    # Test sampling
    available_actions = ["1", "2"] # Target node IDs
    print(f"Testing policy on graph with {len(graph.nodes)} nodes.")
    
    for i in range(5):
        action, log_prob = policy.sample_action(graph, start_node, available_actions)
        print(f"Sample {i+1}: Action={action}, LogProb={log_prob:.4f}")
    
    # Test greedy
    best_action, best_log_prob = policy.get_best_action(graph, start_node, available_actions)
    print(f"Greedy Action: {best_action}, LogProb: {best_log_prob:.4f}")
    
    # Test entropy
    probs, _ = policy.get_action_probabilities(graph, start_node, available_actions)
    entropy = -sum(p * math.log(p) for p in probs.values())
    print(f"Policy Entropy: {entropy:.4f}")
    
    if entropy <= 0:
        logger.error("Entropy is zero or negative! Policy is deterministic when it should be stochastic.")
        sys.exit(1)
    else:
        logger.info("Policy successfully generates stochastic actions with non-zero entropy.")

if __name__ == "__main__":
    main()