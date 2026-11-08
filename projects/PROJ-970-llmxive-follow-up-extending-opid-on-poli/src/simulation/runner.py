"""
Core simulation runner.

This lightweight implementation runs episodes for a given graph,
router, and policy.  It records success, steps taken, average action
entropy and average log‑probability shift, and returns a dict that
conforms to the ``episode_result.schema.yaml`` contract.
"""

import random
from dataclasses import asdict
from typing import Dict

from ..agent.opid_router import OPIDRouter
from ..agent.policy import BaselinePolicy, create_baseline_policy
from ..environment.state_graph import StateGraph

def run_episode(graph: StateGraph, router: OPIDRouter, policy: BaselinePolicy) -> Dict:
    """
    Execute a single episode on ``graph`` using ``router`` and ``policy``.

    Returns a dictionary with keys:
      - success (bool)
      - steps_taken (int)
      - action_entropy (float)
      - log_prob_shift (float)
    """
    max_steps = 200
    current = graph.start
    steps = 0
    entropies = []
    shifts = []

    while steps < max_steps and current != graph.goal:
        node = graph.nodes[current]
        # Obtain action distribution from the policy
        action, log_prob = policy.select_action(node, graph)
        if action is None:
            break

        # Query router for possible injection
        if router.should_inject():
            # Apply a fixed log‑probability shift for demonstration
            shifted_log_prob = log_prob + 0.1
            shifts.append(0.1)
        else:
            shifted_log_prob = log_prob
            shifts.append(0.0)

        # Record entropy (using the softmax probabilities underlying the policy)
        # For simplicity we approximate entropy from the log‑probability
        entropies.append(-log_prob)

        # Transition to the next state (deterministic for this stub)
        current = action
        steps += 1

    success = current == graph.goal
    avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0
    avg_shift = sum(shifts) / len(shifts) if shifts else 0.0

    result = {
        "success": success,
        "steps_taken": steps,
        "action_entropy": avg_entropy,
        "log_prob_shift": avg_shift,
        "tier": graph.tier,
        "threshold": router.routing_threshold,
    }
    return result